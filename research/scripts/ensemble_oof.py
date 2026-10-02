"""Fixed averaging of matched training OOF predictions, without tuning."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from corpus_experiment import metrics

LABELS = ('LEFT', 'CENTER', 'RIGHT')


def combine(first, second):
    if first['id'] != second['id'] or first['fold'] != second['fold']:
        raise ValueError('OOF ID/fold mismatch')
    for row in (first, second):
        scores = row['probabilities']
        if set(scores) != set(LABELS) or any(not math.isfinite(v) or not 0 <= v <= 1 for v in scores.values()) or not math.isclose(sum(scores.values()), 1, abs_tol=1e-6):
            raise ValueError('Invalid class probabilities')
        if row['prediction'] not in LABELS or scores[row['prediction']] != max(scores.values()):
            raise ValueError('Prediction disagrees with probability maximum')
    scores = {label: (first['probabilities'][label] + second['probabilities'][label]) / 2 for label in LABELS}
    return {'id': first['id'], 'fold': first['fold'], 'probabilities': scores,
            'prediction': max(LABELS, key=scores.get),
            'components_agree': first['prediction'] == second['prediction']}


def run(data, source, output):
    if output.exists():
        raise ValueError('Use a new output path')
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    prior = json.loads(source.read_text())
    if prior['data_sha256'] != hashlib.sha256(data.read_bytes()).hexdigest():
        raise ValueError('Training input hash mismatch')
    ids = {r['id'] for r in rows}
    if len(ids) != len(rows) or not ids:
        raise ValueError('Unique nonempty reference IDs required')
    components = {}
    for name in ('word', 'semantic'):
        values = prior['oof'][name]
        aligned = {r['id']: r for r in values}
        if len(values) != len(rows) or set(aligned) != ids:
            raise ValueError('Incomplete or duplicate OOF IDs')
        components[name] = aligned
    predictions = [combine(components['word'][r['id']], components['semantic'][r['id']]) for r in rows]
    agreeing = [i for i, p in enumerate(predictions) if p['components_agree']]
    word_ok = [components['word'][r['id']]['prediction'] == r['label'] for r in rows]
    semantic_ok = [components['semantic'][r['id']]['prediction'] == r['label'] for r in rows]
    ensemble_ok = [p['prediction'] == r['label'] for r, p in zip(rows, predictions)]
    result = {'purpose': 'Fixed training OOF ensemble, not independent product evaluation',
              'release_approved': False, 'reserved_test_read': False, 'validation_read': False,
              'settings': {'word_weight': .5, 'semantic_weight': .5, 'tie_order': LABELS, 'tuned': False},
              'inputs': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in (data, source)},
              'component_folds_and_hashes': prior['folds'], 'encoder': prior['encoder'],
              'metrics': metrics(rows, [p['prediction'] for p in predictions]), 'predictions': predictions,
              'corrected_vs_word': sum(e and not w for e, w in zip(ensemble_ok, word_ok)),
              'regressed_vs_word': sum(w and not e for e, w in zip(ensemble_ok, word_ok)),
              'both_components_wrong': sum(not w and not s for w, s in zip(word_ok, semantic_ok)),
              'oracle_either_correct_n': sum(w or s for w, s in zip(word_ok, semantic_ok)),
              'agreement_subset': {'n': len(agreeing), 'coverage': len(agreeing) / len(rows),
                 'matches': sum(ensemble_ok[i] for i in agreeing),
                 'agreement': sum(ensemble_ok[i] for i in agreeing) / len(agreeing) if agreeing else None},
              'cautions': ['Oracle either-correct count assumes perfect selection, not achievable performance or an upper bound for probability averaging',
                           'Agreement-only accuracy is selective and does not establish overall accuracy',
                           'Balanced-class probabilities are uncalibrated; equal weights are a fixed baseline',
                           'Event-string grouping is not proven event-family independence',
                           'Previously explored training data and noncommercial corpus; no release']}
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('metrics', 'corrected_vs_word', 'regressed_vs_word', 'both_components_wrong', 'oracle_either_correct_n', 'agreement_subset')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('data', 'source', 'output'):
        parser.add_argument(f'--{name}', type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.source, args.output)
