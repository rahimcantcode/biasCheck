"""Synthetic test records only; these are not completed human annotations."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from research.annotation.compare_reviews import agreement, compare, validate, wilson_interval

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'research/annotation'
M = json.loads((FOLDER / 'pilot_manifest_v2.json').read_text())
V1 = json.loads((FOLDER / 'pilot_manifest.json').read_text())


def review(who='reviewer-A', label='UNCERTAIN', index=0):
    item = M['items'][index]
    return {
        'schema_version': 2, 'pilot_id': M['pilot_id'], 'rubric_version': 'v2',
        'reviewer_id': who, 'reviewer_kind': 'human', 'annotation_method': 'manual',
        'independently_completed': True, 'exported_at': '2026-10-02T00:00:00Z',
        'annotations': [{
            'id': item['id'], 'text_sha256': item['text_sha256'], 'reviewer_id': who,
            'rubric_version': 'v2', 'status': 'reviewed', 'full_text_read': True,
            'relevance': 'POLITICAL', 'author_framing': label, 'label': label,
            'issue_policy_stance': 'NOT_ASSESSED', 'attribution': 'UNCLEAR',
            'context_sufficiency': 'SUFFICIENT',
            'uncertainty_reason': 'MIXED_AUTHOR_POSITIONS' if label == 'UNCERTAIN' else 'NONE',
            'confidence': 'low', 'rationale': 'Synthetic unit test evidence only, never human gold.',
            'completed_at': '2026-10-02T00:00:00Z',
            'text_context': {'scope': 'complete_frozen_text', 'text_sha256': item['text_sha256'],
                             'external_context_used': False, 'external_context_notes': ''},
            'prior_exposure': {'model_predictions': False, 'legacy_labels': False,
                               'other_reviewer_answers': False, 'notes': ''},
            'review_phase': 'initial_independent_10', 'review_pass_id': 'test-only',
            'rubric_freeze_id': '',
        }],
    }


def test_pilot_is_unlabeled_and_separate_from_previous_comparison():
    items = M['items']
    assert len(items) == 100 and len({x['id'] for x in items}) == 100
    assert sum(x['kind'] == 'historical_article' for x in items) == 60
    assert all('label' not in x and 'bias_text' not in x for x in items)
    assert all(x['text'] is None for x in items if x['kind'] == 'historical_article')
    assert M['human_reviewed'] is False
    previous = json.loads((ROOT / 'research/results/context_comparison.json').read_text())
    assert not {str(x['id']) for x in previous['first512']['predictions']} & {x.get('dataset_id') for x in items}


def test_v1_preserved_and_v2_exact_same_text_and_order():
    assert M['items'] == V1['items']
    assert M['pilot_id'] != V1['pilot_id']
    assert M['parent_pilot_id'] == V1['pilot_id']
    assert M['parent_manifest_sha256'] == hashlib.sha256((FOLDER / 'pilot_manifest.json').read_bytes()).hexdigest()
    assert (FOLDER / 'legacy_v1/pilot_manifest.json').read_bytes() == (FOLDER / 'pilot_manifest.json').read_bytes()
    assert 'rubric_version:\'v1\'' in (FOLDER / 'legacy_v1/Bias_Checker_Review_Pilot.html').read_text()
    for item in M['items']:
        if item['text'] is not None:
            assert hashlib.sha256(item['text'].encode()).hexdigest() == item['text_sha256']


def test_comparison_preserves_disagreement_missing_and_intervals():
    result = compare(review(), review('reviewer-B', 'LEFT'), M)
    assert result['paired_n'] == 1 and result['label_agreement']['agreement'] == 0
    assert result['label_agreement']['agree_n'] == 0
    assert result['label_agreement']['disagree_n'] == 1
    assert result['label_agreement']['agreement_ci95_wilson'][1] > .7
    assert len(result['missing_or_skipped_ids']) == 99 and len(result['disagreements']) == 1
    assert result['disagreements'][0]['reviewer_a']['uncertainty_reason'] == 'MIXED_AUTHOR_POSITIONS'
    assert result['disagreements'][0]['adjudicator_id'] is None
    assert result['gold_labels_approved'] is False


@pytest.mark.parametrize('second', ['reviewer-A', 'reviewer-a'])
def test_same_reviewer_rejected(second):
    with pytest.raises(ValueError, match='distinct'):
        compare(review(), review(second), M)


@pytest.mark.parametrize('mutation', [
    'hash', 'duplicate', 'unread', 'relevance', 'pilot', 'rubric', 'schema', 'per_row_rubric',
    'empty_reviewer', 'whitespace_reviewer', 'mixed_reviewer', 'nonhuman', 'machine_method',
    'unattested', 'missing_attribution', 'missing_uncertainty', 'unknown_exposure',
    'exposed_no_notes', 'external_no_notes', 'wrong_context_hash', 'wrong_context_scope',
    'missing_context', 'insufficient_center', 'missing_freeze', 'naive_timestamp',
])
def test_invalid_review_rejected(mutation):
    r = review()
    a = r['annotations'][0]
    if mutation == 'hash': a['text_sha256'] = 'changed'
    if mutation == 'duplicate': r['annotations'].append(copy.deepcopy(a))
    if mutation == 'unread': a['full_text_read'] = False
    if mutation == 'relevance': a['relevance'] = 'NONPOLITICAL'
    if mutation == 'pilot': r['pilot_id'] = 'other-pilot'
    if mutation == 'rubric': r['rubric_version'] = 'v1'
    if mutation == 'schema': r['schema_version'] = 1
    if mutation == 'per_row_rubric': a['rubric_version'] = 'v1'
    if mutation == 'empty_reviewer': r['reviewer_id'] = ''
    if mutation == 'whitespace_reviewer': r['reviewer_id'] = '  '
    if mutation == 'mixed_reviewer': a['reviewer_id'] = 'another-person'
    if mutation == 'nonhuman': r['reviewer_kind'] = 'machine'
    if mutation == 'machine_method': r['annotation_method'] = 'model_generated'
    if mutation == 'unattested': r['independently_completed'] = False
    if mutation == 'missing_attribution': a.pop('attribution')
    if mutation == 'missing_uncertainty': a.pop('uncertainty_reason')
    if mutation == 'unknown_exposure': a['prior_exposure'].pop('model_predictions')
    if mutation == 'exposed_no_notes': a['prior_exposure']['model_predictions'] = True
    if mutation == 'external_no_notes': a['text_context']['external_context_used'] = True
    if mutation == 'wrong_context_hash': a['text_context']['text_sha256'] = 'wrong'
    if mutation == 'wrong_context_scope': a['text_context']['scope'] = 'headline_only'
    if mutation == 'missing_context': a.pop('text_context')
    if mutation == 'insufficient_center':
        a.update(author_framing='CENTER', label='CENTER', uncertainty_reason='NONE', context_sufficiency='INSUFFICIENT')
    if mutation == 'missing_freeze': a['review_phase'] = 'frozen_main'
    if mutation == 'naive_timestamp': a['completed_at'] = '2026-10-02T00:00:00'
    with pytest.raises(ValueError):
        validate(r, M)


def test_v1_cannot_be_silently_upgraded():
    legacy = {'pilot_id': V1['pilot_id'], 'rubric_version': 'v1', 'reviewer_id': 'reviewer-A', 'annotations': []}
    with pytest.raises(ValueError, match='legacy v1'):
        validate(legacy, M)
    with pytest.raises(ValueError, match='legacy v1'):
        validate(review(), V1)


def test_no_policy_stance_does_not_force_center():
    first, second = review(label='LEFT'), review('reviewer-B', label='LEFT')
    first['annotations'][0]['issue_policy_stance'] = 'NO_EXPLICIT_STANCE'
    second['annotations'][0]['issue_policy_stance'] = 'NO_EXPLICIT_STANCE'
    result = compare(first, second, M)
    assert result['per_axis']['author_framing']['reviewer_a_counts'] == {'LEFT': 1}
    assert result['per_axis']['issue_policy_stance']['reviewer_a_counts'] == {'NO_EXPLICIT_STANCE': 1}


def test_policy_and_author_axis_different_denominators():
    first, second = review(), review('reviewer-B')
    second['annotations'][0].update(relevance='NONPOLITICAL', author_framing='NOT_APPLICABLE', label='NONPOLITICAL', uncertainty_reason='NONE')
    result = compare(first, second, M)
    assert result['per_axis']['relevance']['n'] == 1
    assert result['per_axis']['author_framing']['n'] == 0
    assert result['per_axis']['author_framing']['excluded_n'] == 1
    assert result['per_axis']['issue_policy_stance']['n'] == 0
    assert result['per_axis']['issue_policy_stance']['excluded_n'] == 1
    assert result['slices']['historical_article']['paired_n'] == 1
    assert result['slices']['controlled_example']['paired_n'] == 0


def test_exposure_preserved_and_excluded_only_from_strict_subset():
    first, second = review(), review('reviewer-B')
    row = first['annotations'][0]
    row['prior_exposure'].update(model_predictions=True, legacy_labels=True, other_reviewer_answers=True, notes='Previously saw diagnostic scores and peer answer in discussion.')
    row['text_context'].update(external_context_used=True, external_context_notes='Read the complete live article and an event background panel.')
    result = compare(first, second, M)
    assert result['paired_n'] == 1
    assert result['blinded_frozen_text_only']['paired_n'] == 0
    saved = result['disagreements'][0]['reviewer_a']
    assert saved['prior_exposure'] == row['prior_exposure']
    assert saved['text_context'] == row['text_context']
    assert set(result['disagreements'][0]['review_flags']) == {'primary_uncertainty', 'external_context', 'prior_exposure'}


def test_review_round_mismatch_excluded_from_same_round():
    first, second = review(), review('reviewer-B')
    second['annotations'][0].update(review_phase='post_discussion_rereview', rubric_freeze_id='freeze-test-only')
    result = compare(first, second, M)
    assert result['same_round']['paired_n'] == result['blinded_frozen_text_only']['paired_n'] == 0
    assert 'different_review_round_or_freeze' in result['disagreements'][0]['review_flags']


def test_empty_and_skipped_do_not_create_human_labels():
    first, second = review(), review('reviewer-B')
    first['annotations'][0].update(status='skipped', skip_reason='Unavailable frozen snapshot')
    second['annotations'] = []
    result = compare(first, second, M)
    assert result['completed'] == [0, 0] and result['paired_n'] == 0
    assert result['per_axis']['label']['agreement'] is None
    assert result['per_axis']['label']['agreement_ci95_wilson'] is None
    assert len(result['missing_or_skipped_ids']) == 100


def test_wilson_and_degenerate_kappa():
    assert wilson_interval(0, 0) is None
    lo, hi = wilson_interval(5, 10)
    assert lo == pytest.approx(.23659, abs=.00001)
    assert hi == pytest.approx(.76341, abs=.00001)
    row = {'label': 'CENTER'}
    result = agreement([(row, row)], 'label')
    assert result['cohens_kappa'] is None and result['agreement'] == 1
    assert result['agreement_ci95_wilson'][0] < .21


def test_standalone_html_is_current_and_no_labels_added():
    template = (FOLDER / 'reviewer.template.html').read_text()
    payload = (FOLDER / 'pilot_manifest_v2.json').read_text().replace('<', '\\u003c')
    script = (FOLDER / 'reviewer.js').read_text().replace('</script', '<\\/script')
    assert (FOLDER / 'Bias_Checker_Review_Pilot.html').read_text() == template.replace('__PILOT_DATA__', payload).replace('__REVIEWER_SCRIPT__', script)
    assert 'source_url' not in {key for row in M['items'] for key in row}


def test_span_agreement_in_same_round_and_blinded_subsets():
    index = next(i for i, item in enumerate(M['items']) if item['kind'] == 'controlled_example')
    first, second = review(label='LEFT', index=index), review('reviewer-B', label='LEFT', index=index)
    item = M['items'][index]
    for record in (first, second):
        record['annotations'][0].update(span_protocol_version=1, span_status='ANNOTATED', evidence_spans=[{
            'start': 0, 'end': 12, 'text': item['text'][:12], 'source_text_sha256': item['text_sha256'],
            'direction': 'RIGHT', 'attribution': 'QUOTED',
        }])
    result = compare(first, second, M)
    for subset in ('same_round', 'blinded_frozen_text_only'):
        spans = result[subset]['span_agreement']
        assert spans['paired_items'] == spans['verified_assessed_pairs'] == 1
        assert spans['exact_matched_span_n'] == 1
        assert spans['gold_qualified'] is False
    first['annotations'][0]['prior_exposure'].update(model_predictions=True, notes='Previously saw synthetic fixture model output.')
    result = compare(first, second, M)
    assert result['same_round']['span_agreement']['verified_assessed_pairs'] == 1
    assert result['blinded_frozen_text_only']['span_agreement']['paired_items'] == 0
    assert result['blinded_frozen_text_only']['span_agreement']['symmetric_exact_span_f1'] is None


def test_span_agreement_round_mismatch_excluded_from_subset_denominators():
    first, second = review(), review('reviewer-B')
    second['annotations'][0].update(review_phase='frozen_main', rubric_freeze_id='fixture-freeze')
    result = compare(first, second, M)
    assert result['span_agreement']['paired_items'] == 1
    assert result['same_round']['span_agreement']['paired_items'] == 0
    assert result['blinded_frozen_text_only']['span_agreement']['paired_items'] == 0
