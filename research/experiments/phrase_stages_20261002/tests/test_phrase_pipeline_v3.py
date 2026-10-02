"""Structural/synthetic unit tests, never evidence of semantic model accuracy."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from backend.evidence import EvidenceValidationError, validate_prediction
from backend.phrase_pipeline_v3 import (MAX_CANDIDATES, PROMPTS, STAGES, assemble_prediction,
    decision_schema, extraction_schema, payload_for, validate_candidates,
    validate_completion, validate_decisions, validate_extraction)
from research.scripts.probe_phrase_pipeline_v3 import (evaluate_all, exact_diagnostic,
    run_case, stable_hash)

TEXT = '🐈 Café\r\nThe government must not privatize public healthcare.\r\nDone.'
QUOTE = 'The government must not privatize public healthcare'
PROTOCOL = {'model': 'pinned', 'seed': 20261002, 'temperature': 0,
            'output_token_limit': 1024, 'context_tokens': 4096, 'runtime_fingerprint': 'pinned'}


def extracted(*texts):
    return {'spans': [{'text': text, 'context': ''} for text in texts], 'reason': 'Synthetic extraction'}


def choices(stage, candidates, value):
    return {item['id']: {stage: value, 'reason': 'Synthetic decision'} for item in candidates}


def completion(decoded):
    return {'system_fingerprint': 'pinned', 'usage': {'prompt_tokens': 700, 'completion_tokens': 90},
            'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(decoded)}}]}


class FakeRuntime:
    proc = None
    def __init__(self, outputs, count=700):
        self.outputs = list(outputs)
        self.bodies = []
        self.preflights = []
        self.count = count
    def exact_input_tokens(self, body):
        self.preflights.append(deepcopy(body))
        return self.count
    def request(self, path, body, timeout):
        assert path == '/v1/chat/completions'
        self.bodies.append(deepcopy(body))
        value = self.outputs.pop(0)
        if isinstance(value, Exception):
            raise value
        return completion(value)


def test_unicode_crlf_negation_boundaries_survive_all_stages():
    candidates = validate_extraction(TEXT, extracted(QUOTE))
    directions = choices('direction', candidates, 'LEFT')
    speakers = choices('speaker', candidates, 'NARRATOR')
    prediction = assemble_prediction(TEXT, candidates, directions, speakers)
    result = validate_prediction(TEXT, prediction)[0]
    assert result['text'] == QUOTE and result['start'] == TEXT.index(QUOTE)
    assert TEXT[result['start']:result['end']] == QUOTE
    assert 'must not' in result['text'] and result['attribution'] == 'author'
    for stage in STAGES:
        body = payload_for(stage, TEXT, [] if stage == 'extract' else candidates, PROTOCOL)
        content = json.loads(body['messages'][1]['content'])
        assert content['source'] == TEXT
        assert body['temperature'] == 0 and body['seed'] == 20261002
        assert body['chat_template_kwargs'] == {'enable_thinking': False}
        if stage != 'extract':
            assert content['candidates'] == candidates
        assert 'expected' not in content


def test_extraction_has_no_ideology_or_speaker_response_fields():
    assert set(extraction_schema()['properties']) == {'spans', 'reason'}
    assert set(extraction_schema()['properties']['spans']['items']['properties']) == {'text', 'context'}
    assert 'LEFT' not in PROMPTS['extract'] and 'RIGHT' not in PROMPTS['extract']


def test_repeated_text_requires_unique_exact_context_and_preserves_occurrence():
    source = '"policy is good" said a guest. My view: policy is good.'
    value = {'spans': [{'text': 'policy is good', 'context': '"policy is good"'},
                       {'text': 'policy is good', 'context': 'My view: policy is good'}], 'reason': 'test'}
    candidates = validate_extraction(source, value)
    assert [s['occurrence'] for s in candidates] == [0, 1]
    assert [s['id'] for s in candidates] == ['c000', 'c001']
    speakers = {'c000': {'speaker': 'DIRECT_QUOTED_SPEAKER', 'reason': 'Guest'},
                'c001': {'speaker': 'NARRATOR', 'reason': 'Own voice'}}
    out = assemble_prediction(source, candidates, choices('direction', candidates, 'LEFT'), speakers)
    assert [s['attribution'] for s in out['spans']] == ['quoted', 'author']


@pytest.mark.parametrize('value', [extracted('missing'), extracted('tax', 'tax'),
    {'spans': [{'text': 'tax', 'context': 'invented tax'}], 'reason': 'test'},
    {'spans': [], 'reason': ''}, {'spans': [], 'reason': 'test', 'predictions': []},
    {'spans': [{'text': 'tax', 'context': '', 'label': 'LEFT'}], 'reason': 'test'}])
def test_extraction_rejects_absent_duplicate_extra_fields_or_bad_context(value):
    with pytest.raises(ValueError):
        validate_extraction('tax policy', value)


@pytest.mark.parametrize('text', ['Café', 'Café\n', 'café', 'Café.'])
def test_extraction_does_not_normalize_source(text):
    with pytest.raises(ValueError):
        validate_extraction('Café\r\n', extracted(text))


def test_extraction_rejects_ambiguous_or_overlapping_candidates():
    for source, value in [('tax tax', extracted('tax')), ('tax policy', extracted('tax', 'tax policy'))]:
        with pytest.raises(ValueError):
            validate_extraction(source, value)


def test_candidate_count_excess_is_rejected_not_sliced():
    tokens = [f'word{i:02d}' for i in range(MAX_CANDIDATES + 1)]
    with pytest.raises(ValueError):
        validate_extraction(' '.join(tokens), extracted(*tokens))


@pytest.mark.parametrize('field,value', [('text', 'government'), ('start', 0), ('end', 1),
    ('id', 'c999'), ('occurrence', True), ('context', 'invented')])
def test_downstream_rejects_candidate_mutation(field, value):
    candidates = validate_extraction(TEXT, extracted(QUOTE))
    candidates[0][field] = value
    with pytest.raises(ValueError):
        validate_candidates(TEXT, candidates)


@pytest.mark.parametrize('stage,value', [('direction', 'LEFT'), ('speaker', 'NARRATOR')])
def test_dynamic_schema_requires_exact_ids_and_no_extra_envelope(stage, value):
    candidates = validate_extraction('one two', extracted('one', 'two'))
    schema = decision_schema(stage, candidates)
    assert schema['required'] == ['c000', 'c001']
    assert not schema['additionalProperties']
    good = choices(stage, candidates, value)
    assert validate_decisions(stage, candidates, good) == good
    for malformed in [{}, {'c000': good['c000']}, {**good, 'c002': good['c000']}, {'predictions': good},
                      {'c000': {stage: 'UNKNOWN', 'reason': 'test'}, 'c001': good['c001']}]:
        with pytest.raises(ValueError):
            validate_decisions(stage, candidates, malformed)


def test_explicit_no_direction_abstains_without_converse_inference():
    source = 'I do not support raising taxes.'
    candidates = validate_extraction(source, extracted(source[:-1]))
    output = assemble_prediction(source, candidates, choices('direction', candidates, 'NO_DIRECTION'),
                                 choices('speaker', candidates, 'NARRATOR'))
    assert output['spans'] == []
    # Structural validators cannot prove semantic negation correctness. An unsafe
    # model direction remains an error to count, never repaired into correctness.
    unsafe = assemble_prediction(source, candidates, choices('direction', candidates, 'RIGHT'),
                                 choices('speaker', candidates, 'NARRATOR'))
    metrics = evaluate_all([{'id': 'x', 'category': 'negation', 'text': source, 'expected': []}], {'x': unsafe}, [])
    assert metrics['primary_exact']['totals']['no_expected_span_false_highlights'] == 1


def test_unresolved_is_not_upgraded_to_narrator():
    candidates = validate_extraction(TEXT, extracted(QUOTE))
    out = assemble_prediction(TEXT, candidates, choices('direction', candidates, 'LEFT'),
                              choices('speaker', candidates, 'UNRESOLVED'))
    assert out['spans'][0]['attribution'] == 'unknown'


@pytest.mark.parametrize('mutation', ['fingerprint', 'prompt_tokens', 'completion_tokens', 'length',
    'tools', 'reasoning', 'duplicate_key', 'nan', 'choices'])
def test_strict_completion_rejects_identity_token_and_json_failures(mutation):
    output = completion(extracted())
    if mutation == 'fingerprint': output['system_fingerprint'] = 'other'
    if mutation == 'prompt_tokens': output['usage']['prompt_tokens'] = 699
    if mutation == 'completion_tokens': output['usage']['completion_tokens'] = 1025
    if mutation == 'length': output['choices'][0]['finish_reason'] = 'length'
    if mutation == 'tools': output['choices'][0]['message']['tool_calls'] = [{'name': 'test'}]
    if mutation == 'reasoning': output['choices'][0]['message']['reasoning_content'] = 'x'
    if mutation == 'duplicate_key': output['choices'][0]['message']['content'] = '{"c000":{},"c000":{}}'
    if mutation == 'nan': output['choices'][0]['message']['content'] = '{"x":NaN}'
    if mutation == 'choices': output['choices'] = []
    with pytest.raises(ValueError):
        validate_completion(output, 700, 4096, 1024, 'pinned')


@pytest.mark.parametrize('count', [True, 0, -1, 3057])
def test_invalid_or_overflow_preflight_stops_inference_and_counts_failure(count):
    runtime = FakeRuntime([], count=count)
    attempt, output = run_case(runtime, {'id': 'x', 'text': TEXT}, PROTOCOL)
    assert output is None and not runtime.bodies
    assert attempt['status'] == 'failed'
    assert attempt['stages']['extract']['status'] == 'failed'
    assert attempt['stages']['direction']['status'] == 'blocked_extraction_failure'
    assert attempt['stages']['speaker']['status'] == 'blocked_extraction_failure'


def test_empty_extraction_is_valid_explicit_negative_with_no_extra_calls():
    runtime = FakeRuntime([extracted()])
    attempt, output = run_case(runtime, {'id': 'x', 'text': ''}, PROTOCOL)
    assert attempt['status'] == 'validated' and output['spans'] == []
    assert len(runtime.bodies) == 1
    assert attempt['stages']['direction']['status'] == 'not_required_empty_candidates'
    assert attempt['stages']['speaker']['status'] == 'not_required_empty_candidates'


def test_direction_failure_still_records_speaker_and_invalidates_entire_case():
    candidates = validate_extraction(TEXT, extracted(QUOTE))
    runtime = FakeRuntime([extracted(QUOTE), {}, choices('speaker', candidates, 'NARRATOR')])
    attempt, output = run_case(runtime, {'id': 'x', 'text': TEXT}, PROTOCOL)
    assert len(runtime.bodies) == 3 and output is None
    assert attempt['stages']['direction']['status'] == 'failed'
    assert attempt['stages']['speaker']['status'] == 'validated'
    assert runtime.bodies == runtime.preflights


def test_speaker_failure_never_silently_returns_direction_only_result():
    candidates = validate_extraction(TEXT, extracted(QUOTE))
    runtime = FakeRuntime([extracted(QUOTE), choices('direction', candidates, 'LEFT'), ValueError('speaker failed')])
    attempt, output = run_case(runtime, {'id': 'x', 'text': TEXT}, PROTOCOL)
    assert output is None and len(runtime.bodies) == 3
    assert attempt['stages']['direction']['status'] == 'validated'
    assert attempt['stages']['speaker']['status'] == 'failed'


def test_all_candidates_receive_both_tasks_even_after_no_direction():
    candidates = validate_extraction(TEXT, extracted(QUOTE))
    runtime = FakeRuntime([extracted(QUOTE), choices('direction', candidates, 'NO_DIRECTION'),
                           choices('speaker', candidates, 'UNRESOLVED')])
    attempt, output = run_case(runtime, {'id': 'x', 'text': TEXT}, PROTOCOL)
    assert len(runtime.bodies) == 3 and output['spans'] == []
    assert [json.loads(b['messages'][1]['content'])['source'] for b in runtime.bodies] == [TEXT] * 3
    assert 'direction' not in json.loads(runtime.bodies[2]['messages'][1]['content'])
    assert attempt['stages']['speaker']['validated_response']['c000']['speaker'] == 'UNRESOLVED'


def test_coverage_fixed_denominators_and_secondary_axes_are_separate():
    rows = [{'id': 'positive', 'category': 'stance', 'text': TEXT, 'expected': [
        {'text': QUOTE, 'occurrence': 0, 'label': 'LEFT', 'attribution': 'author'}]},
        {'id': 'negative', 'category': 'negation', 'text': 'Unclear', 'expected': []}]
    candidate = validate_extraction(TEXT, extracted(QUOTE))
    wrong_speaker = assemble_prediction(TEXT, candidate, choices('direction', candidate, 'LEFT'),
                                       choices('speaker', candidate, 'UNRESOLVED'))
    metric = evaluate_all(rows, {'positive': wrong_speaker}, [])
    assert metric['primary_exact']['totals']['cases'] == 2
    assert metric['primary_exact']['totals']['covered_cases'] == 1
    assert metric['primary_exact']['totals']['expected_spans'] == 1
    assert metric['primary_exact']['totals']['exact_recovered_spans'] == 0
    assert metric['direction_only_secondary']['totals']['recovered_spans'] == 1
    assert metric['speaker_only_secondary']['totals']['recovered_spans'] == 0
    assert metric['primary_exact']['totals']['no_expected_span_cases'] == 1
    missing = evaluate_all(rows, {}, [])
    assert missing['primary_exact']['totals']['exact_cases'] == 0
    assert missing['primary_exact']['totals']['expected_positive_cases'] == 1
    assert missing['primary_exact']['totals']['covered_expected_positive_cases'] == 0


def test_code_and_protocol_hashes_change_with_meaningful_mutation():
    assert stable_hash({'a': 1, 'b': 2}) == stable_hash({'b': 2, 'a': 1})
    assert stable_hash(PROMPTS) != stable_hash({**PROMPTS, 'extract': 'changed'})


def test_new_pipeline_not_imported_in_serving():
    root = Path(__file__).resolve().parents[1]
    assert 'phrase_pipeline_v3' not in (root / 'backend/evidence.py').read_text()
    assert 'phrase_pipeline_v3' not in (root / 'backend/main.py').read_text()


def test_excess_candidates_preserve_raw_count_and_fail_whole_case():
    tokens = [f'word{i:02d}' for i in range(MAX_CANDIDATES + 1)]
    runtime = FakeRuntime([extracted(*tokens)])
    attempt, output = run_case(runtime, {'id': 'x', 'text': ' '.join(tokens)}, PROTOCOL)
    assert output is None and attempt['candidates'] == []
    assert attempt['stages']['extract']['raw_candidate_count'] == MAX_CANDIDATES + 1
    assert attempt['stages']['extract']['raw_response'] is not None
    assert attempt['stages']['speaker']['status'] == 'blocked_extraction_failure'
    assert len(runtime.bodies) == 1


def test_stage_failure_metrics_retain_fixed_expected_recall_denominator():
    candidates = validate_extraction(TEXT, extracted(QUOTE))
    runtime = FakeRuntime([extracted(QUOTE), choices('direction', candidates, 'LEFT'), {}])
    row = {'id': 'x', 'category': 'stance', 'text': TEXT, 'expected': [
        {'text': QUOTE, 'occurrence': 0, 'label': 'LEFT', 'attribution': 'author'}]}
    attempt, output = run_case(runtime, row, PROTOCOL)
    assert output is None
    metrics = evaluate_all([row], {}, [attempt])
    assert metrics['primary_exact']['totals']['covered_cases'] == 0
    assert metrics['primary_exact']['totals']['missed_spans'] == 1
    assert metrics['stage_accounting']['speaker']['status_counts'] == {'failed': 1}
    assert metrics['candidate_diagnostics']['all_expected_spans'] == 1
    assert metrics['candidate_diagnostics']['exact_expected_boundaries_extracted'] == 1
    assert metrics['candidate_diagnostics']['exact_expected_boundaries_with_correct_speaker'] == 0


@pytest.mark.parametrize('props', [None, [], {}, {'default_generation_settings': None},
    {'default_generation_settings': []},
    {'default_generation_settings': {'n_ctx': 4096}, 'total_slots': True, 'model_path': 'model.gguf', 'build_info': 'pinned'},
    {'default_generation_settings': {'n_ctx': 4096}, 'total_slots': 1, 'model_path': None, 'build_info': 'pinned'}])
def test_malformed_runtime_properties_fail_before_generation(props):
    from research.scripts.probe_phrase_pipeline_v3 import verify_runtime_props
    with pytest.raises(ValueError):
        verify_runtime_props(props, {**PROTOCOL, 'file': 'model.gguf'})


def test_expected_runtime_properties_pass():
    from research.scripts.probe_phrase_pipeline_v3 import verify_runtime_props
    verify_runtime_props({'default_generation_settings': {'n_ctx': 4096}, 'total_slots': 1,
                          'model_path': '/tmp/model.gguf', 'build_info': 'pinned'},
                         {**PROTOCOL, 'file': 'model.gguf'})


def test_publication_replays_canonical_json_and_distinguishes_sanitized_protocol(tmp_path):
    from research.scripts.probe_phrase_pipeline_v3 import publish, ROOT
    row = {'id': 'x', 'category': 'negative', 'text': '', 'expected': []}
    attempt, prediction = run_case(FakeRuntime([extracted()]), row, PROTOCOL)
    predictions = {'x': prediction}
    protocol = {'fixture_snapshots': {'original': {'rows': [row]}},
                'path_to_sanitize': str(ROOT.parent / 'runtime_cpu/models/model.gguf')}
    data = {'complete': True, 'protocol': protocol, 'protocol_sha256': stable_hash(protocol),
            'suites': {'original': {'complete': True, 'predictions': predictions, 'attempts': [attempt],
                      'metrics': evaluate_all([row], predictions, [attempt])}}}
    source, target = tmp_path / 'raw.json', tmp_path / 'public.json'
    source.write_text(json.dumps(data))
    result = publish(source, target)
    assert target.is_file()
    assert result['suites']['original']['metrics'] == json.loads(json.dumps(data['suites']['original']['metrics']))
    assert result['publication_note']['original_frozen_protocol_sha256'] == stable_hash(protocol)
    assert result['publication_note']['sanitized_public_protocol_sha256'] == stable_hash(result['protocol'])
    assert result['publication_note']['sanitized_public_protocol_sha256'] != stable_hash(protocol)
    assert str(ROOT.parent) not in target.read_text()
    assert json.loads(source.read_text()) == json.loads(json.dumps(data))
