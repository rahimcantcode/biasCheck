"""Score delivered highlights against unchanged, published BASIL references."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import re

HERE = Path(__file__).resolve().parent


def token_offsets(text):
    return [(m.start(), m.end()) for m in re.finditer(r'[^\W_]+', text, re.UNICODE)]


def token_set(tokens, spans):
    return {i for i, (start, end) in enumerate(tokens)
            if any(s['start'] < end and start < s['end'] for s in spans)}


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {'tp': tp, 'fp': fp, 'fn': fn, 'precision': p, 'recall': r,
            'f1': 2 * p * r / (p + r) if p + r else 0.0}


def match_count(pred, gold, edge):
    """Maximum cardinality bipartite matching, not many-to-many overlap credit."""
    assigned = {}

    def visit(i, seen):
        for j, ref in enumerate(gold):
            if j in seen or not edge(pred[i], ref):
                continue
            seen.add(j)
            if j not in assigned or visit(assigned[j], seen):
                assigned[j] = i
                return True
        return False

    return sum(visit(i, set()) for i in range(len(pred)))


def quantile(xs, q):
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    lower = math.floor(k)
    upper = math.ceil(k)
    return xs[lower] + (xs[upper] - xs[lower]) * (k - lower)


def wilson(k, n):
    if not n:
        return None
    z = 1.959963984540054
    p = k / n
    denominator = 1 + z*z/n
    middle = (p + z*z/(2*n)) / denominator
    radius = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denominator
    return [max(0, middle-radius), min(1, middle+radius)]


def score_case(case, row):
    assert row['id'] == case['id'] and row['source_sha256'] == case['source_sha256']
    body = row.get('response', {})
    predictions = body.get('spans', []) if row.get('http_status') == 200 else []
    text = case['text']
    assert hashlib.sha256(text.encode()).hexdigest() == case['source_sha256']
    if body:
        assert body['resolved_text'] == text and body['source_sha256'] == case['source_sha256']
        assert body['release_approved'] is False
    for s in predictions:
        assert text[s['start']:s['end']] == s['text']
    gold = case['gold']
    tokens = token_offsets(text)
    p = token_set(tokens, predictions)
    g = token_set(tokens, gold)
    lex = token_set(tokens, [s for s in gold if s['bias'] == 'lex'])
    pspans = sorted({(s['start'], s['end']) for s in predictions})
    gspans = sorted({(s['start'], s['end']) for s in gold})
    ptokens = [token_set(tokens, [{'start': a, 'end': b}]) for a, b in pspans]
    gtokens = [token_set(tokens, [{'start': a, 'end': b}]) for a, b in gspans]
    overlap = match_count(ptokens, gtokens, lambda a, b: bool(a & b))
    iou50 = match_count(ptokens, gtokens,
                        lambda a, b: bool(a | b) and len(a & b)/len(a | b) >= .5)
    exact = len(set(pspans) & set(gspans))
    quoted = [s for s in gold if s['quoted']]
    nonquoted = [s for s in gold if not s['quoted']]
    span_covered = lambda s: bool(p & token_set(tokens, [s]))
    return {
        'id': case['id'], 'event_id': case['event_id'], 'stratum': case['stratum'],
        'publisher': case['publisher'].lower(), 'source_sha256': case['source_sha256'],
        'status': body.get('status', 'request_failure'), 'http_status': row.get('http_status'),
        'seconds': row['seconds'], 'reference_positive': bool(gold),
        'delivered_positive': bool(predictions), 'token': prf(len(p & g), len(p - g), len(g - p)),
        'lexical_reference_tokens': len(lex), 'lexical_covered_tokens': len(lex & p),
        'reference_spans': len(gspans), 'predicted_spans': len(pspans),
        'exact_span': prf(exact, len(pspans)-exact, len(gspans)-exact),
        'overlap_span': prf(overlap, len(pspans)-overlap, len(gspans)-overlap),
        'iou50_span': prf(iou50, len(pspans)-iou50, len(gspans)-iou50),
        'quoted_reference_spans': len(quoted), 'quoted_covered_spans': sum(map(span_covered, quoted)),
        'nonquoted_reference_spans': len(nonquoted), 'nonquoted_covered_spans': sum(map(span_covered, nonquoted)),
        'attributed_predictions': sum(s.get('attribution') not in {None, 'unknown'} for s in predictions),
        'rejections': body.get('rejected', []),
        # Preserve offsets and labels for audit; no news text or generated rationales.
        'predictions': [{k: s[k] for k in ['start', 'end', 'bias_type', 'attribution']} for s in predictions],
    }


def aggregate(rows):
    tp = sum(r['reference_positive'] and r['delivered_positive'] for r in rows)
    fp = sum(not r['reference_positive'] and r['delivered_positive'] for r in rows)
    fn = sum(r['reference_positive'] and not r['delivered_positive'] for r in rows)
    tn = sum(not r['reference_positive'] and not r['delivered_positive'] for r in rows)
    count = len(rows)
    sentence = {**prf(tp, fp, fn), 'tn': tn, 'accuracy': (tp+tn)/count if count else None,
                'false_positive_rate': fp/(fp+tn) if fp+tn else None,
                'recall_wilson95': wilson(tp, tp+fn), 'fpr_wilson95': wilson(fp, fp+tn),
                'precision_wilson95': wilson(tp, tp+fp)}
    result = {'n': count, 'sentence': sentence,
              'statuses': dict(Counter(r['status'] for r in rows)),
              'rejected_spans': sum(len(r['rejections']) for r in rows),
              'rejection_reasons': dict(Counter(x['reason'] for r in rows for x in r['rejections']))}
    complete_correct = sum(r['status'] in {'suggestions', 'no_suggestions'}
                           and r['reference_positive'] == r['delivered_positive'] for r in rows)
    result['complete_correct_sentence_count'] = complete_correct
    result['complete_correct_sentence_fraction_all_requested'] = complete_correct/count if count else None
    for metric in ['token', 'exact_span', 'overlap_span', 'iou50_span']:
        result[metric] = prf(*(sum(r[metric][k] for r in rows) for k in ['tp', 'fp', 'fn']))
    result['lexical_reference_tokens'] = sum(r['lexical_reference_tokens'] for r in rows)
    result['lexical_covered_tokens'] = sum(r['lexical_covered_tokens'] for r in rows)
    result['lexical_token_recall'] = (result['lexical_covered_tokens']/result['lexical_reference_tokens']
                                       if result['lexical_reference_tokens'] else None)
    for k in ['quoted_reference_spans', 'quoted_covered_spans', 'nonquoted_reference_spans',
              'nonquoted_covered_spans', 'attributed_predictions', 'predicted_spans']:
        result[k] = sum(r[k] for r in rows)
    return result


def bootstrap(rows):
    rng = random.Random(20261004)
    groups = [[r for r in rows if r['stratum'] == s]
              for s in ['lexical', 'informational', 'unannotated']]
    scores = {k: [] for k in ['precision', 'recall', 'f1']}
    for _ in range(2000):
        sample = [rng.choice(group) for group in groups for _ in group]
        metric = prf(*(sum(r['token'][k] for r in sample) for k in ['tp', 'fp', 'fn']))
        for k in scores:
            scores[k].append(metric[k])
    return {k: [quantile(v, .025), quantile(v, .975)] for k, v in scores.items()}


def summarize(cases_path, results_path):
    manifest = json.loads((HERE / 'sample_manifest.json').read_text())
    raw_cases = cases_path.read_bytes()
    assert hashlib.sha256(raw_cases).hexdigest() == manifest['fixture_sha256']
    run = json.loads(results_path.read_text())
    assert run['fixture_sha256'] == manifest['fixture_sha256']
    assert run['protocol_sha256'] == manifest['protocol_sha256']
    assert hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest() == manifest['protocol_sha256']
    assert run['owned_processes_stopped'] is True and 'completed_utc' in run
    cases = json.loads(raw_cases)['cases']
    assert [r['id'] for r in run['rows']] == [c['id'] for c in cases]
    assert len(cases) == 60
    rows = [score_case(c, r) for c, r in zip(cases, run['rows'])]
    seconds = [r['seconds'] for r in rows]
    positives = sum(r['reference_positive'] for r in rows)
    report = {
        'kind': 'exploratory_published_human_reference_evaluation',
        'fixture_sha256': manifest['fixture_sha256'],
        'raw_results_sha256': hashlib.sha256(results_path.read_bytes()).hexdigest(),
        'protocol_sha256': manifest['protocol_sha256'],
        'started_utc': run['started_utc'], 'completed_utc': run['completed_utc'],
        'model_id': run['model_id'], 'model_revision': run['model_revision'],
        'weights_sha256': run['weights_sha256'], 'source_bindings': run['source_bindings'],
        'scorer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'release_approved': False, 'overall': aggregate(rows),
        'by_stratum': {s: aggregate([r for r in rows if r['stratum'] == s])
                       for s in ['lexical', 'informational', 'unannotated']},
        'balanced_lexical_control': aggregate([r for r in rows if r['stratum'] != 'informational']),
        'token_stratified_event_bootstrap95': bootstrap(rows),
        'sentence_constant_baselines': {
            'highlight_all': {**prf(positives, len(rows)-positives, 0), 'accuracy': positives/len(rows)},
            'highlight_none': {**prf(0, 0, positives), 'accuracy': (len(rows)-positives)/len(rows)},
            'balanced_lexical_control_accuracy_both': .5,
        },
        'latency_seconds': {'first': seconds[0], 'median': quantile(seconds, .5),
                            'warm_median': quantile(seconds[1:], .5), 'p90': quantile(seconds, .9),
                            'p95': quantile(seconds, .95), 'maximum': max(seconds),
                            'sum_requests': sum(seconds), 'startup': run['startup_seconds'],
                            'total_including_startup': run['total_seconds_including_startup']},
        'rows': rows,
    }
    failures = [r for r in rows if r['status'] not in {'suggestions', 'no_suggestions'}]
    report['complete_success_count'] = len(rows)-len(failures)
    if failures:
        report['complete_success_sensitivity'] = aggregate([r for r in rows if r not in failures])
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = summarize(args.cases, args.results)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'rows', 'source_bindings'}}, indent=2))
