"""Training-only OOF confidence diagnostics; never selects or approves a policy."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

LABELS = ('LEFT', 'CENTER', 'RIGHT')


def audit(rows):
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Expected nonempty unique examples')
    if any(r['gold'] not in LABELS or set(r['probabilities']) != set(LABELS) for r in rows):
        raise ValueError('Invalid labels')
    p = np.array([[r['probabilities'][k] for k in LABELS] for r in rows], dtype=float)
    if not np.isfinite(p).all() or (p < 0).any() or (p > 1).any() or not np.allclose(p.sum(axis=1), 1, atol=1e-10, rtol=0):
        raise ValueError('Invalid probabilities')
    gold = np.array([LABELS.index(r['gold']) for r in rows])
    pred = p.argmax(axis=1)
    if any(r['prediction'] != LABELS[i] for r, i in zip(rows, pred)):
        raise ValueError('Stored prediction disagrees with probability argmax')
    correct = pred == gold
    confidence = p.max(axis=1)
    bins = []
    # Half-open bins; include confidence exactly one in the last bin.
    indices = np.minimum((confidence * 10).astype(int), 9)
    for b in range(10):
        mask = indices == b
        bins.append(dict(lower=b / 10, upper=(b + 1) / 10, n=int(mask.sum()),
            accuracy=float(correct[mask].mean()) if mask.any() else None,
            mean_confidence=float(confidence[mask].mean()) if mask.any() else None))
    ece = sum(b['n'] / len(rows) * abs(b['accuracy'] - b['mean_confidence']) for b in bins if b['n'])
    curves = []
    for fraction in (1., .8, .6, .4, .2):
        rank = int(np.ceil(fraction * len(rows)))
        threshold = float(np.sort(confidence)[-rank])
        accepted = confidence >= threshold
        classes = {}
        for i, label in enumerate(LABELS):
            mask = gold == i
            n = int(mask.sum())
            delivered = int((mask & accepted & correct).sum())
            classes[label] = dict(reference_n=n, retained_n=int((mask & accepted).sum()),
                correct_and_retained_n=delivered, delivered_recall=delivered / n if n else None)
        curves.append(dict(target_fraction=fraction, threshold=threshold, retained_n=int(accepted.sum()),
            coverage=float(accepted.mean()), selective_accuracy=float(correct[accepted].mean()),
            correct_and_retained_fraction=float((correct & accepted).mean()), per_class=classes,
            retained_ids=[r['id'] for r, keep in zip(rows, accepted) if keep]))
    true_p = p[np.arange(len(rows)), gold]
    return dict(n=len(rows), raw_accuracy=float(correct.mean()),
        multiclass_brier_sum=float(((p - np.eye(3)[gold]) ** 2).sum(axis=1).mean()),
        nll=float(-np.log(np.clip(true_p, 1e-15, 1)).mean()), nll_clip=1e-15,
        ece_10_equal_width=float(ece), bins=bins,
        correctness_auc=float(roc_auc_score(correct, confidence)) if len(set(correct)) == 2 else None,
        retained_fraction_diagnostics=curves)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Use a new output path')
    raw = args.source.read_bytes()
    source = json.loads(raw)
    report = dict(purpose='Training-only descriptive confidence audit; no threshold selection',
        source_sha256=hashlib.sha256(raw).hexdigest(), data_sha256=source['data_sha256'],
        fold_manifest_sha256=source['fold_manifest_sha256'], release_approved=False,
        validation_read=False, reserved_test_read=False,
        models={name: audit(rows) for name, rows in source['oof'].items()},
        limitations=['Small repeatedly inspected development data with disputed labels',
            'Fold-specific models and event dependencies; no independent calibration claim',
            'Fixed-width ECE is descriptive and bin-dependent; no uncertainty intervals',
            'All confidence ties retained; actual coverage may exceed target',
            'Abstained examples remain in each reference-class denominator'])
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps({name: {k: r[k] for k in ('raw_accuracy', 'multiclass_brier_sum',
        'nll', 'ece_10_equal_width', 'correctness_auc')} for name, r in report['models'].items()}, indent=2))
