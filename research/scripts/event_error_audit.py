"""Descriptive event concentration of frozen OOF errors, not model selection."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


def summarize(rows, predictions):
    lookup = {r['id']: r for r in rows}
    ids = [p['id'] for p in predictions]
    if len(lookup) != len(rows) or len(set(ids)) != len(ids) or set(ids) != set(lookup):
        raise ValueError('Expected unique, complete aligned IDs')
    groups = defaultdict(list)
    for p in predictions:
        r = lookup[p['id']]
        if p['gold'] != r['label'] or p['text_sha256'] != r['text_sha256']:
            raise ValueError('Reference mismatch')
        if p['prediction'] not in ('LEFT', 'CENTER', 'RIGHT'):
            raise ValueError('Invalid prediction')
        groups[r['event']].append(dict(id=r['id'], gold=r['label'], prediction=p['prediction'],
            strict_agreement=r['strict_agreement'], correct=p['prediction'] == r['label'], fold=p['fold']))
    events = []
    for event, records in groups.items():
        if len({r['fold'] for r in records}) != 1:
            raise ValueError('An event crosses held-out folds')
        correct = sum(r['correct'] for r in records)
        center = [r for r in records if r['gold'] == 'CENTER']
        events.append(dict(event=event, n=len(records), correct=correct, errors=len(records)-correct,
            accuracy=correct/len(records), label_counts=dict(Counter(r['gold'] for r in records)),
            strict_agreement_n=sum(r['strict_agreement'] for r in records),
            center_n=len(center), center_errors=sum(not r['correct'] for r in center), records=records))
    events.sort(key=lambda e: (-e['errors'], e['event']))
    errors = sum(e['errors'] for e in events)
    return dict(n=len(rows), event_n=len(events), errors=errors, events=events,
        top_five_error_count=sum(e['errors'] for e in events[:5]),
        top_five_error_share=sum(e['errors'] for e in events[:5])/errors if errors else None,
        top_five_row_count=sum(e['n'] for e in events[:5]),
        events_with_errors=sum(e['errors'] > 0 for e in events),
        events_with_center=sum(e['center_n'] > 0 for e in events),
        events_with_center_errors=sum(e['center_errors'] > 0 for e in events),
        center_errors=sum(e['center_errors'] for e in events))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('data', 'predictions', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.predictions.read_text())
    if digest(args.data) != source['data_sha256']:
        raise ValueError('Training data hash mismatch')
    report = summarize([json.loads(s) for s in args.data.read_text().splitlines()], source['oof']['baseline'])
    report.update(data_sha256=digest(args.data), predictions_sha256=digest(args.predictions),
        source_model_folds=source['folds'], script_sha256=digest(Path(__file__)),
        validation_read=False, reserved_test_read=False, release_approved=False,
        limitations=['Descriptive, reused training OOF predictions with disputed noncommercial labels.',
                    'Events sorted by observed error count; larger groups have more opportunities for errors.',
                    'Event strings are not guaranteed independent event families; concentration is not causation or evidence of incorrect labels.'])
    with args.output.open('x') as f:
        json.dump(report, f, indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ('events','source_model_folds')}, indent=2))
