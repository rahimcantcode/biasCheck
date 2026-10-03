"""Synthetic contract fixtures only. These are not completed human reviews."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from research.annotation.validate_adjudication import (
    RESOLUTION_FIELDS, _read, digest, make_template, validate_adjudication,
)

TEXT = '😀 We do not support higher taxes. Later, higher taxes were discussed.'


def fixture(historical=False):
    source_hash = hashlib.sha256(TEXT.encode()).hexdigest()
    manifest = {'schema_version': 2, 'rubric_version': 'v2', 'pilot_id': 'synthetic-test-only',
                'items': [{'id': 'T01', 'kind': 'historical_article' if historical else 'controlled_example',
                           'text': None if historical else TEXT, 'text_sha256': source_hash}]}
    start, phrase = TEXT.index('do not'), 'do not support higher taxes'
    row = {'id': 'T01', 'text_sha256': source_hash, 'reviewer_id': 'test-reviewer-A',
           'rubric_version': 'v2', 'status': 'reviewed', 'full_text_read': True,
           'relevance': 'POLITICAL', 'author_framing': 'RIGHT', 'label': 'RIGHT',
           'issue_policy_stance': 'NOT_ASSESSED', 'attribution': 'AUTHOR_NARRATION',
           'context_sufficiency': 'SUFFICIENT', 'uncertainty_reason': 'NONE',
           'confidence': 'low', 'rationale': 'Synthetic software fixture, not a human political judgment.',
           'completed_at': '2026-10-02T00:00:00Z',
           'text_context': {'scope': 'complete_frozen_text', 'text_sha256': source_hash,
                            'external_context_used': False, 'external_context_notes': ''},
           'prior_exposure': {'model_predictions': False, 'legacy_labels': False,
                              'other_reviewer_answers': False, 'notes': ''},
           'review_phase': 'frozen_main', 'review_pass_id': 'test-pass-1', 'rubric_freeze_id': 'test-freeze',
           'span_status': 'ANNOTATED', 'span_protocol_version': 1,
           'evidence_spans': [{'start': start, 'end': start + len(phrase), 'text': phrase,
                               'source_text_sha256': source_hash, 'direction': 'RIGHT', 'attribution': 'AUTHOR'}]}
    first = {'schema_version': 2, 'rubric_version': 'v2', 'pilot_id': manifest['pilot_id'],
             'reviewer_id': row['reviewer_id'], 'reviewer_kind': 'human', 'annotation_method': 'manual',
             'independently_completed': True, 'exported_at': '2026-10-02T00:01:00Z',
             'annotations': [row]}
    second = copy.deepcopy(first)
    second['reviewer_id'] = second['annotations'][0]['reviewer_id'] = 'test-reviewer-B'
    return first, second, manifest


def document(first, second, manifest, snapshots=None):
    value = make_template(first, second, manifest, snapshots)
    original = first['annotations'][0]
    value['items'][0].update(status='adjudicated', adjudication={
        'adjudicator_id': 'test-adjudicator-C', 'adjudicator_kind': 'human', 'annotation_method': 'manual',
        'completed_at': '2026-10-02T00:02:00Z', 'full_text_read': True, 'both_reviews_considered': True,
        'text_context': copy.deepcopy(original['text_context']),
        'prior_exposure': {'model_predictions': False, 'legacy_labels': False, 'other_reviewer_answers': True,
                           'notes': 'Synthetic software fixture considered both test review objects.'},
        'resolution': {k: copy.deepcopy(original[k]) for k in RESOLUTION_FIELDS}})
    return value


def test_matching_reviews_never_automatically_resolve_or_create_gold():
    first, second, manifest = fixture()
    result = validate_adjudication(first, second, manifest, make_template(first, second, manifest))
    record = result['records'][0]
    assert record['status'] == 'unresolved' and record['adjudication'] is None
    assert record['disagreement_axes'] == []
    assert result['summary']['human_adjudicated_development_n'] == 0
    assert result['development_only'] and record['development_only']
    for value in (result, record):
        assert value['final_test_eligible'] is False
        assert value['gold_labels_approved'] is False
        assert value['release_approved'] is False


def test_valid_exact_source_adjudication_preserves_originals_and_scope():
    first, second, manifest = fixture()
    original = copy.deepcopy((first, second, manifest))
    result = validate_adjudication(first, second, manifest, document(first, second, manifest))
    row = result['records'][0]
    assert row['status'] == 'human_adjudicated_development'
    assert row['span_verification']['verification'] == 'verified_exact_source'
    assert row['span_verification']['gold_qualified'] is False
    assert row['adjudication']['resolution']['evidence_spans'][0]['text'].startswith('do not')
    assert row['original_reviews'] == [first['annotations'][0], second['annotations'][0]]
    assert (first, second, manifest) == original
    assert 'text' not in row['source']
    assert result['review_sha256'][first['reviewer_id']] == digest(first)


@pytest.mark.parametrize('scope', ['gold_labels_approved', 'final_test_eligible', 'release_approved', 'development_only'])
def test_claimed_approval_or_final_test_scope_rejected(scope):
    first, second, manifest = fixture()
    value = document(first, second, manifest)
    value[scope] = not value[scope]
    with pytest.raises(ValueError, match='scope mismatch'):
        validate_adjudication(first, second, manifest, value)


def test_modified_source_or_review_invalidates_existing_adjudication():
    first, second, manifest = fixture()
    value = document(first, second, manifest)
    second['annotations'][0]['rationale'] = 'A changed synthetic rationale cannot share the prior signature.'
    with pytest.raises(ValueError, match='review_sha256'):
        validate_adjudication(first, second, manifest, value)
    first, second, manifest = fixture()
    manifest['items'][0]['text'] += ' altered'
    with pytest.raises(ValueError, match='hash mismatch'):
        validate_adjudication(first, second, manifest, value)


def test_historical_snapshot_required_even_if_no_spans():
    first, second, manifest = fixture(historical=True)
    for review in (first, second):
        review['annotations'][0].update(span_status='NO_DIRECTIONAL_SPANS', evidence_spans=[])
    value = document(first, second, manifest)
    with pytest.raises(ValueError, match='exact frozen source snapshot'):
        validate_adjudication(first, second, manifest, value)
    result = validate_adjudication(first, second, manifest, value, {'T01': TEXT})
    assert result['records'][0]['span_verification']['verification'] == 'verified_exact_source'
    unresolved = validate_adjudication(first, second, manifest, make_template(first, second, manifest))
    assert 'missing_source_snapshot' in unresolved['records'][0]['limitations']


@pytest.mark.parametrize('field,value', [
    ('adjudicator_id', 'TEST-REVIEWER-A'), ('adjudicator_kind', 'ai'),
    ('annotation_method', 'model_generated'), ('full_text_read', False),
    ('both_reviews_considered', False), ('completed_at', '2026-10-02T00:02:00'),
    ('completed_at', '2026-10-01T00:02:00Z'),
])
def test_invalid_or_nonhuman_adjudication_rejected(field, value):
    first, second, manifest = fixture()
    adjudication = document(first, second, manifest)
    adjudication['items'][0]['adjudication'][field] = value
    with pytest.raises(ValueError):
        validate_adjudication(first, second, manifest, adjudication)


@pytest.mark.parametrize('mutation', ['wrong_direction', 'wrong_text', 'wrong_offset', 'wrong_hash', 'duplicate_span', 'bool_offset'])
def test_invalid_resolution_span_rejected(mutation):
    first, second, manifest = fixture()
    value = document(first, second, manifest)
    spans = value['items'][0]['adjudication']['resolution']['evidence_spans']
    span = spans[0]
    if mutation == 'wrong_direction': span['direction'] = 'CENTER'
    if mutation == 'wrong_text': span['text'] = 'XX' + span['text'][2:]
    if mutation == 'wrong_offset': span['start'] += 1; span['end'] += 1
    if mutation == 'wrong_hash': span['source_text_sha256'] = 'wrong'
    if mutation == 'duplicate_span': spans.append(copy.deepcopy(span))
    if mutation == 'bool_offset': span['start'] = True
    with pytest.raises(ValueError):
        validate_adjudication(first, second, manifest, value)


def test_unassessed_spans_do_not_become_negative_examples():
    first, second, manifest = fixture()
    value = document(first, second, manifest)
    value['items'][0]['adjudication']['resolution'].update(span_status='NOT_ASSESSED', evidence_spans=[])
    result = validate_adjudication(first, second, manifest, value)
    assert result['records'][0]['span_verification']['verification'] == 'not_assessed'
    assert 'adjudicated_spans_unassessed' in result['records'][0]['limitations']


def test_disagreement_stays_explicit_and_uncertain_is_not_forced_to_center():
    first, second, manifest = fixture()
    second['annotations'][0].update(author_framing='LEFT', label='LEFT')
    value = make_template(first, second, manifest)
    unresolved = validate_adjudication(first, second, manifest, value)['records'][0]
    assert unresolved['status'] == 'unresolved'
    assert 'author_framing' in unresolved['disagreement_axes']
    value = document(first, second, manifest)
    value['items'][0]['adjudication']['resolution'].update(author_framing='UNCERTAIN', label='UNCERTAIN',
                                                         uncertainty_reason='ATTRIBUTION_UNCLEAR')
    result = validate_adjudication(first, second, manifest, value)['records'][0]
    assert result['adjudication']['resolution']['label'] == 'UNCERTAIN'
    assert 'adjudicated_primary_uncertainty' in result['limitations']
    assert result['original_reviews'][0]['label'] == 'RIGHT'
    assert result['original_reviews'][1]['label'] == 'LEFT'


def test_context_exposure_and_review_round_limitations_survive_adjudication():
    first, second, manifest = fixture()
    first['annotations'][0]['prior_exposure'].update(model_predictions=True, notes='Synthetic prior model exposure disclosure.')
    second['annotations'][0]['text_context'].update(external_context_used=True, external_context_notes='Synthetic external article context disclosure.')
    second['annotations'][0]['review_phase'] = 'post_discussion_rereview'
    value = document(first, second, manifest)
    decision = value['items'][0]['adjudication']
    decision['prior_exposure']['legacy_labels'] = True
    decision['text_context'].update(external_context_used=True, external_context_notes='Synthetic adjudicator context disclosure.')
    result = validate_adjudication(first, second, manifest, value)['records'][0]
    assert set(result['limitations']) == {'prior_reviewer_exposure', 'reviewer_external_context',
        'different_review_round_or_freeze', 'post_discussion_rereview',
        'adjudicator_external_context', 'adjudicator_model_or_legacy_exposure'}
    assert result['original_reviews'][0]['prior_exposure']['model_predictions'] is True


def test_missing_review_cannot_be_adjudicated_or_silently_dropped():
    first, second, manifest = fixture()
    second['annotations'] = []
    value = make_template(first, second, manifest)
    result = validate_adjudication(first, second, manifest, value)
    assert result['summary']['unresolved_n'] == 1
    assert 'missing_or_skipped_review' in result['records'][0]['limitations']
    value = document(first, second, manifest)
    with pytest.raises(ValueError, match='two completed reviews'):
        validate_adjudication(first, second, manifest, value)
    value['items'] = []
    with pytest.raises(ValueError, match='Every manifest item'):
        validate_adjudication(first, second, manifest, value)


def test_identical_reviewer_alias_or_duplicate_items_rejected():
    first, second, manifest = fixture()
    second['reviewer_id'] = second['annotations'][0]['reviewer_id'] = 'TEST-REVIEWER-A'
    with pytest.raises(ValueError, match='distinct human reviewers'):
        make_template(first, second, manifest)
    first, second, manifest = fixture()
    value = document(first, second, manifest)
    value['items'].append(copy.deepcopy(value['items'][0]))
    with pytest.raises(ValueError, match='unique known IDs'):
        validate_adjudication(first, second, manifest, value)
    manifest['items'].append(copy.deepcopy(manifest['items'][0]))
    with pytest.raises(ValueError, match='unique IDs'):
        make_template(first, second, manifest)


def test_adjudicator_cannot_claim_not_to_have_seen_reviews():
    first, second, manifest = fixture()
    value = document(first, second, manifest)
    value['items'][0]['adjudication']['prior_exposure']['other_reviewer_answers'] = False
    with pytest.raises(ValueError, match='seeing both human reviews'):
        validate_adjudication(first, second, manifest, value)


def test_review_timestamp_cannot_follow_export():
    first, second, manifest = fixture()
    first['annotations'][0]['completed_at'] = '2026-10-03T00:00:00Z'
    with pytest.raises(ValueError, match='after its export'):
        make_template(first, second, manifest)


@pytest.mark.parametrize('invalid', ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'])
def test_ambiguous_json_rejected(tmp_path, invalid):
    file = tmp_path / 'invalid.json'
    file.write_text(invalid)
    with pytest.raises(ValueError): _read(file)


def test_cli_template_then_validation_and_refuse_overwrite(tmp_path):
    first, second, manifest = fixture()
    for name, value in [('first', first), ('second', second), ('manifest', manifest)]:
        (tmp_path / (name + '.json')).write_text(json.dumps(value))
    script = Path(__file__).resolve().parents[1] / 'research/annotation/validate_adjudication.py'
    common = [sys.executable, str(script), '--first', str(tmp_path / 'first.json'),
              '--second', str(tmp_path / 'second.json'), '--manifest', str(tmp_path / 'manifest.json')]
    template = tmp_path / 'template.json'
    subprocess.run(common + ['--template', '--output', str(template)], check=True, capture_output=True)
    assert json.loads(template.read_text())['items'][0]['adjudication'] is None
    output = tmp_path / 'validated.json'
    subprocess.run(common + ['--adjudication', str(template), '--output', str(output)], check=True, capture_output=True)
    assert json.loads(output.read_text())['summary']['human_adjudicated_development_n'] == 0
    result = subprocess.run(common + ['--template', '--output', str(template)], capture_output=True)
    assert result.returncode != 0
    assert b'FileExistsError' in result.stderr
