"""Diagnostics classify failures without placing source/model text in logs."""
import json
from unittest.mock import Mock, patch
import pytest
import requests
from fastapi.testclient import TestClient
from backend.main import app, _inference_lock
from backend.unbias import client

SECRET = 'PRIVATE_SOURCE_AND_COMPLETION'


def envelope(content='null'):
    return {'model': 'unbias-plus-v2', 'system_fingerprint': client.FINGERPRINT,
            'usage': {'prompt_tokens': 100},
            'choices': [{'finish_reason': 'stop', 'message': {'content': content}}]}


@pytest.fixture(autouse=True)
def enabled(monkeypatch):
    monkeypatch.setenv('BIASCHECK_UNBIAS_ENABLED', '1')
    monkeypatch.delenv('BIASCHECK_UNBIAS_ENDPOINT', raising=False)


@pytest.mark.parametrize('value,stage,code', [
    (envelope(SECRET), 'native_json', 'invalid_native_json'),
    (envelope('{"severity":0,"severity":1}'), 'native_json', 'duplicate_json_key'),
    (envelope('{"severity":NaN}'), 'native_json', 'nonfinite_json_value'),
    (envelope(), 'native_schema', 'invalid_native_schema'),
    (envelope(json.dumps({'severity': 1, 'biased_segments': [], 'unbiased_text': SECRET})),
     'native_schema', 'inconsistent_severity'),
    ({**envelope(), 'model': SECRET}, 'metadata', 'model_alias_mismatch'),
    ({**envelope(), 'usage': {'prompt_tokens': 99}}, 'metadata', 'prompt_preflight_mismatch'),
    ({**envelope(), 'choices': []}, 'metadata', 'incomplete_response'),
    ([], 'metadata', 'invalid_metadata'),
])
def test_diagnostic_stage_and_safe_api_logging(value, stage, code, caplog):
    with patch.object(client, '_post', side_effect=[{'input_tokens': 100}, value]):
        with pytest.raises(client.FramingUnavailable) as caught:
            client.analyze(SECRET)
    error = caught.value
    assert (error.stage, error.code) == (stage, code)
    assert error.__cause__ is not None
    assert SECRET not in str(error)
    with patch.object(client, '_post', side_effect=[{'input_tokens': 100}, value]):
        result = TestClient(app).post('/framing', json={'text': SECRET})
    assert result.status_code == 503
    assert result.json() == {'detail': 'Experimental framing is temporarily unavailable.'}
    assert SECRET not in caplog.text
    assert f'{stage}:{code}' in caplog.text
    assert not _inference_lock.locked()


@pytest.mark.parametrize('exc,code', [(requests.Timeout(SECRET), 'model_timeout'),
                                      (requests.ConnectionError(SECRET), 'model_transport_error')])
def test_transport_preserves_cause_without_text(exc, code):
    session = Mock()
    session.post.side_effect = exc
    with pytest.raises(client.FramingUnavailable) as caught:
        client._post(session, 'http://127.0.0.1:8082', '/v1/chat/completions', {})
    assert caught.value.__cause__ is exc
    assert (caught.value.stage, caught.value.code) == ('transport', code)
    assert SECRET not in str(caught.value)


@pytest.mark.parametrize('raw,code', [(SECRET.encode(), 'invalid_outer_json'),
                                     (b'\xff', 'invalid_outer_json'),
                                     (b'{"x":1,"x":2}', 'duplicate_json_key')])
def test_outer_json_is_distinct(raw, code):
    session = Mock()
    response = Mock(status_code=200)
    response.iter_content.return_value = [raw]
    session.post.return_value.__enter__ = Mock(return_value=response)
    session.post.return_value.__exit__ = Mock(return_value=False)
    with pytest.raises(client.FramingUnavailable) as caught:
        client._post(session, 'http://127.0.0.1:8082', '/v1/chat/completions', {})
    assert (caught.value.stage, caught.value.code) == ('outer_json', code)
    assert caught.value.__cause__ is not None
    assert SECRET not in str(caught.value)


@pytest.mark.parametrize('endpoint', ['http://[::1', 'http://127.0.0.1:bad',
                                      'http://127.0.0.1:99999'])
def test_malformed_endpoint_is_safe_503(monkeypatch, endpoint, caplog):
    monkeypatch.setenv('BIASCHECK_UNBIAS_ENDPOINT', endpoint)
    with patch.object(client, '_post') as post:
        result = TestClient(app).post('/framing', json={'text': SECRET})
    assert result.status_code == 503
    post.assert_not_called()
    assert 'configuration:invalid_local_endpoint' in caplog.text
    assert not _inference_lock.locked()


def test_explicit_research_capture_survives_native_parse_failure():
    capture = {}
    value = envelope(SECRET)
    with patch.object(client, '_post', side_effect=[{'input_tokens': 100}, value]):
        with pytest.raises(client.FramingUnavailable):
            client.analyze(SECRET, diagnostics=capture)
    assert capture['output'] is value
    assert capture['preflight'] == {'input_tokens': 100}
    assert SECRET in capture['payload']['messages'][1]['content']


def test_unknown_error_details_cannot_escape_safe_summary():
    error = client.FramingUnavailable(SECRET, SECRET)
    assert str(error) == 'unknown:invalid_or_unavailable_model_response'
