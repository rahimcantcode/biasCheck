"""Synthetic transport/API tests, not model accuracy tests."""
import json
from unittest.mock import patch
import pytest
import requests
from fastapi.testclient import TestClient
from backend.main import app, _inference_lock
from backend.unbias import client
TEXT='🦋 They called it "a reckless disaster".'

def native():
    return dict(severity=5,unbiased_text='unused',biased_segments=[dict(original='a reckless disaster',replacement='a policy',severity='Medium',bias_type='loaded_language',reasoning='Synthetic fixture')])

def response(value=None):
    return dict(model='unbias-plus-v2',system_fingerprint=client.FINGERPRINT,usage={'prompt_tokens':100},choices=[dict(finish_reason='stop',message={'content':json.dumps(native() if value is None else value)})])

@pytest.fixture(autouse=True)
def enabled(monkeypatch):
    monkeypatch.setenv('BIASCHECK_UNBIAS_ENABLED','1')
    monkeypatch.delenv('BIASCHECK_UNBIAS_ENDPOINT',raising=False)

def test_disabled_has_no_transport(monkeypatch):
    monkeypatch.delenv('BIASCHECK_UNBIAS_ENABLED')
    with patch.object(client,'_post') as post:
        assert TestClient(app).post('/framing',json={'text':TEXT}).status_code==404
        post.assert_not_called()

def test_exact_original_unknown_attribution():
    with patch.object(client,'_post',side_effect=[{'input_tokens':100},response()]):
        r=TestClient(app).post('/framing',json={'text':TEXT})
    assert r.status_code==200
    body=r.json();span=body['spans'][0]
    assert body['resolved_text']==TEXT and TEXT[span['start']:span['end']]==span['text']
    assert span['attribution']=='unknown' and 'label' not in span
    assert body['release_approved'] is False

def test_context_overflow_does_not_generate():
    with patch.object(client,'_post',return_value={'input_tokens':8000}) as post:
        assert TestClient(app).post('/framing',json={'text':TEXT}).status_code==413
        assert post.call_count==1

@pytest.mark.parametrize('mutate',[
    lambda r:r.update(system_fingerprint='wrong'),lambda r:r.update(model='wrong'),
    lambda r:r['usage'].update(prompt_tokens=99),lambda r:r['choices'][0].update(finish_reason='length'),
    lambda r:r['choices'][0]['message'].update(reasoning_content='unexpected'),
    lambda r:r['choices'][0]['message'].update(content='{"severity":0,"severity":1}'),
    lambda r:r['choices'][0]['message'].update(content='null')])
def test_invalid_fails_closed(mutate):
    value=response();mutate(value)
    with patch.object(client,'_post',side_effect=[{'input_tokens':100},value]):
        assert TestClient(app).post('/framing',json={'text':TEXT}).status_code==503
    assert not _inference_lock.locked()

def test_rejection_is_partial_failure():
    value=native();value['biased_segments'][0]['original']='absent text'
    with patch.object(client,'_post',side_effect=[{'input_tokens':100},response(value)]):
        body=TestClient(app).post('/framing',json={'text':TEXT}).json()
    assert body['status']=='partial_failure' and not body['spans'] and body['rejected']

def test_empty_success():
    with patch.object(client,'_post',side_effect=[{'input_tokens':100},response(dict(severity=0,biased_segments=[],unbiased_text=TEXT))]):
        assert TestClient(app).post('/framing',json={'text':TEXT}).json()['status']=='no_suggestions'

@pytest.mark.parametrize('endpoint',['https://example.com','http://127.0.0.1@evil.example','http://127.0.0.1/path','http://localhost:8082'])
def test_endpoint_rejected(monkeypatch,endpoint):
    monkeypatch.setenv('BIASCHECK_UNBIAS_ENDPOINT',endpoint)
    with patch.object(client,'_post') as post:
        assert TestClient(app).post('/framing',json={'text':TEXT}).status_code==503
        post.assert_not_called()

def test_timeout():
    with patch.object(client,'_post',side_effect=requests.Timeout):
        assert TestClient(app).post('/framing',json={'text':TEXT}).status_code==503

def test_busy():
    _inference_lock.acquire()
    try:
        with patch.object(client,'_post') as post:
            assert TestClient(app).post('/framing',json={'text':TEXT}).status_code==503
            post.assert_not_called()
    finally:_inference_lock.release()

def test_blank():
    assert TestClient(app).post('/framing',json={'text':'  \n'}).status_code==400

def test_vendored_code_matches_research():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    for source,target in [('adapter.py','adapter.py'),('upstream_prompt.py','prompt.py')]:
        assert (root/'research/experiments/unbias_20261003'/source).read_bytes()==(root/'backend/unbias'/target).read_bytes()
