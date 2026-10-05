"""Withhold disputed supervision while retaining frozen fold-local text features."""
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


def supervised_ids(lookup, train):
    if any(type(lookup[i]['strict_agreement']) is not bool for i in train):
        raise ValueError('Agreement flags must be boolean')
    selected = [i for i in train if lookup[i]['strict_agreement']]
    if {lookup[i]['label'] for i in selected} != {'LEFT', 'CENTER', 'RIGHT'}:
        raise ValueError('All three classes required in supervised subset')
    return selected


def run(data, folds, output):
    if output.exists(): raise ValueError('Use a new output directory')
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    prior = json.loads((folds / 'training_results.json').read_text())
    if digest(data) != prior['input_sha256']: raise ValueError('Training fingerprint mismatch')
    lookup = {r['id']: r for r in rows}
    report = dict(purpose='Fixed disputed-supervision exclusion diagnostic, not independent accuracy',
        validation_read=False, reserved_test_read=False, release_approved=False,
        data_sha256=digest(data), fold_manifest_sha256=digest(folds / 'training_results.json'),
        runtime=dict(numpy=np.__version__, sklearn=sklearn.__version__, joblib=joblib.__version__),
        representation='Frozen vectorizer fitted on ALL fold-training text, including excluded-label rows',
        folds=[], oof={'full': [], 'strict': []})
    output.mkdir(parents=True)
    (output / 'protocol.json').write_text(json.dumps(report, indent=2))
    for split in prior['folds']:
        train, held = split['train_ids'], split['held_ids']
        validate_split(rows, train, held)
        selected = supervised_ids(lookup, train)
        path = folds / f"fold-{split['fold']}-baseline.joblib"
        if digest(path) != split['models']['baseline']['model_sha256']: raise ValueError('Baseline mismatch')
        saved = joblib.load(path)
        baseline, vec = saved['classifier'], saved['vectorizer']
        candidate = clone(baseline)
        with warnings.catch_warnings():
            warnings.simplefilter('error', ConvergenceWarning)
            candidate.fit(vec.transform([lookup[i]['text'] for i in selected]), [lookup[i]['label'] for i in selected])
        dest = output / f"fold-{split['fold']}-strict.joblib"
        joblib.dump(dict(vectorizer=vec, classifier=candidate), dest)
        report['folds'].append(dict(fold=split['fold'], train_ids=train, held_ids=held,
            supervised_ids=selected, excluded_ids=[i for i in train if i not in selected],
            full_counts=dict(Counter(lookup[i]['label'] for i in train)),
            supervised_counts=dict(Counter(lookup[i]['label'] for i in selected)),
            baseline_sha256=digest(path), candidate_sha256=digest(dest),
            parameters=candidate.get_params(), iterations=candidate.n_iter_.tolist()))
        h = vec.transform([lookup[i]['text'] for i in held])
        for name, model in [('full', baseline), ('strict', candidate)]:
            p = model.predict_proba(h)
            if not np.isfinite(p).all() or not np.allclose(p.sum(axis=1), 1): raise ValueError('Invalid scores')
            report['oof'][name].extend(dict(id=i, fold=split['fold'], gold=lookup[i]['label'],
                strict_agreement=lookup[i]['strict_agreement'], text_sha256=lookup[i]['text_sha256'],
                prediction=str(model.classes_[scores.argmax()]),
                probabilities=dict(zip(model.classes_.tolist(), scores.tolist()))) for i, scores in zip(held, p))
        print('completed fold', split['fold'], 'supervised n', len(selected), flush=True)
    report['metrics'] = {}
    maps = {}
    for name, predictions in report['oof'].items():
        maps[name] = {r['id']: r['prediction'] for r in predictions}
        if len(predictions) != len(rows) or set(maps[name]) != set(lookup): raise ValueError('Invalid OOF coverage')
        report['metrics'][name] = metrics(rows, [maps[name][r['id']] for r in rows])
        disputed = [r for r in rows if not r['strict_agreement']]
        report['metrics'][name]['disputed_slice'] = metrics(disputed, [maps[name][r['id']] for r in disputed])
    report['corrected_ids'] = [r['id'] for r in rows if maps['full'][r['id']] != r['label'] and maps['strict'][r['id']] == r['label']]
    report['regressed_ids'] = [r['id'] for r in rows if maps['full'][r['id']] == r['label'] and maps['strict'][r['id']] != r['label']]
    report['limitations'] = ['Less supervision changes sample size, class/topic mix and balanced class weights',
        'Not a causal estimate of label-noise effects; unanimity does not prove correctness',
        'Representation still uses excluded-label training text, never held-out text',
        'Repeated development folds and disputed noncommercial corpus labels; research only']
    (output / 'results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report['metrics'], indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('data', 'folds', 'output'): p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    run(a.data, a.folds, a.output)
