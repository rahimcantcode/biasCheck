"""Synthetic paired-score mechanics, not semantic quality evidence."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / 'research/experiments/unbias_20261004/compare.py'
spec = importlib.util.spec_from_file_location('paired_comparison', PATH)
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


@pytest.fixture
def inputs():
    cases, rows = [], []
    text = 'Loaded wording, factual context.'
    digest = hashlib.sha256(text.encode()).hexdigest()
    for i in range(60):
        group = ['lexical', 'informational', 'unannotated'][i // 20]
        gold = [] if group == 'unannotated' else [dict(start=0, end=6, bias='lex' if group == 'lexical' else 'inf', quoted=False)]
        cases.append(dict(id=str(i), source_sha256=digest, text=text, event_id=str(i),
                          stratum=group, publisher='test', gold=gold))
        rows.append(dict(id=str(i), source_sha256=digest, http_status=200, seconds=1.,
                         response=dict(resolved_text=text, source_sha256=digest, release_approved=False,
                                       status='no_suggestions', spans=[], rejected=[])))
    baseline = dict(rows=rows)
    candidate = dict(rows=copy.deepcopy(rows), completed_utc='2026-10-04T00:00:00Z',
                     runtime=dict(owned_process_stopped=True), code_unchanged=True)
    for row in candidate['rows']:
        row.update(original_http_status=200, refinement_status='skipped_no_spans', refinement_seconds=0.)
    return cases, baseline, candidate


def activate(inputs, index=0, action='keep', partial=False):
    cases, baseline, candidate = inputs
    body = baseline['rows'][index]['response']
    span = dict(native_index=0, start=0, end=14, text=cases[index]['text'][:14],
                bias_type='loaded_language', reason='fixture', attribution='unknown')
    body.update(spans=[span], status='partial_failure' if partial else 'suggestions')
    decision = dict(native_index=0, action=action, original='' if action == 'drop' else span['text'],
                    reason='fixture', bias_type=None if action == 'drop' else 'loaded_language')
    result = compare.validate_refinement(cases[index]['text'], [span], {'decisions': [decision]})
    row = candidate['rows'][index]
    row.update(refinement_status='succeeded', refinement_seconds=2., refinement_result=result)
    row['response'] = copy.deepcopy(body)
    row['response'].update(spans=result['spans'], status='partial_failure' if partial else
                           'no_suggestions' if action == 'drop' else 'suggestions')


@pytest.mark.parametrize('mutation', ['missing', 'identity', 'hash', 'order'])
def test_reject_incomplete_or_unpaired(inputs, mutation):
    cases, baseline, candidate = inputs
    if mutation == 'missing':
        candidate['rows'].pop()
    elif mutation == 'order':
        candidate['rows'].reverse()
    else:
        candidate['rows'][0]['id' if mutation == 'identity' else 'source_sha256'] = 'changed'
    with pytest.raises(ValueError):
        compare.compare_runs(cases, baseline, candidate)


def test_failure_never_gets_complete_negative_credit(inputs):
    cases, baseline, candidate = inputs
    baseline['rows'][40].update(http_status=503, response={})
    candidate['rows'][40].update(http_status=503, response={}, original_http_status=503,
                                  refinement_status='skipped_upstream_failure')
    report = compare.compare_runs(*inputs)
    result = report['metrics']['refinement']['all_reference']['by_stratum']['unannotated']
    assert result['sentence']['tn'] == 20
    assert result['complete_correct_sentence_count'] == 19
    candidate['rows'][40]['response'] = dict(status='no_suggestions')
    with pytest.raises(ValueError, match='upstream_outcome_changed'):
        compare.compare_runs(*inputs)


def test_lexical_reference_groups_are_distinct(inputs):
    # Add informational annotation to lexical group; it must be removed only in lexical-only view.
    inputs[0][0]['gold'].append(dict(start=16, end=23, bias='inf', quoted=False))
    report = compare.compare_runs(*inputs)
    metrics = report['metrics']['baseline']
    assert metrics['all_reference']['all_60']['token']['fn'] == 41
    assert metrics['lexical_only_reference']['all_60']['token']['fn'] == 20
    assert metrics['lexical_only_reference']['lexical_plus_unannotated_40']['n'] == 40
    assert metrics['all_reference']['by_stratum']['informational']['n'] == 20


def test_partial_preserved_and_latency_counts_only_active(inputs):
    activate(inputs, partial=True)
    report = compare.compare_runs(*inputs)
    assert report['decision_counts'] == dict(keep=1, narrow=0, drop=0)
    assert report['added_latency_seconds_active_calls_only']['n'] == 1
    assert report['added_latency_seconds_active_calls_only']['median'] == 2
    inputs[2]['rows'][0]['response']['status'] = 'suggestions'
    with pytest.raises(ValueError, match='upstream_partial'):
        compare.compare_runs(*inputs)


def test_refinement_failure_withholds_and_is_not_empty_success(inputs):
    activate(inputs, index=40)
    row = inputs[2]['rows'][40]
    row.update(refinement_status='failed', http_status=503, response={})
    report = compare.compare_runs(*inputs)
    assert report['metrics']['refinement']['all_reference']['by_stratum']['unannotated']['complete_correct_sentence_count'] == 19
    row.update(http_status=200)
    with pytest.raises(ValueError, match='failure_must_withhold'):
        compare.compare_runs(*inputs)


def test_no_generated_text_in_report(inputs):
    activate(inputs)
    result = json.dumps(compare.compare_runs(*inputs))
    assert inputs[0][0]['text'] not in result
    assert 'Loaded wording' not in result
    assert 'reason": "fixture' not in result


def test_fixture_and_baseline_binding(tmp_path, monkeypatch, inputs):
    cases, baseline, candidate = inputs
    paths = [tmp_path / name for name in ['cases.json', 'baseline.json', 'refinement.json']]
    paths[0].write_text(json.dumps({'cases': cases}))
    paths[1].write_text(json.dumps(baseline))
    fixture_hash, baseline_hash = [compare.sha(p.read_bytes()) for p in paths[:2]]
    baseline['fixture_sha256'] = fixture_hash
    paths[1].write_text(json.dumps(baseline))
    baseline_hash = compare.sha(paths[1].read_bytes())
    candidate.update(fixture_sha256=fixture_hash, baseline_sha256=baseline_hash)
    paths[2].write_text(json.dumps(candidate))
    (tmp_path / 'sample_manifest.json').write_text(json.dumps({'fixture_sha256': fixture_hash}))
    (tmp_path / 'summary.json').write_text(json.dumps({'raw_results_sha256': baseline_hash}))
    (tmp_path / 'score.py').write_text('synthetic scorer hash fixture')
    monkeypatch.setattr(compare, 'OLD', tmp_path)
    assert compare.summarize(*paths)['baseline_sha256'] == baseline_hash
    candidate['baseline_sha256'] = 'wrong'
    paths[2].write_text(json.dumps(candidate))
    with pytest.raises(ValueError, match='candidate_baseline_hash'):
        compare.summarize(*paths)
    paths[0].write_text('{}')
    with pytest.raises(ValueError, match='fixture_hash'):
        compare.summarize(*paths)


@pytest.mark.parametrize('value', [False, None])
def test_changed_or_unverified_code_rejected(inputs, value):
    inputs[2]['code_unchanged'] = value
    with pytest.raises(ValueError, match='candidate_code_changed_or_unverified'):
        compare.compare_runs(*inputs)


def test_existing_output_never_overwritten(tmp_path):
    output = tmp_path / 'comparison.json'
    compare.write_report(output, {'first': True})
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        compare.write_report(output, {'replacement': True})
    assert output.read_bytes() == original
