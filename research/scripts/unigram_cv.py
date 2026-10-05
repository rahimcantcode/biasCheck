"""Fixed unigram-only development ablation; no validation/test or release."""
import argparse
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
    if output.exists(): raise ValueError('Use a new output directory')
    rows = [json.loads(s) for s in data.read_text().splitlines()]
    prior = json.loads((folds / 'training_results.json').read_text())
    if digest(data) != prior['input_sha256']: raise ValueError('Data mismatch')
    lookup = {r['id']: r for r in rows}
    report = dict(purpose='Fixed unigram-only exploratory training-fold comparison',
        data_sha256=digest(data), fold_manifest_sha256=digest(folds / 'training_results.json'),
        validation_read=False, reserved_test_read=False, release_approved=False,
        runtime=dict(numpy=np.__version__, sklearn=sklearn.__version__, joblib=joblib.__version__),
        folds=[], oof={'baseline': [], 'unigram': []})
    output.mkdir(parents=True)
    (output / 'protocol.json').write_text(json.dumps(report, indent=2))
    for split in prior['folds']:
        train, held = split['train_ids'], split['held_ids']
        validate_split(rows, train, held)
        path = folds / f"fold-{split['fold']}-baseline.joblib"
        if digest(path) != split['models']['baseline']['model_sha256']: raise ValueError('Model mismatch')
        saved = joblib.load(path)
        vec = clone(saved['vectorizer']).set_params(ngram_range=(1, 1))
        model = clone(saved['classifier'])
        x = vec.fit_transform([lookup[i]['text'] for i in train])
        if any(' ' in f for f in vec.vocabulary_): raise ValueError('Unexpected non-unigram feature')
        with warnings.catch_warnings():
            warnings.simplefilter('error', ConvergenceWarning)
            model.fit(x, [lookup[i]['label'] for i in train])
        dest = output / f"fold-{split['fold']}.joblib"
        joblib.dump(dict(vectorizer=vec, classifier=model), dest)
        report['folds'].append(dict(fold=split['fold'], train_ids=train, held_ids=held,
            baseline_sha256=digest(path), candidate_sha256=digest(dest), iterations=model.n_iter_.tolist(),
            parameters=model.get_params(), vocabulary_size=len(vec.vocabulary_),
            baseline_vocabulary_size=len(saved['vectorizer'].vocabulary_),
            vectorizer_settings={k: vec.get_params()[k] for k in ('ngram_range','min_df','max_features','sublinear_tf','token_pattern','lowercase','stop_words','norm')}))
        for name, v, m in [('baseline', saved['vectorizer'], saved['classifier']), ('unigram', vec, model)]:
            p = m.predict_proba(v.transform([lookup[i]['text'] for i in held]))
            if not np.isfinite(p).all() or not np.allclose(p.sum(axis=1), 1): raise ValueError('Invalid scores')
            report['oof'][name].extend(dict(id=i, fold=split['fold'], gold=lookup[i]['label'],
                strict_agreement=lookup[i]['strict_agreement'], text_sha256=lookup[i]['text_sha256'],
                prediction=str(m.classes_[scores.argmax()]), probabilities=dict(zip(m.classes_.tolist(), scores.tolist())))
                for i, scores in zip(held, p))
        print('completed fold', split['fold'], flush=True)
    report['metrics'] = {}; maps = {}
    for name, predictions in report['oof'].items():
        maps[name] = {r['id']: r['prediction'] for r in predictions}
        if len(predictions) != len(rows) or set(maps[name]) != set(lookup): raise ValueError('Invalid OOF coverage')
        report['metrics'][name] = metrics(rows, [maps[name][r['id']] for r in rows])
    report['corrected_ids'] = [r['id'] for r in rows if maps['baseline'][r['id']] != r['label'] and maps['unigram'][r['id']] == r['label']]
    report['regressed_ids'] = [r['id'] for r in rows if maps['baseline'][r['id']] == r['label'] and maps['unigram'][r['id']] != r['label']]
    report['limitations'] = ['Unigram-only changes normalization and possible feature-cap competition, not just bigram information',
        'Repeated development folds, disputed noncommercial labels; not independent accuracy',
        'One fixed pipeline comparison, no threshold or hyperparameter search']
    (output / 'results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report['metrics'], indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('data', 'folds', 'output'): p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    run(a.data, a.folds, a.output)
