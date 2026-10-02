"""Strict model JSON decoding: reject ambiguity and non-JSON numeric literals."""
import json


def strict_json_loads(content):
    if not isinstance(content,str):
        raise ValueError('Expected JSON text')
    def unique_object(pairs):
        value={}
        for key,item in pairs:
            if key in value:raise ValueError(f'Duplicate JSON key: {key}')
            value[key]=item
        return value
    def invalid_constant(value):
        raise ValueError(f'Nonfinite JSON literal: {value}')
    return json.loads(content,object_pairs_hook=unique_object,parse_constant=invalid_constant)
