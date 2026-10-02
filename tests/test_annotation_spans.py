"""Automated synthetic span fixtures, never completed human annotations."""
import copy
import hashlib

import pytest

from research.annotation.spans import resolve_text, span_agreement, validate_spans

TEXT = '😀 Café: do not support higher taxes. Later: do not support higher taxes. e\u0301.'


def fixture(historical=False, occurrence=0):
    quote = 'do not support higher taxes'
    start = TEXT.index(quote) if not occurrence else TEXT.rindex(quote)
    item = {'id': 'span-test', 'text': None if historical else TEXT,
            'text_sha256': hashlib.sha256(TEXT.encode()).hexdigest()}
    row = {'id': item['id'], 'span_status': 'ANNOTATED', 'span_protocol_version': 1,
           'evidence_spans': [{'start': start, 'end': start + len(quote), 'text': quote,
                               'source_text_sha256': item['text_sha256'],
                               'direction': 'RIGHT', 'attribution': 'AUTHOR'}]}
    return item, row


def test_exact_codepoints_unicode_repeated_and_negation_preserved():
    item, first = fixture()
    _, second = fixture(occurrence=1)
    assert validate_spans(first, item)['verification'] == 'verified_exact_source'
    assert first['evidence_spans'][0]['start'] == 8  # emoji occupies one codepoint
    assert first['evidence_spans'][0]['text'].startswith('do not')
    assert second['evidence_spans'][0]['start'] > first['evidence_spans'][0]['start']
    assert validate_spans(second, item)['verification'] == 'verified_exact_source'
    # Combining marks are preserved, not NFC-normalized.
    start = TEXT.index('e\u0301')
    first['evidence_spans'] = [{'start': start, 'end': start + 2, 'text': 'e\u0301',
                               'source_text_sha256': item['text_sha256'],
                               'direction': 'LEFT', 'attribution': 'UNKNOWN'}]
    assert validate_spans(first, item)['span_n'] == 1


@pytest.mark.parametrize('mutation', ['overlap', 'duplicate', 'wrong_text', 'wrong_hash', 'wrong_offsets', 'bool_offset', 'direction', 'attribution', 'protocol'])
def test_invalid_spans_rejected(mutation):
    item, row = fixture()
    span = row['evidence_spans'][0]
    if mutation in {'overlap', 'duplicate'}:
        duplicate = copy.deepcopy(span)
        if mutation == 'overlap': duplicate['start'] += 1
        row['evidence_spans'].append(duplicate)
    if mutation == 'wrong_text': span['text'] = 'xx' + span['text'][2:]
    if mutation == 'wrong_hash': span['source_text_sha256'] = 'changed'
    if mutation == 'wrong_offsets': span['start'] += 1; span['end'] += 1
    if mutation == 'bool_offset': span['start'] = True
    if mutation == 'direction': span['direction'] = 'CENTER'
    if mutation == 'attribution': span['attribution'] = 'MODEL'
    if mutation == 'protocol': row['span_protocol_version'] = True
    with pytest.raises(ValueError): validate_spans(row, item)


def test_historical_requires_exact_snapshot_and_never_auto_gold():
    item, row = fixture(historical=True)
    unverified = validate_spans(row, item)
    assert unverified['verification'] == 'unverified_missing_snapshot'
    assert not unverified['eligible_for_human_adjudication']
    assert not unverified['gold_qualified']
    verified = validate_spans(row, item, {item['id']: TEXT})
    assert verified['verification'] == 'verified_exact_source'
    assert not verified['gold_qualified']
    with pytest.raises(ValueError, match='snapshot hash mismatch'):
        validate_spans(row, item, {item['id']: TEXT + ' changed'})


def test_legacy_unassessed_not_negative_or_verified():
    item, _ = fixture()
    assert validate_spans({'id': item['id']}, item)['verification'] == 'not_assessed'
    with pytest.raises(ValueError):
        validate_spans({'span_status': 'NO_DIRECTIONAL_SPANS', 'evidence_spans': []}, item)


def test_no_spans_and_symmetric_agreement_denominators():
    item, first = fixture()
    _, second = fixture(occurrence=1)
    result = span_agreement([(first, second)], {item['id']: item})
    assert result['verified_assessed_pairs'] == 1
    assert result['exact_matched_span_n'] == 0
    assert result['reviewer_a_span_n'] == result['reviewer_b_span_n'] == 1
    assert result['symmetric_exact_span_f1'] == 0
    second['evidence_spans'] = copy.deepcopy(first['evidence_spans'])
    assert span_agreement([(first, second)], {item['id']: item})['symmetric_exact_span_f1'] == 1
    second['evidence_spans'][0]['attribution'] = 'QUOTED'
    assert span_agreement([(first, second)], {item['id']: item})['exact_matched_span_n'] == 0
    empty = {'id': item['id'], 'span_protocol_version': 1, 'span_status': 'NO_DIRECTIONAL_SPANS', 'evidence_spans': []}
    result = span_agreement([(empty, empty)], {item['id']: item})
    assert result['both_no_directional_spans_n'] == 1
    assert result['reviewer_a_exact_match_fraction'] is None
    assert result['symmetric_exact_span_f1'] is None


def test_unverified_historical_excluded_from_span_agreement():
    item, row = fixture(historical=True)
    result = span_agreement([(row, row)], {item['id']: item})
    assert result['verified_assessed_pairs'] == 0
    assert result['excluded_missing_snapshot_ids'] == [item['id']]
    assert result['reviewer_a_span_n'] == 0
    result = span_agreement([(row, row)], {item['id']: item}, {item['id']: TEXT})
    assert result['exact_matched_span_n'] == 1
    assert result['gold_qualified'] is False
