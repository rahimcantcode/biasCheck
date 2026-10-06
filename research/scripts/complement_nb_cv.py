"""Fixed ComplementNB comparison on existing training-only folds."""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.naive_bayes import ComplementNB

from corpus_experiment import metrics
from hybrid_cv import digest, validate_split


def run(data, folds, output):
    if output.exists():
        raise ValueError('Use a new output directory')
    rows = [json.loads(s) for s in data.read_text().splitlines()]
    prior = json.loads((folds / 'training_results.json').read_text())
    if digest(data) != prior['input_sha256']:
        raise ValueError('Data mismatch')
    lookup = {r['id']: r for r in rows}
    report = dict(purpose='Fixed ComplementNB development comparison; research-only',
                  data_sha256=digest(data), fold_manifest_sha256=digest(folds / 'training_results.json'),
                  script_sha256=digest(Path(__file__)), validation_read=False,
                  reserved_test_read=False, release_approved=False,
                  runtime=dict(numpy=np.__version__, sklearn=sklearn.__version__, joblib=joblib.__version__),
                  parameters=ComplementNB(alpha=1, norm=False, fit_prior=True).get_params(),
                  folds=[], oof={'baseline': [], 'complement_nb': []})
    output.mkdir(parents=True)
    (output / 'protocol.json').write_text(json.dumps(report, indent=2))
    for split in prior['folds']:
        train, held = split['train_ids'], split['held_ids']
        validate_split(rows, train, held)
        source = folds / f"fold-{split['fold']}-baseline.joblib"
        if digest(source) != split['models']['baseline']['model_sha256']:
            raise ValueError('Model mismatch')
        saved = joblib.load(source)
        vec = saved['vectorizer']
        model = ComplementNB(**report['parameters'])
        model.fit(vec.transform([lookup[i]['text'] for i in train]), [lookup[i]['label'] for i in train])
        destination = output / f"fold-{split['fold']}.joblib"
        joblib.dump(dict(vectorizer=vec, classifier=model), destination)
        report['folds'].append(dict(fold=split['fold'], train_ids=train, held_ids=held,
                                   baseline_sha256=digest(source), candidate_sha256=digest(destination),
                                   vocabulary_size=len(vec.vocabulary_)))
        for name, classifier in [('baseline', saved['classifier']), ('complement_nb', model)]:
            probabilities = classifier.predict_proba(vec.transform([lookup[i]['text'] for i in held]))
            if not np.isfinite(probabilities).all() or not np.allclose(probabilities.sum(axis=1), 1):
                raise ValueError('Invalid probabilities')
            report['oof'][name].extend(dict(id=i, fold=split['fold'], gold=lookup[i]['label'],
                strict_agreement=lookup[i]['strict_agreement'], text_sha256=lookup[i]['text_sha256'],
                prediction=str(classifier.classes_[p.argmax()]), probabilities=dict(zip(classifier.classes_.tolist(), p.tolist())))
                for i, p in zip(held, probabilities))
    maps = {}
    report['metrics'] = {}
    for name, predictions in report['oof'].items():
        maps[name] = {r['id']: r['prediction'] for r in predictions}
        if len(predictions) != len(rows) or set(maps[name]) != set(lookup):
            raise ValueError('Invalid OOF coverage')
        report['metrics'][name] = metrics(rows, [maps[name][r['id']] for r in rows])
    report['corrected_ids'] = [r['id'] for r in rows if maps['baseline'][r['id']] != r['label'] and maps['complement_nb'][r['id']] == r['label']]
    report['regressed_ids'] = [r['id'] for r in rows if maps['baseline'][r['id']] == r['label'] and maps['complement_nb'][r['id']] != r['label']]
    report['limitations'] = ['Repeated development folds with disputed noncommercial labels, not independent accuracy.',
                            'Classifier family, objective, smoothing and class weighting differ; not an isolated causal ablation.',
                            'Fixed alpha=1 and norm=False, no tuning; scores are uncalibrated.']
    (output / 'results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report['metrics'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('data', 'folds', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.folds, args.output)
