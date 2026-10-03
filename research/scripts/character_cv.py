"""Fixed character TF-IDF experiment on frozen training-only group folds."""
import argparse
import json
from pathlib import Path

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from corpus_experiment import metrics
from hybrid_cv import digest, validate_split


def run(data, folds, output):
    if output.exists():
        raise ValueError('Use a new output directory')
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    prior = json.loads((folds / 'training_results.json').read_text())
    if prior['input_sha256'] != digest(data):
        raise ValueError('Frozen training hash mismatch')
    lookup = {r['id']: r for r in rows}
    record = dict(purpose='Training-only exploratory grouped CV, not independent accuracy',
                  reserved_test_read=False, validation_read=False, release_approved=False,
                  data_sha256=digest(data), fold_manifest_sha256=digest(folds / 'training_results.json'),
                  sklearn_version=sklearn.__version__,
                  settings=dict(analyzer='char_wb', ngram_range=[3, 5], min_df=2,
                                max_features=30000, sublinear_tf=True, C=1,
                                class_weight='balanced', solver='lbfgs', max_iter=1000,
                                random_state=20261001),
                  folds=[], oof={'word': [], 'character': []})
    output.mkdir(parents=True)
    (output / 'protocol.json').write_text(json.dumps(record, indent=2))
    for split in prior['folds']:
        train, held = split['train_ids'], split['held_ids']
        validate_split(rows, train, held)
        baseline = folds / f"fold-{split['fold']}-baseline.joblib"
        if digest(baseline) != split['models']['baseline']['model_sha256']:
            raise ValueError('Baseline artifact mismatch')
        saved = joblib.load(baseline)
        vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5),
                                    min_df=2, max_features=30000, sublinear_tf=True)
        features = vectorizer.fit_transform([lookup[i]['text'] for i in train])
        model = LogisticRegression(C=1, class_weight='balanced', solver='lbfgs',
                                   max_iter=1000, random_state=20261001)
        model.fit(features, [lookup[i]['label'] for i in train])
        destination = output / f"fold-{split['fold']}-character.joblib"
        joblib.dump(dict(vectorizer=vectorizer, classifier=model), destination)
        record['folds'].append(dict(fold=split['fold'], train_ids=train, held_ids=held,
                                   word_sha256=digest(baseline), character_sha256=digest(destination),
                                   vocabulary_size=len(vectorizer.vocabulary_), iterations=model.n_iter_.tolist()))
        for name, vec, clf in [('word', saved['vectorizer'], saved['classifier']),
                               ('character', vectorizer, model)]:
            probabilities = clf.predict_proba(vec.transform([lookup[i]['text'] for i in held]))
            for id, scores in zip(held, probabilities):
                record['oof'][name].append(dict(id=id, fold=split['fold'],
                    prediction=str(clf.classes_[scores.argmax()]),
                    probabilities=dict(zip(clf.classes_.tolist(), scores.tolist()))))
        (output / 'training_results.json').write_text(json.dumps(record, indent=2))
        print('completed fold', split['fold'], flush=True)
    record['metrics'] = {}
    maps = {}
    for name, predictions in record['oof'].items():
        maps[name] = {r['id']: r['prediction'] for r in predictions}
        if len(predictions) != len(rows) or set(maps[name]) != set(lookup):
            raise ValueError('Incomplete or repeated OOF coverage')
        record['metrics'][name] = metrics(rows, [maps[name][r['id']] for r in rows])
        strict = [r for r in rows if r['strict_agreement']]
        record['metrics'][name]['unanimous_only'] = metrics(strict, [maps[name][r['id']] for r in strict])
    record['corrected_ids'] = [r['id'] for r in rows if maps['word'][r['id']] != r['label'] and maps['character'][r['id']] == r['label']]
    record['regressed_ids'] = [r['id'] for r in rows if maps['word'][r['id']] == r['label'] and maps['character'][r['id']] != r['label']]
    (output / 'training_results.json').write_text(json.dumps(record, indent=2))
    print(json.dumps(record['metrics'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('data', 'folds', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.folds, args.output)
