import pytest
from research.scripts.prepare_data import domain,normalized_hash
from research.scripts.calibrate import fit
from research.scripts.evaluate import summarize


def test_publisher_subdomains_are_one_group():
    assert domain('https://blogs.wsj.com/a')==domain('https://online.wsj.com/b')==domain('https://wsj.com')
    assert domain('https://politicalticker.blogs.cnn.com')==domain('https://money.cnn.com')
    assert domain('https://www.bbc.co.uk')=='bbc.co.uk'


def test_duplicate_whitespace_and_case():
    assert normalized_hash('An Article\n today')==normalized_hash('an article today ')


def test_test_split_cannot_fit_calibration():
    with pytest.raises(ValueError,match='Only validation'):fit({'split':'test'})
    with pytest.raises(ValueError,match='human-reviewed'):fit({'split':'validation'})


def test_abstention_is_not_accuracy():
    result=summarize([{'gold':'LEFT','raw_label':'RIGHT','decision':'abstained','label':None}])
    assert result['coverage']==0 and result['selective_accuracy'] is None and result['raw_accuracy']==0


def test_offline_policy_rejects_reused_test():
    from research.scripts.evaluate_policy import evaluate
    metadata=dict(weights_sha256='w',config_sha256='c',tokenizer_sha256='t',aggregation='a',max_length=512,stride=64,id2label={'0':'LEFT','1':'CENTER','2':'RIGHT'})
    policy={**metadata,'schema_version':1,'release_approved':False,'temperature':1.,'min_confidence':.7,'min_margin':.2,'min_tokens':30,'validated_modes':['article'],'calibration_data_sha256':'same'}
    report={'model':metadata,'mode':'article','split':'test','data_sha256':'same','annotation_provenance':{'human_reviewed':True,'reference':'synthetic unit test fixture'}}
    with pytest.raises(ValueError,match='identical'):evaluate(report,policy,{**report,'split':'validation'})
