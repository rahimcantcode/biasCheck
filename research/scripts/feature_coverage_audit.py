"""Vocabulary survival on frozen development folds; no fitting or policy tuning."""
import argparse
from collections import Counter
import json
from pathlib import Path
import joblib
from hybrid_cv import digest, validate_split


def coverage(features, vocabulary):
    counts = Counter(features)
    total = sum(counts.values())
    retained = sum(n for f, n in counts.items() if f in vocabulary)
    return dict(emitted_occurrences=total, retained_occurrences=retained,
        emitted_distinct=len(counts), retained_distinct=sum(f in vocabulary for f in counts),
        occurrence_fraction=retained / total if total else None)


def summarize(rows):
    out = dict(n=len(rows), correct=sum(r['prediction'] == r['gold'] for r in rows))
    for key in ('all', 'unigrams', 'bigrams'):
        values = [r[key]['occurrence_fraction'] for r in rows if r[key]['occurrence_fraction'] is not None]
        out[key] = dict(nonempty_n=len(values), mean_document_coverage=sum(values) / len(values) if values else None)
    return out


def run(data, folds, output):
    if output.exists(): raise ValueError('Use a new output file')
    rows = [json.loads(s) for s in data.read_text().splitlines()]
    prior = json.loads((folds / 'training_results.json').read_text())
    if digest(data) != prior['input_sha256']: raise ValueError('Training fingerprint mismatch')
    lookup = {r['id']: r for r in rows}
    report = dict(purpose='Descriptive training-only vocabulary survival audit',
        data_sha256=digest(data), fold_manifest_sha256=digest(folds / 'training_results.json'),
        validation_read=False, reserved_test_read=False, release_approved=False, folds=[], rows=[])
    for split in prior['folds']:
        validate_split(rows, split['train_ids'], split['held_ids'])
        path = folds / f"fold-{split['fold']}-baseline.joblib"
        if digest(path) != split['models']['baseline']['model_sha256']: raise ValueError('Model mismatch')
        saved = joblib.load(path)
        vec, model = saved['vectorizer'], saved['classifier']
        if vec.analyzer != 'word' or tuple(vec.ngram_range) != (1, 2): raise ValueError('Expected word 1,2 features')
        analyzer = vec.build_analyzer()
        report['folds'].append(dict(fold=split['fold'], train_ids=split['train_ids'], held_ids=split['held_ids'],
            model_sha256=digest(path), vocabulary_size=len(vec.vocabulary_),
            settings={k: vec.get_params()[k] for k in ('ngram_range','min_df','max_features','sublinear_tf','token_pattern','lowercase','stop_words','norm')}))
        for id in split['held_ids']:
            row = lookup[id]
            features = analyzer(row['text'])
            x = vec.transform([row['text']])
            probs = model.predict_proba(x)[0]
            all_features = coverage(features, vec.vocabulary_)
            if all_features['retained_distinct'] != x.nnz: raise ValueError('Feature count disagrees with transform')
            report['rows'].append(dict(id=id, fold=split['fold'], text_sha256=row['text_sha256'],
                gold=row['label'], strict_agreement=row['strict_agreement'],
                prediction=str(model.classes_[probs.argmax()]), probabilities=dict(zip(model.classes_.tolist(), probs.tolist())),
                sparse_nnz=x.nnz, all=all_features,
                unigrams=coverage([f for f in features if ' ' not in f], vec.vocabulary_),
                bigrams=coverage([f for f in features if ' ' in f], vec.vocabulary_)))
    if len(report['rows']) != len(rows) or {r['id'] for r in report['rows']} != set(lookup): raise ValueError('Invalid coverage')
    report['summary'] = {'overall': summarize(report['rows'])}
    for label in ('LEFT', 'CENTER', 'RIGHT'):
        report['summary'][label] = summarize([r for r in report['rows'] if r['gold'] == label])
    for correct in (True, False):
        report['summary']['correct' if correct else 'incorrect'] = summarize(
            [r for r in report['rows'] if (r['prediction'] == r['gold']) == correct])
    report['limitations'] = ['Coverage counts analyzer-emitted features, not raw words or semantic content',
        'Mean of per-document fractions; not occurrence-weighted across documents',
        'No causal attribution to min_df: vocabulary also depends on train topics, tokenization and feature cap',
        'Disputed noncommercial development labels; no independent accuracy or calibration claim']
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('data','folds','output'): p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    run(a.data, a.folds, a.output)
