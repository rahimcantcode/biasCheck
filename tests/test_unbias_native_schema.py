"""Grammar contract tests; runtime support and model quality need separate runs."""
import json
from itertools import product

import pytest

from backend.unbias.adapter import BIAS_TYPES, adapt_unbias_v2
from backend.unbias.native_schema import NATIVE_SCHEMA, response_format


def native(bias_type='loaded_language', severity='Medium'):
    return {'severity': 5, 'biased_segments': [{
        'original': 'reckless', 'replacement': '', 'severity': severity,
        'bias_type': bias_type, 'reasoning': 'Charged adjective.'}],
        'unbiased_text': 'The policy.'}


def test_exact_fields_types_and_bounds_match_native_adapter():
    schema = NATIVE_SCHEMA
    fixture = native()
    assert schema['type'] == 'object'
    assert schema['additionalProperties'] is False
    assert set(schema['properties']) == set(schema['required']) == set(fixture)
    assert schema['properties']['severity'] == {'type': 'integer', 'minimum': 0, 'maximum': 10}
    segments = schema['properties']['biased_segments']
    assert segments['type'] == 'array' and segments['maxItems'] == 64
    segment = segments['items']
    assert segment['type'] == 'object' and segment['additionalProperties'] is False
    assert set(segment['properties']) == set(segment['required']) == set(fixture['biased_segments'][0])
    assert segment['properties']['original'] == {'type': 'string', 'minLength': 1}
    assert segment['properties']['replacement'] == {'type': 'string'}
    assert segment['properties']['reasoning'] == {'type': 'string'}
    assert schema['properties']['unbiased_text'] == {'type': 'string'}
    assert set(segment['properties']['bias_type']['enum']) == BIAS_TYPES
    assert set(segment['properties']['severity']['enum']) == {'Low', 'Medium', 'High'}


@pytest.mark.parametrize('bias_type,severity', list(product(sorted(BIAS_TYPES), ['Low', 'Medium', 'High'])))
def test_every_grammar_label_is_accepted_by_adapter(bias_type, severity):
    result = adapt_unbias_v2('The reckless policy.', native(bias_type, severity))
    assert result['status'] == 'suggestions'
    assert result['spans'][0]['text'] == 'reckless'
    assert result['spans'][0]['bias_type'] == bias_type


def test_grammar_does_not_replace_semantic_validation():
    value = native()
    value['severity'] = 0  # In the numeric grammar range, but semantically inconsistent.
    with pytest.raises(ValueError, match='inconsistent_severity'):
        adapt_unbias_v2('The reckless policy.', value)
    value['severity'] = 5
    value['biased_segments'][0]['original'] = 'invented phrase'
    result = adapt_unbias_v2('The reckless policy.', value)
    assert result['status'] == 'partial_failure'
    assert result['rejected'] == [{'native_index': 0, 'reason': 'unmatched_phrase'}]


def test_response_format_is_serializable_and_mutation_isolated():
    first = response_format()
    assert first['type'] == 'json_schema'
    assert first['json_schema']['strict'] is True
    assert first['json_schema']['schema'] == NATIVE_SCHEMA
    assert json.loads(json.dumps(first)) == first
    first['json_schema']['schema']['properties']['biased_segments']['items']['properties']['bias_type']['enum'].clear()
    second = response_format()
    assert set(second['json_schema']['schema']['properties']['biased_segments']['items']['properties']['bias_type']['enum']) == BIAS_TYPES
