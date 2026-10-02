"""Source-contract/probe tests are synthetic structural tests, not model accuracy."""
from copy import deepcopy
import json
import pytest

from backend.evidence import EvidenceValidationError, validate_prediction
from backend.phrase_contract_v2 import (
    PROMPT, aligned_occurrence, canonical_prediction, literal_starts,
    model_output_schema, recover_unique_quotes, validate_v2_batch, validate_v2_completion)
from research.scripts.probe_phrase_contract_v2 import boundary_metrics, payload_for, stable_hash

TEXT = '🐈 Café\r\nThe government must not privatize public healthcare.\r\nDone.'
QUOTE = 'The government must not privatize public healthcare'


def v2_span(text=QUOTE, context='', label='LEFT', attribution='author'):
    return dict(text=text, context=context, label=label, attribution=attribution, reason='Synthetic expectation')


def prediction(*spans):
    return {'spans': list(spans), 'reason': 'Synthetic test only'}


def envelope(pred=None):
    return {'predictions': [{'id': 'article', **(pred if pred is not None else prediction(v2_span()))}]}


def completion(pred=None):
    return {'system_fingerprint': 'pinned', 'usage': {'prompt_tokens': 700, 'completion_tokens': 90},
            'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(envelope(pred))}}]}


def test_alignment_preserves_entire_source_unicode_crlf_and_negation():
    result = canonical_prediction(TEXT, prediction(v2_span()))
    spans = validate_prediction(TEXT, result)
    assert spans[0]['text'] == QUOTE and 'must not' in spans[0]['text']
    assert TEXT[spans[0]['start']:spans[0]['end']] == QUOTE
    assert spans[0]['start'] == TEXT.index(QUOTE)
    assert result['spans'][0]['attribution'] == 'author'
    assert TEXT.startswith('🐈 Café\r\n')


def test_full_clause_shared_negation_is_preserved_without_splitting():
    text = 'We should not restrict voting or privatize schools.'
    chosen = text[:-1]
    result = canonical_prediction(text, prediction(v2_span(chosen)))
    assert result['spans'][0]['text'] == chosen


def test_structural_validation_cannot_certify_negation_scope():
    # Deliberately unsafe model choice remains structurally possible. Semantic
    # expected-span scoring must catch this; alignment does NOT claim to fix it.
    text = 'I do not believe taxing the rich is good.'
    result = canonical_prediction(text, prediction(v2_span('taxing the rich is good')))
    row = {'id': 'x', 'category': 'negation', 'text': text, 'expected': []}
    from research.scripts.probe_phrase_evidence import evaluate
    score = evaluate([row], {'x': result})['totals']
    assert score['false_highlights'] == 1 and score['exact_cases'] == 0


def test_unique_valid_optional_context_is_checked():
    assert aligned_occurrence(TEXT, QUOTE, QUOTE + '.') == 0
    with pytest.raises(ValueError):
        aligned_occurrence(TEXT, QUOTE, 'Invented context: ' + QUOTE)


def test_repeated_quote_attribution_is_bound_to_selected_occurrence():
    quote = 'taxing the rich is good'
    source = '"' + quote + '" said a guest. My view: ' + quote + '.'
    result = canonical_prediction(source, prediction(
        v2_span(quote, '"' + quote + '"', attribution='quoted'),
        v2_span(quote, 'My view: ' + quote, attribution='author')))
    assert [s['occurrence'] for s in result['spans']] == [0, 1]
    assert [s['attribution'] for s in result['spans']] == ['quoted', 'author']
    offsets = validate_prediction(source, result)
    assert offsets[1]['start'] == source.rindex(quote)
    assert [s['text'] for s in offsets] == [quote, quote]


@pytest.mark.parametrize('context', ['', 'x', 'x x', 'invented x', 'x x x'])
def test_ambiguous_or_fabricated_repeated_quote_fails_closed(context):
    with pytest.raises(ValueError):
        aligned_occurrence('x x x', 'x', context)


def test_overlapping_literal_occurrences_count_and_reject_ambiguity():
    assert literal_starts('aaaa', 'aa') == [0, 1, 2]
    with pytest.raises(ValueError):
        aligned_occurrence('aaaa', 'aa', 'aaa')


@pytest.mark.parametrize('mutation', ['normalization', 'crlf', 'punctuation', 'case'])
def test_no_fuzzy_or_cleaned_source_alignment(mutation):
    source = 'Café\r\nWe must not privatize hospitals.'
    chosen = source
    if mutation == 'normalization':
        chosen = chosen.replace('é', 'é')
    if mutation == 'crlf':
        chosen = chosen.replace('\r\n', '\n')
    if mutation == 'punctuation':
        chosen = chosen.replace('hospitals.', 'hospitals!')
    if mutation == 'case':
        chosen = chosen.lower()
    with pytest.raises(ValueError):
        canonical_prediction(source, prediction(v2_span(chosen)))


def test_no_attribution_or_label_repair():
    item = v2_span(label='RIGHT', attribution='unknown')
    result = canonical_prediction(TEXT, prediction(item))
    assert result['spans'][0]['label'] == 'RIGHT'
    assert result['spans'][0]['attribution'] == 'unknown'
    assert result['spans'][0]['reason'] == item['reason']


@pytest.mark.parametrize('spans', [
    [v2_span(), v2_span()],
    [v2_span(QUOTE), v2_span('must not privatize public healthcare')]])
def test_final_duplicate_or_overlapping_spans_fail(spans):
    with pytest.raises(ValueError):
        canonical_prediction(TEXT, prediction(*spans))


@pytest.mark.parametrize('key,value', [('context', None), ('text', ''), ('label', 'CENTER'),
                                      ('attribution', 'reporter'), ('reason', '')])
def test_invalid_span_fields(key, value):
    item = v2_span()
    item[key] = value
    with pytest.raises(ValueError):
        canonical_prediction(TEXT, prediction(item))


def test_extra_fields_and_model_offsets_rejected():
    for added in ('start', 'end', 'occurrence', 'confidence'):
        item = {**v2_span(), added: 0}
        with pytest.raises(ValueError):
            canonical_prediction(TEXT, prediction(item))


def test_empty_source_must_still_have_complete_identity():
    assert validate_v2_batch([{'id': 'article', 'text': ''}], envelope(prediction())) == {'article': prediction()}
    with pytest.raises(ValueError):
        validate_v2_batch([{'id': 'article', 'text': ''}], {'predictions': []})


def test_schema_has_no_occurrence_or_offsets():
    fields = model_output_schema()['properties']['predictions']['items']['properties']['spans']['items']['properties']
    assert set(fields) == {'text', 'label', 'attribution', 'context', 'reason'}


@pytest.mark.parametrize('mode', ['missing', 'duplicate', 'wrong', 'input_duplicate'])
def test_batch_identity_failures(mode):
    response = envelope()
    rows = [{'id': 'article', 'text': TEXT}]
    if mode == 'missing':
        response['predictions'] = []
    if mode == 'duplicate':
        response['predictions'] *= 2
    if mode == 'wrong':
        response['predictions'][0]['id'] = 'hinted_left_case'
    if mode == 'input_duplicate':
        rows *= 2
    with pytest.raises(ValueError):
        validate_v2_batch(rows, response)


def test_format_recovery_changes_only_unique_occurrence_and_does_not_mutate():
    original = {'spans': [{'text': QUOTE, 'occurrence': 11, 'label': 'RIGHT', 'attribution': 'unknown', 'reason': 'Model judgment unchanged'}], 'reason': 'Original model reason'}
    saved = deepcopy(original)
    restored, changes = recover_unique_quotes(TEXT, original)
    assert original == saved
    assert changes == [{'span_index': 0, 'old_occurrence': 11, 'new_occurrence': 0}]
    restored['spans'][0]['occurrence'] = 11
    assert restored == original


@pytest.mark.parametrize('occurrence', [-1, True, '1', 100000])
def test_format_recovery_does_not_accept_other_malformed_index(occurrence):
    item = {'text': QUOTE, 'occurrence': occurrence, 'label': 'LEFT', 'attribution': 'author', 'reason': 'test'}
    with pytest.raises(ValueError):
        recover_unique_quotes(TEXT, prediction(item))


def test_format_recovery_never_guesses_repeated_quote():
    item = {'text': 'yes', 'occurrence': 9, 'label': 'LEFT', 'attribution': 'unknown', 'reason': 'test'}
    with pytest.raises(ValueError):
        recover_unique_quotes('yes yes', prediction(item))


def test_valid_completion_gives_source_bound_canonical_output():
    result = validate_v2_completion(TEXT, completion(), 700, 4096, 1024, 'pinned')
    assert validate_prediction(TEXT, result)[0]['text'] == QUOTE


@pytest.mark.parametrize('mutation', ['fingerprint', 'input_tokens', 'input_bool', 'output_tokens', 'output_bool', 'truncated', 'tools', 'reasoning', 'duplicate_key', 'wrong_id'])
def test_completion_checks_identity_usage_finality_and_contract(mutation):
    output = completion()
    if mutation == 'fingerprint': output['system_fingerprint'] = 'other'
    if mutation == 'input_tokens': output['usage']['prompt_tokens'] = 701
    if mutation == 'input_bool': output['usage']['prompt_tokens'] = True
    if mutation == 'output_tokens': output['usage']['completion_tokens'] = 1025
    if mutation == 'output_bool': output['usage']['completion_tokens'] = True
    if mutation == 'truncated': output['choices'][0]['finish_reason'] = 'length'
    if mutation == 'tools': output['choices'][0]['message']['tool_calls'] = [{'anything': True}]
    if mutation == 'reasoning': output['choices'][0]['message']['reasoning_content'] = 'Unexpected'
    if mutation == 'duplicate_key': output['choices'][0]['message']['content'] = '{"predictions":[],"predictions":[]}'
    if mutation == 'wrong_id': output['choices'][0]['message']['content'] = json.dumps({'predictions': [{'id': 'LEFT_HINT', **prediction()}]})
    with pytest.raises(ValueError):
        validate_v2_completion(TEXT, output, 700, 4096, 1024, 'pinned')


def test_completion_rejects_reservation_overflow():
    with pytest.raises(ValueError):
        validate_v2_completion(TEXT, completion(), 3057, 4096, 1024, 'pinned')


def test_payload_uses_full_original_opaque_id_without_expectations():
    protocol = {'model': 'pinned', 'temperature': 0, 'seed': 20261002, 'output_token_limit': 1024,
                'prompt': PROMPT, 'schema': model_output_schema()}
    row = {'id': 'left_policy_leaking_id', 'text': TEXT, 'expected': ['SECRET_EXPECTATION']}
    body = payload_for(row, protocol)
    assert json.loads(body['messages'][1]['content']) == [{'id': 'article', 'text': TEXT}]
    assert 'SECRET_EXPECTATION' not in json.dumps(body) and 'left_policy_leaking_id' not in json.dumps(body)
    assert body['chat_template_kwargs'] == {'enable_thinking': False}
    assert body['seed'] == 20261002 and body['temperature'] == 0


def test_boundary_metrics_require_label_and_attribution_and_fixed_denominators():
    row = {'id': 'x', 'text': 'We support voting rights.', 'expected': [
        {'text': 'We support voting rights', 'occurrence': 0, 'label': 'LEFT', 'attribution': 'author'}]}
    span = {'text': row['text'], 'occurrence': 0, 'label': 'LEFT', 'attribution': 'author', 'reason': 'test'}
    total = boundary_metrics([row], {'x': prediction(span)})['totals']
    assert total['matched_spans'] == 1
    assert total['labeled_character_precision'] < 1
    for key, value in [('attribution', 'quoted'), ('label', 'RIGHT')]:
        wrong = {**span, key: value}
        assert boundary_metrics([row], {'x': prediction(wrong)})['totals']['matched_spans'] == 0
    missing = boundary_metrics([row], {})['totals']
    assert missing['cases'] == 1 and missing['expected_spans'] == 1 and missing['span_recall'] == 0


def test_overlap_matching_is_one_to_one():
    row = {'id': 'x', 'text': 'abcd', 'expected': [{'text': 'abcd', 'occurrence': 0, 'label': 'LEFT', 'attribution': 'author'}]}
    spans = [{'text': x, 'occurrence': 0, 'label': 'LEFT', 'attribution': 'author', 'reason': 'test'} for x in ('ab', 'cd')]
    total = boundary_metrics([row], {'x': prediction(*spans)})['totals']
    assert total['matched_spans'] == 1 and total['span_precision'] == 0.5


def test_frozen_hash_sensitive_to_every_protocol_change():
    assert stable_hash({'prompt': 'a', 'seed': 0}) == stable_hash({'seed': 0, 'prompt': 'a'})
    assert stable_hash({'prompt': 'a'}) != stable_hash({'prompt': 'b'})
