"""Grammar is an explicit generation variant, not permissive output repair."""
from unittest.mock import patch
import pytest
from backend.unbias import client
from backend.unbias.native_schema import response_format


@pytest.mark.parametrize('flag,expected', [('0', False), ('1', True), ('true', False)])
def test_generation_variant_is_explicit(monkeypatch, flag, expected):
    monkeypatch.setenv('BIASCHECK_UNBIAS_ENABLED', '1')
    monkeypatch.setenv('BIASCHECK_UNBIAS_STRUCTURED', flag)
    native = {'severity': 0, 'biased_segments': [], 'unbiased_text': 'A hearing occurred.'}
    import json
    output = {'model': 'unbias-plus-v2', 'system_fingerprint': client.FINGERPRINT,
              'usage': {'prompt_tokens': 100},
              'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(native)}}]}
    with patch.object(client, '_post', side_effect=[{'input_tokens': 100}, output]) as post:
        result = client.analyze('A hearing occurred.')
    payload = post.call_args_list[1].args[3]
    assert ('response_format' in payload) is expected
    if expected:
        assert payload['response_format'] == response_format()
    assert result['model']['structured_output'] is expected
    assert result['release_approved'] is False
