"""AI-authored integrity fixtures, not natural-news or semantic accuracy tests."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

import pytest

from backend.unbias.refinement import (
    MAX_CANDIDATES, MAX_REASON_CHARS, build_refinement_messages,
    build_refinement_request, validate_refinement, validate_model_refinement,
)


TEXT = '🦋 The witness said the policy was not a reckless gamble. Context remains.'


def candidate(text=TEXT, phrase='not a reckless gamble', index=3, bias_type='loaded_language'):
    start = text.index(phrase)
    return dict(native_index=index, start=start, end=start + len(phrase), text=phrase,
                bias_type=bias_type, reason='Native diagnostic rationale.', attribution='unknown')


def decision(action='keep', original='not a reckless gamble', index=3, **extra):
    return dict(native_index=index, action=action, original=original,
                reason='Synthetic scope-preservation fixture.',
                bias_type=None if action == 'drop' else 'loaded_language', **extra)


def validate(decisions, candidates=None, text=TEXT):
    return validate_refinement(text, [candidate()] if candidates is None else candidates,
                               {'decisions': decisions})


def test_full_source_request_and_inputs_unchanged():
    spans = [candidate()]
    snapshot = copy.deepcopy(spans)
    messages = build_refinement_messages(TEXT, spans)
    assert json.loads(messages[1]['content'])['source'] == TEXT
    assert 'negation' in messages[0]['content']
    request = build_refinement_request(TEXT, spans)
    assert request['response_format']['json_schema']['schema']['additionalProperties'] is False
    result = validate([decision()], spans)
    assert spans == snapshot
    span = result['spans'][0]
    assert TEXT[span['start']:span['end']] == 'not a reckless gamble'
    assert span['attribution'] == 'unknown'
    assert result['release_approved'] is False
    assert 'status' not in result  # Caller must preserve detector failures.


def test_narrow_resolves_repeated_source_phrase_within_parent_and_retypes():
    text = 'A wild claim. Another wild claim.'
    parent = candidate(text, 'Another wild claim', bias_type='informational_bias')
    result = validate([decision('narrow', 'wild claim')], [parent], text)
    span = result['spans'][0]
    assert span['start'] == text.rindex('wild claim')
    assert span['bias_type'] == 'loaded_language'
    assert span['native_bias_type'] == 'informational_bias'
    assert span['native_index'] == 3


def test_drop_explicit_and_empty_candidate_batch():
    result = validate([decision('drop', '')])
    assert result['spans'] == [] and result['dropped_native_indices'] == [3]
    assert validate([], [])['decisions'] == []


@pytest.mark.parametrize('change', [
    {'native_index': True}, {'native_index': 99}, {'action': 'split'},
    {'original': 'reckless gamble'}, {'reason': ''}, {'reason': 'x' * (MAX_REASON_CHARS + 1)},
    {'bias_type': 'informational_bias'}, {'bias_type': None}, {'unexpected': 'field'},
    {'attribution_judgment': {'kind': 'author', 'evidence': 'Context remains.'}},
])
def test_invalid_decisions_fail_batch(change):
    value = decision()
    value.update(change)
    with pytest.raises(ValueError):
        validate([value])


@pytest.mark.parametrize('action,original', [
    ('narrow', 'not a reckless gamble'), ('narrow', ''), ('narrow', 'Context remains.'),
    ('narrow', 'not reckless'), ('drop', 'not a reckless gamble'),
])
def test_invalid_selection(action, original):
    with pytest.raises(ValueError):
        validate([decision(action, original)])


def test_ambiguous_parent_substring_rejected():
    text = 'wild and wild'
    with pytest.raises(ValueError, match='ambiguous_occurrence'):
        validate([decision('narrow', 'wild')], [candidate(text, text)], text)


def test_missing_extra_duplicate_ids_rejected():
    second = candidate(TEXT, 'Context remains.', index=8)
    with pytest.raises(ValueError, match='count'):
        validate([])
    with pytest.raises(ValueError, match='count'):
        validate([decision(), decision()])
    with pytest.raises(ValueError, match='index'):
        validate([decision(), decision()], [candidate(), second])


def test_candidate_source_and_overlap_validation():
    for update in [{'start': True}, {'end': len(TEXT) + 1}, {'text': 'fabricated'},
                   {'native_index': True}]:
        bad = candidate()
        bad.update(update)
        with pytest.raises(ValueError):
            build_refinement_messages(TEXT, [bad])
    with pytest.raises(ValueError, match='overlapping'):
        build_refinement_messages(TEXT, [candidate(), candidate(index=4)])


def test_candidate_cap_fails_without_truncation():
    with pytest.raises(ValueError, match='candidates'):
        build_refinement_messages(TEXT, [candidate(index=i) for i in range(MAX_CANDIDATES + 1)])


def test_schema_and_request_are_not_mutated_across_calls():
    request = build_refinement_request(TEXT, [candidate()])
    request['response_format']['json_schema']['schema']['properties'].clear()
    assert build_refinement_request(TEXT, [candidate()])['response_format']['json_schema']['schema']['properties']


def test_validator_does_not_claim_semantic_negation_check():
    # Exact containment cannot prove semantic fidelity. Deliberately demonstrate
    # this limit rather than disguising a keyword rule as a semantic guarantee.
    result = validate([decision('narrow', 'reckless gamble')])
    assert result['spans'][0]['text'] == 'reckless gamble'
    assert result['experimental'] and not result['release_approved']


def test_whitespace_only_candidates_and_retained_originals_rejected():
    text = 'First\t \nSecond'
    with pytest.raises(ValueError, match='invalid_candidate'):
        build_refinement_messages(text, [candidate(text, '\t \n')])
    parent = candidate(text, text)
    with pytest.raises(ValueError, match='blank_retained_original'):
        validate([decision('narrow', '\t \n')], [parent], text)


@pytest.mark.parametrize('original,bias_type,action', [
    ('not a reckless gamble', 'loaded_language', 'keep'),
    ('reckless gamble', 'loaded_language', 'narrow'),
    ('', None, 'drop'),
])
def test_model_contract_derives_actions(original, bias_type, action):
    generated = {'native_index': 3, 'original': original, 'bias_type': bias_type,
                 'reason': 'AI-authored integrity fixture, not semantic validation.'}
    before = copy.deepcopy(generated)
    result = validate_model_refinement(TEXT, [candidate()], {'decisions': [generated]})
    assert generated == before
    assert result['decisions'][0]['action'] == action
    assert bool(result['spans']) == (action != 'drop')


@pytest.mark.parametrize('change', [
    {'action': 'drop'}, {'action': 'keep'}, {'original': '', 'bias_type': 'loaded_language'},
    {'bias_type': None}, {'bias_type': 'informational_bias'}, {'original': None},
    {'original': 'Context remains.'}, {'original': ' '}, {'native_index': True},
    {'reason': ''}, {'reason': 'x' * (MAX_REASON_CHARS + 1)},
])
def test_model_contract_rejects_extra_action_and_invalid_choices(change):
    generated = {'native_index': 3, 'original': 'not a reckless gamble',
                 'bias_type': 'loaded_language', 'reason': 'AI-authored fixture.'}
    generated.update(change)
    with pytest.raises(ValueError):
        validate_model_refinement(TEXT, [candidate()], {'decisions': [generated]})


def test_model_contract_requires_all_fields_and_unique_complete_decisions():
    generated = {'native_index': 3, 'original': '', 'bias_type': None, 'reason': 'No cue.'}
    for key in generated:
        invalid = {k: v for k, v in generated.items() if k != key}
        with pytest.raises(ValueError):
            validate_model_refinement(TEXT, [candidate()], {'decisions': [invalid]})
    with pytest.raises(ValueError, match='count'):
        validate_model_refinement(TEXT, [candidate()], {'decisions': []})
    second = candidate(TEXT, 'Context remains.', index=8)
    with pytest.raises(ValueError, match='index'):
        validate_model_refinement(TEXT, [candidate(), second], {'decisions': [generated, generated]})


def test_generated_schema_excludes_action_and_couples_empty_text_to_null_type():
    schema = build_refinement_request(TEXT, [candidate()])['response_format']['json_schema']['schema']
    item = schema['properties']['decisions']['items']
    assert set(item) == {'oneOf'}
    for branch in item['oneOf']:
        assert branch['type'] == 'object'
        assert set(branch['required']) == {'native_index', 'original', 'reason', 'bias_type'}
        assert set(branch['properties']) == set(branch['required'])
        assert branch['additionalProperties'] is False
    empty, retained = item['oneOf']
    assert empty['properties']['original']['maxLength'] == 0
    assert empty['properties']['bias_type']['type'] == 'null'
    assert retained['properties']['original']['minLength'] == 1
    assert None not in retained['properties']['bias_type']['enum']


def test_pinned_runtime_grammar_requires_all_fields(tmp_path):
    """Compile a tiny converter probe against the existing runtime, without a model.

    This environment-specific regression skips when pinned research artifacts or
    a compiler are unavailable; other tests do not establish grammar compatibility.
    """
    root = Path(__file__).resolve().parents[1]
    archive = Path('/tmp/llama-b11349-conversion-source/source.tar.gz')
    runtime = root / 'research/checkpoints/unbias-runtime/bin/llama-b11349'
    compiler = shutil.which('c++')
    if not archive.is_file() or not (runtime / 'libllama-common.so').is_file() or not compiler:
        pytest.skip('Pinned runtime, source archive, and C++ compiler required for grammar regression')
    prefix = 'llama.cpp-fb4b2737a808a3fb7c2117a498f43815dc9be53e/common/'
    with tarfile.open(archive) as source:
        for name in ('json.h', 'json-schema.h', 'json-schema-to-grammar.h'):
            (tmp_path / name).write_bytes(source.extractfile(prefix + name).read())
    probe = tmp_path / 'probe.cpp'
    probe.write_text('''#include "json-schema-to-grammar.h"
#include <iostream>
#include <iterator>
int main() {
    std::string input((std::istreambuf_iterator<char>(std::cin)), std::istreambuf_iterator<char>());
    std::cout << json_schema_to_grammar(common_json::parse(input), true);
}
''')
    binary = tmp_path / 'probe'
    subprocess.run([compiler, '-std=c++17', str(probe), '-I' + str(tmp_path),
                    '-L' + str(runtime), '-Wl,-rpath,' + str(runtime), '-lllama-common',
                    '-o', str(binary)], check=True, capture_output=True, text=True)
    schema = build_refinement_request(TEXT, [candidate()])['response_format']['json_schema']['schema']
    grammar = subprocess.run([str(binary)], input=json.dumps(schema), check=True,
                             capture_output=True, text=True).stdout
    rules = dict(line.split(' ::= ', 1) for line in grammar.splitlines())
    for index in (0, 1):
        name = f'decisions-item-{index}'
        # Exact production comparison proves required fields are in sequence,
        # with no optional branches around them. A mere key-presence check would
        # not prove requiredness.
        assert rules[name] == (
            '"{" space ' + name + '-native-index-kv "," space ' + name
            + '-reason-kv "," space ' + name + '-original-kv "," space '
            + name + '-bias-type-kv space "}"')
