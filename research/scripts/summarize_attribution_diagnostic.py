"""Describe frozen synthetic paired probes without assigning gold labels."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

LABELS = ('LEFT', 'CENTER', 'RIGHT')
PAIRS = (
    ('market-endorsement', 'market-rejection'),
    ('market-endorsement', 'market-quotation'),
    ('market-endorsement', 'market-preface'),
    ('safety-net-endorsement', 'safety-net-quotation'),
    ('market-endorsement', 'safety-net-endorsement'),
)


def paired_change(first, second):
    a, b = first['probabilities'], second['probabilities']
    return {
        'released_label_changed': first['label'] != second['label'],
        'raw_label_changed': first['raw_label'] != second['raw_label'],
        'decision_changed': first['decision'] != second['decision'],
        'score_deltas': {label: b[label] - a[label] for label in LABELS},
        'total_variation': sum(abs(b[label] - a[label]) for label in LABELS) / 2,
    }


def summarize(inputs, audit):
    wanted = {row['id']: row for row in inputs}
    if len(wanted) != len(inputs):
        raise ValueError('Duplicate input IDs')
    cases = audit['cases']
    if len(cases) != len(wanted) or {r['id'] for r in cases} != set(wanted):
        raise ValueError('Missing, duplicate or unexpected browser cases')
    records = []
    models = []
    for case in cases:
        body = case['result']
        if case['status'] != 200 or body['resolved_text'] != wanted[case['id']]['text']:
            raise ValueError('Failed response or changed input text')
        model = body.get('model')
        if not model:
            raise ValueError('Missing model provenance')
        models.append(model)
        records.append({'id': case['id'], 'text_sha256': hashlib.sha256(
            body['resolved_text'].encode()).hexdigest(), 'overall': body['overall']})
    if any(model != models[0] for model in models):
        raise ValueError('Model metadata changed between paired probes')
    by_id = {row['id']: row['overall'] for row in records}
    return {
        'purpose': 'AI-authored paired diagnostic; not human gold or accuracy',
        'human_reviewed': False, 'started_at': audit['started_at'],
        'finished_at': audit['finished_at'], 'model': models[0],
        'cases': records,
        'label_counts': dict(Counter(r['overall']['label'] for r in records)),
        'abstentions': sum(r['overall']['decision'] == 'abstained' for r in records),
        'pairs': [{'first': a, 'second': b, **paired_change(by_id[a], by_id[b])}
                  for a, b in PAIRS],
        'browser': audit['browser'], 'environment': audit['environment'],
        'page_errors': audit['page_errors'], 'failed_requests': audit['failed_requests'],
        'mobile_overflow': audit['mobile_overflow'],
        'limitations': ['Six selected AI-authored cases are not representative',
                       'No accuracy or correctness inferred from flips or invariance',
                       'Wording, stance and attribution effects are confounded',
                       'Softmax scores are not calibrated correctness probabilities'],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = summarize(json.loads(args.input.read_text()), json.loads(args.audit.read_text()))
    result['input_file_sha256'] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    result['audit_file_sha256'] = hashlib.sha256(args.audit.read_bytes()).hexdigest()
    result['screenshots_sha256'] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(args.audit.parent.glob('*.png'))}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'counts': result['label_counts'], 'pairs': result['pairs']}, indent=2))
