"""Opt-in decoding grammar for the existing UnBias native output contract.

This schema controls JSON syntax and basic field shapes only. The adapter
remains responsible for severity consistency, exact source spans, and overlap
rejection. Constrained decoding is not evidence of semantic correctness.
"""
from copy import deepcopy

from .adapter import BIAS_TYPES

NATIVE_SCHEMA = {
    'type': 'object',
    'properties': {
        'severity': {'type': 'integer', 'minimum': 0, 'maximum': 10},
        'biased_segments': {
            'type': 'array',
            'maxItems': 64,
            'items': {
                'type': 'object',
                'properties': {
                    'original': {'type': 'string', 'minLength': 1},
                    'replacement': {'type': 'string'},
                    'severity': {'type': 'string', 'enum': ['Low', 'Medium', 'High']},
                    'bias_type': {'type': 'string', 'enum': sorted(BIAS_TYPES)},
                    'reasoning': {'type': 'string'},
                },
                'required': ['original', 'replacement', 'severity', 'bias_type', 'reasoning'],
                'additionalProperties': False,
            },
        },
        'unbiased_text': {'type': 'string'},
    },
    'required': ['severity', 'biased_segments', 'unbiased_text'],
    'additionalProperties': False,
}


def response_format():
    """Return a fresh OpenAI-compatible structured-output request value."""
    return {
        'type': 'json_schema',
        'json_schema': {
            'name': 'unbias_native_v2',
            'strict': True,
            'schema': deepcopy(NATIVE_SCHEMA),
        },
    }
