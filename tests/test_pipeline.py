import socket
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from backend.utils import segment_spans, extract_article_html, validate_public_url
from backend.model import token_windows, classify_scores, validate_policy
from backend.main import app


def test_sentence_offsets_and_abbreviations():
    text='Dr. Smith supports the U.S. Government. He explained why.\n\nHe explained why.'
    spans=segment_spans(text,'sentence')
    assert [text[a:b] for a,b in spans]==['Dr. Smith supports the U.S. Government.','He explained why.','He explained why.']
    assert all(b<=c for (_,b),(c,_) in zip(spans,spans[1:]))


def test_nested_article_not_duplicated():
    first='The city council met on Tuesday to discuss the proposed annual budget and its impact on local public services.'
    second='Members heard testimony from residents before scheduling a public vote on the proposal for the following month.'
    html=f'<nav>subscribe</nav><article><p>{first}</p><p>{second}</p></article><aside>unrelated</aside>'
    assert extract_article_html(html)==first+'\n\n'+second


def test_unreadable_html_fails():
    with pytest.raises(ValueError): extract_article_html('<html><script>foo</script>Subscribe now</html>')


@pytest.mark.parametrize('length',[1,509,510,511,956,957,1400])
def test_window_coverage(length):
    ids=list(range(length));windows=list(token_windows(ids))
    assert sum(w for _,_,_,w in windows)==length
    assert set(x for window,_,_,_ in windows for x in window)==set(ids)
    assert all(len(window)<=510 for window,_,_,_ in windows)
    assert windows[-1][2]==length


def test_high_score_is_not_validated_label():
    scores,reason=classify_scores([10,0,0],15,'article',None)
    assert scores[0]>.99
    assert reason=='model_not_validated'


def test_demo_mode_exposes_clear_estimate_without_approving_release(monkeypatch):
    monkeypatch.setenv('BIASCHECK_DEMO_MODE', '1')
    scores, reason=classify_scores([10,0,0],15,'article',None)
    assert scores[0] > .99
    assert reason == 'demo_estimate'


def test_demo_mode_still_withholds_short_context(monkeypatch):
    monkeypatch.setenv('BIASCHECK_DEMO_MODE', '1')
    _, reason=classify_scores([10,0,0],3,'article',None)
    assert reason == 'insufficient_context'


def test_context_and_mode_are_not_center():
    p={'release_approved':True,'temperature':1.,'min_tokens':30,'min_confidence':.7,'min_margin':.2,'validated_modes':['article']}
    assert classify_scores([0,9,0],10,'article',p)[1]=='insufficient_context'
    assert classify_scores([0,9,0],100,'sentence',p)[1]=='mode_not_validated'
    assert classify_scores([0,0,0],100,'article',p)[1]=='uncertain'
    assert classify_scores([0,9,0],100,'article',p)[1] is None


def test_private_url_rejected():
    with patch('socket.getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',80))]):
        with pytest.raises(ValueError): validate_public_url('http://example.com/article')


def fake_prediction(text,mode='article'):
    return dict(label=None,label_id=None,raw_label='LEFT',probabilities={'LEFT':.99,'RIGHT':.005,'CENTER':.005},decision='abstained',reason='model_not_validated',token_count=10,tokens_processed=10,chunk_count=1,truncated=False,calibrated=False)


def test_independent_overall_and_mode():
    text='Dr. Smith attended the meeting. The vote began later.'
    with patch('backend.main.predict_text',side_effect=fake_prediction) as predictor,patch('backend.main.model_metadata',return_value={}):
        r=TestClient(app).post('/predict',json={'input':text,'mode':'sentence'})
        assert r.status_code==200
        body=r.json();assert body['mode']=='sentence' and body['overall']['label'] is None
        assert len(body['results'])==2
        assert predictor.call_args_list[0].args[0]==text
        assert predictor.call_args_list[0].kwargs['mode']=='article'
        for row in body['results']:assert text[row['start']:row['end']]==row['text']


def test_article_not_sentence_average():
    with patch('backend.main.predict_text',side_effect=fake_prediction) as predictor,patch('backend.main.model_metadata',return_value={}):
        r=TestClient(app).post('/predict',json={'input':'First sentence. Second sentence.','mode':'article'})
        assert r.status_code==200 and predictor.call_count==1
        assert len(r.json()['results'])==1


def test_input_limits():
    client=TestClient(app)
    assert client.post('/predict',json={'input':'x'*100001}).status_code==422
    assert client.post('/predict',json={'input':'hello','mode':'invalid'}).status_code==422
    assert client.post('/predict',json={'input':'   '}).status_code==400


def test_mismatched_policy_cannot_activate():
    metadata={'weights_sha256':'actual'}
    with pytest.raises(RuntimeError,match='weights_sha256'):
        validate_policy({'weights_sha256':'wrong'},metadata)
