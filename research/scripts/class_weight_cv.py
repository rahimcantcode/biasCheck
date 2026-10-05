"""Fixed class-weight ablation on frozen training-only word features."""
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


def run(data, folds, output):
    if output.exists():
        raise ValueError('Use a new output directory')
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    prior = json.loads((folds / 'training_results.json').read_text())
    if digest(data) != prior['input_sha256']:
        raise ValueError('Training fingerprint mismatch')
    lookup = {r['id']: r for r in rows}
    report = dict(purpose='Fixed class-weight ablation; exploratory development evidence only',
        validation_read=False, reserved_test_read=False, release_approved=False,
        data_sha256=digest(data), fold_manifest_sha256=digest(folds / 'training_results.json'),
        runtime=dict(numpy=np.__version__, sklearn=sklearn.__version__, joblib=joblib.__version__),
        folds=[], oof={'balanced': [], 'unweighted': []})
    output.mkdir(parents=True)
    (output / 'protocol.json').write_text(json.dumps(report, indent=2))
    for split in prior['folds']:
        train, held = split['train_ids'], split['held_ids']
        validate_split(rows, train, held)
        path = folds / f"fold-{split['fold']}-baseline.joblib"
        if digest(path) != split['models']['baseline']['model_sha256']:
            raise ValueError('Baseline mismatch')
        saved = joblib.load(path)
        baseline, vec = saved['classifier'], saved['vectorizer']
        if baseline.get_params()['class_weight'] != 'balanced':
            raise ValueError('Expected balanced reference')
        x = vec.transform([lookup[i]['text'] for i in train])
        h = vec.transform([lookup[i]['text'] for i in held])
        y = [lookup[i]['label'] for i in train]
        fold = dict(fold=split['fold'], train_ids=train, held_ids=held,
            training_class_counts=dict(Counter(y)), baseline_sha256=digest(path), models={})
        for name, weight in [('balanced', 'balanced'), ('unweighted', None)]:
            model = clone(baseline).set_params(class_weight=weight)
            with warnings.catch_warnings():
                warnings.simplefilter('error', ConvergenceWarning)
                model.fit(x, y)
            p = model.predict_proba(h)
            if not np.isfinite(p).all() or not np.allclose(p.sum(axis=1), 1):
                raise ValueError('Invalid probabilities')
            if name == 'balanced' and not np.allclose(p, baseline.predict_proba(h), atol=1e-10, rtol=1e-10):
                raise ValueError('Balanced refit does not reproduce frozen reference')
            dest = output / f"fold-{split['fold']}-{name}.joblib"
            joblib.dump(dict(vectorizer=vec, classifier=model), dest)
            fold['models'][name] = dict(model_sha256=digest(dest), parameters=model.get_params(),
                iterations=model.n_iter_.tolist())
            report['oof'][name].extend(dict(id=id, fold=split['fold'], gold=lookup[id]['label'],
                text_sha256=lookup[id]['text_sha256'], strict_agreement=lookup[id]['strict_agreement'],
                prediction=str(model.classes_[scores.argmax()]),
                probabilities=dict(zip(model.classes_.tolist(), scores.tolist())))
                for id, scores in zip(held, p))
        report['folds'].append(fold)
        print('completed fold', split['fold'], flush=True)
    maps = {}
    report['metrics'] = {}
    for name, predictions in report['oof'].items():
        maps[name] = {r['id']: r['prediction'] for r in predictions}
        if len(predictions) != len(rows) or set(maps[name]) != set(lookup):
            raise ValueError('Invalid OOF coverage')
        report['metrics'][name] = metrics(rows, [maps[name][r['id']] for r in rows])
    report['corrected_ids'] = [r['id'] for r in rows
        if maps['balanced'][r['id']] != r['label'] and maps['unweighted'][r['id']] == r['label']]
    report['regressed_ids'] = [r['id'] for r in rows
        if maps['balanced'][r['id']] == r['label'] and maps['unweighted'][r['id']] != r['label']]
    report['limitations'] = ['Repeated exploratory use of small development folds; not independent evaluation',
        'Event strings need not represent independent event families',
        'Disputed noncommercial corpus labels; no threshold tuning or deployment',
        'Clone fixes all estimator parameters except class_weight; balanced refit probabilities checked']
    (output / 'results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report['metrics'], indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('data', 'folds', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    run(a.data, a.folds, a.output)
