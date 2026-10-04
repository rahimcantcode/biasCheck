from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.summary import summarize_predictions
from backend.utils import sentence_spans


def fake_prediction(label):
    labels = ['LEFT', 'CENTER', 'RIGHT']
    return {'label': label, 'label_id': labels.index(label),
            'probabilities': {key: 0.8 if key == label else 0.1 for key in labels}}


def test_each_sentence_has_one_vote_and_ties_are_not_center():
    result = summarize_predictions([fake_prediction('LEFT'), fake_prediction('RIGHT')])
    assert result['counts'] == {'LEFT': 1, 'CENTER': 0, 'RIGHT': 1}
    assert result['label'] is None
    result = summarize_predictions([fake_prediction('LEFT'), fake_prediction('LEFT'), fake_prediction('RIGHT')])
    assert result['label'] == 'LEFT'
    assert result['shares']['LEFT'] == pytest.approx(2 / 3)
    assert sum(result['shares'].values()) == pytest.approx(1)


def test_empty_summary():
    assert summarize_predictions([])['label'] is None
    assert summarize_predictions([])['total_sentences'] == 0


def test_sentence_boundaries_preserve_unicode_and_abbreviations():
    text = '  Dr. Smith met the U.S. senator.\n\n😀 Taxes fell. Taxes fell.  '
    spans = sentence_spans(text)
    assert [text[a:b] for a, b in spans] == [
        'Dr. Smith met the U.S. senator.', '😀 Taxes fell.', 'Taxes fell.']
    assert all(spans[i][1] <= spans[i + 1][0] for i in range(len(spans) - 1))


@pytest.mark.parametrize('mode', ['article', 'paragraph', 'sentence'])
def test_api_uses_sentence_counts_and_preserves_the_exact_article(mode):
    text = '  Taxes fell.\n\n😀 Taxes fell.  '
    with patch('backend.main.predict_sentences', return_value=[fake_prediction('LEFT'), fake_prediction('RIGHT')]) as model:
        response = TestClient(app).post('/predict', json={'input': text, 'mode': mode})
    assert response.status_code == 200
    data = response.json()
    assert data['mode'] == 'sentence'
    assert data['resolved_text'] == text
    assert data['summary']['counts'] == {'LEFT': 1, 'CENTER': 0, 'RIGHT': 1}
    model.assert_called_once_with(['Taxes fell.', '😀 Taxes fell.'])
    for sentence in data['results']:
        assert text[sentence['start']:sentence['end']] == sentence['text']


def test_blank_input_never_reaches_model():
    with patch('backend.main.predict_sentences') as model:
        response = TestClient(app).post('/predict', json={'input': ' \n '})
        assert response.status_code == 400
        model.assert_not_called()


def test_long_articles_are_rejected_without_partial_classification():
    with patch('backend.main.predict_sentences') as model:
        response = TestClient(app).post('/predict', json={'input': 'Taxes fell. ' * 301})
        assert response.status_code == 400
        model.assert_not_called()
