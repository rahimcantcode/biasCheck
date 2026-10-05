"""Fixed size/class-matched controls for unanimous-only supervision."""
import argparse
from collections import Counter
import json
from pathlib import Path
import warnings
import joblib
import numpy as np
import sklearn
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from corpus_experiment import metrics
from hybrid_cv import digest, validate_split


def sample_ids(lookup, train, counts, seed, fold):
    rng = np.random.default_rng(np.random.SeedSequence([seed, fold]))
    selected = set()
    for label in ('LEFT', 'CENTER', 'RIGHT'):
        pool = [i for i in train if lookup[i]['label'] == label]
        count = counts[label]
        if type(count) is not int or not 0 < count <= len(pool): raise ValueError('Invalid class count')
        selected.update(rng.choice(pool, size=count, replace=False).tolist())
    return [i for i in train if i in selected]


def run(data, source, folds, output):
    if output.exists(): raise ValueError('Use a new output directory')
    rows = [json.loads(s) for s in data.read_text().splitlines()]
    prior = json.loads(source.read_text())
    if digest(data) != prior['data_sha256']: raise ValueError('Data mismatch')
    if digest(folds / 'training_results.json') != prior['fold_manifest_sha256']: raise ValueError('Fold mismatch')
    lookup = {r['id']: r for r in rows}
    seeds = list(range(20261005, 20261010))
    report = dict(purpose='Fixed matched-size/class supervision controls; descriptive only',
        seeds=seeds, source_sha256=digest(source), data_sha256=digest(data),
        fold_manifest_sha256=prior['fold_manifest_sha256'], validation_read=False,
        reserved_test_read=False, release_approved=False,
        runtime=dict(numpy=np.__version__, sklearn=sklearn.__version__, joblib=joblib.__version__),
        reference_metrics=prior['metrics'], runs=[])
    output.mkdir(parents=True)
    (output / 'protocol.json').write_text(json.dumps(report, indent=2))
    for seed in seeds:
        trial = dict(seed=seed, folds=[], predictions=[])
        for split in prior['folds']:
            train, held = split['train_ids'], split['held_ids']
            validate_split(rows, train, held)
            selected = sample_ids(lookup, train, split['supervised_counts'], seed, split['fold'])
            assert dict(Counter(lookup[i]['label'] for i in selected)) == split['supervised_counts']
            path = folds / f"fold-{split['fold']}-baseline.joblib"
            if digest(path) != split['baseline_sha256']: raise ValueError('Baseline mismatch')
            saved = joblib.load(path)
            vec, model = saved['vectorizer'], clone(saved['classifier'])
            with warnings.catch_warnings():
                warnings.simplefilter('error', ConvergenceWarning)
                model.fit(vec.transform([lookup[i]['text'] for i in selected]), [lookup[i]['label'] for i in selected])
            p = model.predict_proba(vec.transform([lookup[i]['text'] for i in held]))
            if not np.isfinite(p).all() or not np.allclose(p.sum(axis=1), 1): raise ValueError('Invalid scores')
            dest = output / f"seed-{seed}-fold-{split['fold']}.joblib"
            joblib.dump(dict(vectorizer=vec, classifier=model), dest)
            trial['folds'].append(dict(fold=split['fold'], train_ids=train, held_ids=held, supervised_ids=selected,
                class_counts=split['supervised_counts'], unanimous_n=sum(lookup[i]['strict_agreement'] for i in selected),
                model_sha256=digest(dest), baseline_sha256=digest(path), parameters=model.get_params(),
                iterations=model.n_iter_.tolist()))
            trial['predictions'].extend(dict(id=i, fold=split['fold'], gold=lookup[i]['label'],
                strict_agreement=lookup[i]['strict_agreement'], text_sha256=lookup[i]['text_sha256'],
                prediction=str(model.classes_[scores.argmax()]), probabilities=dict(zip(model.classes_.tolist(), scores.tolist())))
                for i, scores in zip(held, p))
        aligned = {r['id']: r['prediction'] for r in trial['predictions']}
        if len(trial['predictions']) != len(rows) or set(aligned) != set(lookup): raise ValueError('Invalid OOF coverage')
        trial['metrics'] = metrics(rows, [aligned[r['id']] for r in rows])
        disputed = [r for r in rows if not r['strict_agreement']]
        trial['disputed_metrics'] = metrics(disputed, [aligned[r['id']] for r in disputed])
        report['runs'].append(trial)
        (output / 'results.json').write_text(json.dumps(report, indent=2))
        print(seed, trial['metrics']['accuracy'], trial['metrics']['macro_f1'], flush=True)
    report['limitations'] = ['Five seeds are not independent datasets; overlapping training folds',
        'Controls size and class counts, not topic, annotator, difficulty or selection effects',
        'Frozen vectorizers use all fold-training text; disputed texts not removed',
        'No significance test or pure causal estimate of label noise; development research only']
    (output / 'results.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('data', 'source', 'folds', 'output'): p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    run(a.data, a.source, a.folds, a.output)
