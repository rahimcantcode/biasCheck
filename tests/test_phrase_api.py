"""API contract tests with explicitly synthetic evidence and classifier stubs."""
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.evidence import text_sha256
from backend.utils import resolve_input


def fake_prediction(text,mode='article'):
    return dict(label=None,label_id=None,raw_label='LEFT',probabilities={'LEFT':.99,'RIGHT':.005,'CENTER':.005},
                decision='abstained',reason='model_not_validated',token_count=20,tokens_processed=20,
                chunk_count=1,truncated=False,calibrated=False)


def test_exact_plain_text_is_not_cleaned_before_offsets():
    text='  🐈 Cafe\u0301\r\n\tmy cat is pretty and taxing the rich is good  '
    assert resolve_input(text)==('text',text)
    assert resolve_input('\r\n\t ')==('text','')


def test_verified_phrase_output_is_independent_from_withheld_overall():
    text='  🐈 my cat is pretty and taxing the rich is good\r\n\t'
    phrase='taxing the rich is good';start=text.index(phrase)
    evidence=dict(status='available',offset_unit='unicode_code_point',source_text_sha256=text_sha256(text),
                  evidence_source='experimental_phrase_classifier',calibrated=False,release_approved=False,
                  spans=[dict(start=start,end=start+len(phrase),text=phrase,label='LEFT',
                              attribution='author',status='experimental',rationale='Synthetic integration fixture')])
    with patch('backend.main.predict_text',side_effect=fake_prediction),patch('backend.main.model_metadata',return_value={}),\
            patch('backend.main.extract_phrase_evidence',return_value=evidence) as extractor:
        response=TestClient(app).post('/predict',json={'input':text,'mode':'article'})
    assert response.status_code==200
    body=response.json()
    assert body['resolved_text']==text and body['overall']['label'] is None
    assert body['evidence_spans'][0]['text']==phrase
    assert body['evidence_status']=='available'
    assert body['evidence_metadata']['offset_unit']=='unicode_code_point'
    extractor.assert_called_once_with(text)
    assert any('separately generated' in warning for warning in body['warnings'])


def test_default_disabled_provider_never_inherits_article_prediction(monkeypatch):
    monkeypatch.delenv('PHRASE_EVIDENCE_CACHE',raising=False)
    monkeypatch.delenv('PHRASE_EVIDENCE_PROVIDER',raising=False)
    with patch('backend.main.predict_text',side_effect=fake_prediction),patch('backend.main.model_metadata',return_value={}):
        body=TestClient(app).post('/predict',json={'input':'my cat is pretty and taxing the rich is good'}).json()
    assert body['evidence_spans']==[] and body['evidence_status']=='unavailable'
