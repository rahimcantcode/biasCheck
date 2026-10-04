"""Frozen paired development scorer; no inference, retries, or baseline rewrites.

The original scorer defines tokenization, matching and delivered-output metrics.
Failed negative cases still enter its confusion matrix as no delivered highlights;
complete_correct_sentence_count separately excludes all incomplete outcomes.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = HERE.parent / 'unbias_20261003' / 'realnews_basil60'
sys.path.insert(0, str(ROOT))
from backend.unbias.refinement import validate_refinement

spec = importlib.util.spec_from_file_location('archived_basil60_score', OLD / 'score.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
COMPLETE = {'suggestions', 'no_suggestions'}
ACTIVE = {'succeeded', 'failed'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_rows(cases, rows):
    require(len(rows) == len(cases) == 60, 'expected_all_60_records')
    require(len({c['id'] for c in cases}) == 60, 'duplicate_case_id')
    require([(r['id'], r['source_sha256']) for r in rows] ==
            [(c['id'], c['source_sha256']) for c in cases], 'case_identity_order_or_hash')
    for c in cases:
        require(sha(c['text'].encode()) == c['source_sha256'], 'source_hash_mismatch')


def validate_pair(case, baseline, candidate):
    require(candidate['original_http_status'] == baseline['http_status'], 'original_status_changed')
    require(candidate['seconds'] == baseline['seconds'], 'baseline_latency_changed')
    seconds = candidate['refinement_seconds']
    require(type(seconds) in {int, float} and math.isfinite(seconds) and seconds >= 0,
            'invalid_refinement_latency')
    before = baseline.get('response') or {}
    after = candidate.get('response') or {}
    parents = before.get('spans', []) if baseline['http_status'] == 200 else []
    state = candidate['refinement_status']
    if not parents:
        expected = 'skipped_upstream_failure' if baseline['http_status'] != 200 else 'skipped_no_spans'
        require(state == expected and seconds == 0, 'invalid_skipped_outcome')
        require(candidate['http_status'] == baseline['http_status'] and after == before,
                'upstream_outcome_changed')
        return []
    require(state in ACTIVE, 'accepted_spans_require_refinement_outcome')
    if state == 'failed':
        require(candidate['http_status'] == 503 and not after.get('spans')
                and after.get('status') not in COMPLETE, 'refinement_failure_must_withhold')
        return []
    result = candidate['refinement_result']
    verified = validate_refinement(case['text'], parents, {'decisions': result['decisions']})
    require(result == verified, 'refinement_result_not_verified')
    require(candidate['http_status'] == 200 and after.get('spans') == verified['spans'],
            'delivered_spans_differ_from_refinement')
    expected = ('partial_failure' if before.get('status') == 'partial_failure' else
                'suggestions' if verified['spans'] else 'no_suggestions')
    require(after.get('status') == expected, 'upstream_partial_or_refinement_status_changed')
    require(after.get('rejected', []) == before.get('rejected', []), 'upstream_rejections_changed')
    return result['decisions']


def score(case, row):
    # Preserve old scoring exactly; publish only its text-free fields.
    result = old.score_case(case, row)
    result['rejections'] = [{'reason': r['reason'] if re.fullmatch(r'[a-z_]+', r['reason'])
                             else 'unclassified_rejection'} for r in result['rejections']]
    require(all(s['attribution'] == 'unknown' for s in result['predictions']),
            'unsupported_attribution')
    return result


def groups(rows):
    return {'all_60': old.aggregate(rows),
            'lexical_plus_unannotated_40': old.aggregate([r for r in rows if r['stratum'] != 'informational']),
            'by_stratum': {s: old.aggregate([r for r in rows if r['stratum'] == s])
                           for s in ['lexical', 'informational', 'unannotated']}}


def compare_runs(cases, baseline, candidate):
    check_rows(cases, baseline['rows'])
    check_rows(cases, candidate['rows'])
    require(Counter(c['stratum'] for c in cases) ==
            Counter(lexical=20, informational=20, unannotated=20), 'wrong_strata')
    require(candidate.get('completed_utc') and
            candidate.get('runtime', {}).get('owned_process_stopped') is True,
            'incomplete_run_or_owned_process_not_stopped')
    require(candidate.get('code_unchanged') is True, 'candidate_code_changed_or_unverified')
    decisions = [validate_pair(c, b, r) for c, b, r in zip(cases, baseline['rows'], candidate['rows'])]
    metrics, paired_rows = {}, []
    for name, run in [('baseline', baseline), ('refinement', candidate)]:
        all_rows = [score(c, r) for c, r in zip(cases, run['rows'])]
        lex_rows = [score({**c, 'gold': [g for g in c['gold'] if g['bias'] == 'lex']}, r)
                    for c, r in zip(cases, run['rows'])]
        metrics[name] = {'all_reference': groups(all_rows), 'lexical_only_reference': groups(lex_rows)}
        if name == 'baseline':
            paired_rows = [{'id': r['id'], 'source_sha256': r['source_sha256'],
                            'stratum': r['stratum'], 'baseline': r} for r in all_rows]
        else:
            for out, r, lexical, raw, ds in zip(paired_rows, all_rows, lex_rows, run['rows'], decisions):
                out.update(refinement=r, refinement_lexical_only=lexical,
                           refinement_status=raw['refinement_status'],
                           refinement_seconds=raw['refinement_seconds'],
                           decisions=[{k: d[k] for k in ['native_index', 'action']} for d in ds])
    active = [r['refinement_seconds'] for r in candidate['rows'] if r['refinement_status'] in ACTIVE]
    return {
        'kind': 'paired_exposed_development_comparison', 'release_approved': False,
        'independent_accuracy_test': False, 'attribution_supported': False,
        'status_origin': 'derived_pipeline_outcome_not_http',
        'limitations': ['Informational bias is outside the lexical refinement target.',
                       'Lexical-only all-60 scores count informational-only references as negatives.',
                       'BASIL absence is not proof of neutrality; sentence context limits reference fit.',
                       'Delivered-output confusion matrices credit failed negatives as empty output; use complete-correct counts.',
                       'Refinement cannot recover detector misses; these exposed cases are development evidence.'],
        'metrics': metrics, 'rows': paired_rows,
        'refinement_outcomes': dict(Counter(r['refinement_status'] for r in candidate['rows'])),
        'decision_counts': {k: sum(d['action'] == k for ds in decisions for d in ds) for k in ['keep', 'narrow', 'drop']},
        'added_latency_seconds_active_calls_only': {
            'n': len(active), 'sum': sum(active),
            **{k: old.quantile(active, q) if active else None for k, q in [('median', .5), ('p90', .9), ('p95', .95)]},
            'maximum': max(active) if active else None},
    }


def summarize(cases_path, baseline_path, refinement_path):
    manifest = json.loads((OLD / 'sample_manifest.json').read_text())
    archived = json.loads((OLD / 'summary.json').read_text())
    fixture_raw, baseline_raw, refined_raw = [Path(p).read_bytes() for p in [cases_path, baseline_path, refinement_path]]
    require(sha(fixture_raw) == manifest['fixture_sha256'], 'fixture_hash_mismatch')
    require(sha(baseline_raw) == archived['raw_results_sha256'], 'archived_baseline_hash_mismatch')
    baseline, candidate = json.loads(baseline_raw), json.loads(refined_raw)
    require(candidate.get('baseline_sha256') == sha(baseline_raw), 'candidate_baseline_hash_mismatch')
    require(candidate.get('fixture_sha256') == baseline.get('fixture_sha256') == sha(fixture_raw), 'candidate_fixture_hash_mismatch')
    report = compare_runs(json.loads(fixture_raw)['cases'], baseline, candidate)
    report.update(fixture_sha256=sha(fixture_raw), baseline_sha256=sha(baseline_raw),
                  refinement_sha256=sha(refined_raw), scorer_sha256=sha(Path(__file__).read_bytes()),
                  reused_scorer_sha256=sha((OLD / 'score.py').read_bytes()),
                  completed_utc=candidate['completed_utc'])
    return report


def write_report(output, report):
    # Exclusive creation also closes the check/write race for existing evidence.
    with Path(output).open('x') as handle:
        handle.write(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['cases', 'baseline', 'refinement', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.resolve().is_relative_to(OLD.resolve()), 'cannot_overwrite_archived_results')
    require(args.output.resolve() not in {p.resolve() for p in [args.cases, args.baseline, args.refinement]}, 'cannot_overwrite_inputs')
    require(not args.output.exists(), 'cannot_overwrite_existing_output')
    report = summarize(args.cases, args.baseline, args.refinement)
    write_report(args.output, report)
    print(json.dumps({'output': str(args.output), 'decision_counts': report['decision_counts']}))
