import copy,json
from pathlib import Path
import pytest
from research.annotation.compare_reviews import compare,validate,agreement
ROOT=Path(__file__).resolve().parents[1]
M=json.loads((ROOT/'research/annotation/pilot_manifest.json').read_text())

def review(who='A',label='UNCERTAIN'):
    item=M['items'][0]
    return {'pilot_id':M['pilot_id'],'rubric_version':'v1','reviewer_id':who,'annotations':[{'id':item['id'],'text_sha256':item['text_sha256'],'reviewer_id':who,'status':'reviewed','full_text_read':True,'relevance':'POLITICAL','label':label,'confidence':'low','rationale':'Synthetic unit test evidence only.','completed_at':'2026-09-29T00:00:00Z'}]}

def test_pilot_is_unlabeled_and_separate_from_previous_comparison():
    items=M['items'];assert len(items)==100 and len({x['id'] for x in items})==100
    assert sum(x['kind']=='historical_article' for x in items)==60
    assert all('label' not in x and 'bias_text' not in x for x in items)
    assert all(x['text'] is None for x in items if x['kind']=='historical_article')
    previous=json.loads((ROOT/'research/results/context_comparison.json').read_text())
    assert not {str(x['id']) for x in previous['first512']['predictions']}&{x.get('dataset_id') for x in items}

def test_comparison_preserves_disagreement_and_missing_items():
    result=compare(review(),review('B','LEFT'),M)
    assert result['paired_n']==1 and result['label_agreement']['agreement']==0
    assert len(result['missing_or_skipped_ids'])==99 and len(result['disagreements'])==1
    assert result['gold_labels_approved'] is False

def test_same_reviewer_rejected():
    with pytest.raises(ValueError,match='distinct'):compare(review(),review(),M)

@pytest.mark.parametrize('alias',[' A ', 'a', '\uFF21'])
def test_reviewer_aliases_are_not_independent(alias):
    with pytest.raises(ValueError,match='distinct'):
        compare(review('A'),review(alias),M)

@pytest.mark.parametrize('timestamp',['not-a-date','2026-09-29','2026-09-29T00:00:00','2026-02-30T00:00:00Z',123])
def test_invalid_completion_timestamp_rejected(timestamp):
    r=review();r['annotations'][0]['completed_at']=timestamp
    with pytest.raises(ValueError):validate(r,M)

def test_duplicate_manifest_ids_rejected():
    manifest=copy.deepcopy(M);manifest['items'].append(copy.deepcopy(manifest['items'][0]))
    with pytest.raises(ValueError):validate(review(),manifest)

def test_skipped_item_requires_valid_completion_timestamp():
    r=review();r['annotations'][0].update(status='skipped',skip_reason='Snapshot unavailable',completed_at='invalid')
    with pytest.raises(ValueError):validate(r,M)

def test_timezone_offset_timestamp_accepted():
    r=review();r['annotations'][0]['completed_at']='2026-09-28T19:00:00-05:00'
    assert len(validate(r,M))==1

@pytest.mark.parametrize('mutation',['hash','duplicate','unread','relevance'])
def test_invalid_review_rejected(mutation):
    r=review();a=r['annotations'][0]
    if mutation=='hash':a['text_sha256']='changed'
    if mutation=='duplicate':r['annotations'].append(copy.deepcopy(a))
    if mutation=='unread':a['full_text_read']=False
    if mutation=='relevance':a['relevance']='NONPOLITICAL'
    with pytest.raises(ValueError):validate(r,M)

def test_class_agreement_exposes_minor_category_disagreement():
    pairs=[({'label':'LEFT'},{'label':'LEFT'}) for _ in range(9)]
    pairs.append(({'label':'CENTER'},{'label':'RIGHT'}))
    result=agreement(pairs,'label')
    assert result['agreement']==.9
    assert result['per_category']['CENTER']['positive_agreement']==0
    assert result['per_category']['NONPOLITICAL']['positive_agreement'] is None
    assert result['confusion_matrix'][1][2]==1
    assert sum(map(sum,result['confusion_matrix']))==10

def test_positive_agreement_is_symmetric():
    pairs=[({'label':'LEFT'},{'label':'LEFT'}),({'label':'LEFT'},{'label':'CENTER'})]
    first=agreement(pairs,'label');second=agreement([(b,a) for a,b in pairs],'label')
    assert first['per_category']['LEFT']['positive_agreement']==pytest.approx(2/3)
    for k in first['category_order']:
        assert first['per_category'][k]['positive_agreement']==second['per_category'][k]['positive_agreement']
    assert first['confusion_matrix']==[list(row) for row in zip(*second['confusion_matrix'])]

def test_empty_agreement_has_null_metrics_and_zero_counts():
    result=agreement([],'relevance')
    assert result['n']==0 and result['agreement'] is None and result['cohens_kappa'] is None
    assert result['confusion_matrix']==[[0,0,0],[0,0,0],[0,0,0]]
    assert all(v['positive_agreement'] is None for v in result['per_category'].values())

def test_unanimous_single_category_has_undefined_kappa():
    result=agreement([({'label':'LEFT'},{'label':'LEFT'})],'label')
    assert result['agreement']==1 and result['cohens_kappa'] is None
    assert result['per_category']['LEFT']['positive_agreement']==1
