"""Synthetic regression cases; these are not human-reviewed accuracy data."""
import copy
import math
import pytest
from research.scripts.evaluate import summarize
from research.scripts.evaluate_policy import evaluate
from backend.model import classify_scores


@pytest.mark.parametrize('logits',[[math.nan,0,0],[math.inf,0,0],[-math.inf,0,0],[0,1],[[0,1,2]],['0','1','2'],[True,False,True]])
def test_invalid_logits_never_classify(logits):
    _,policy,_=reports();policy['release_approved']=True
    with pytest.raises(ValueError,match='three finite numeric'):classify_scores(logits,40,'article',policy)


def test_large_finite_logits_normalize_without_nan():
    _,policy,_=reports();policy['release_approved']=True;policy['temperature']=1e-300
    scores,reason=classify_scores([1e308,-1e308,0],40,'article',policy)
    assert scores.tolist()==[1.,0.,0.] and reason is None


def row(gold, accepted=True):
    return dict(gold=gold, raw_label=gold, decision='classified' if accepted else 'abstained',
                label=gold if accepted else None)


def test_perfect_raw_scores_cannot_hide_abstained_class():
    result=summarize([row('LEFT'),row('CENTER',False),row('RIGHT')])
    assert result['raw_accuracy']==1 and result['raw_macro_f1']==1
    assert result['macro_f1']==pytest.approx(2/3)
    assert result['per_class']['CENTER']['recall']==0
    assert result['raw_per_class']['CENTER']['recall']==1
    assert result['per_class_coverage']['CENTER']==0
    assert result['decision_confusion_matrix']==[[1,0,0,0],[0,0,0,1],[0,0,1,0]]
    assert result['selective_accuracy']==1 and result['coverage']==pytest.approx(2/3)


def test_abstain_everything_has_zero_product_recall():
    result=summarize([row(x,False) for x in ['LEFT','CENTER','RIGHT']])
    assert result['raw_accuracy']==1 and result['macro_f1']==0
    assert result['selective_accuracy'] is None and result['coverage']==0


def test_wrong_accepted_prediction_and_out_of_scope_errors_are_visible():
    rows=[{**row('LEFT'),'label':'RIGHT'},row('CENTER'),
          {**row('LEFT'),'gold':'NONPOLITICAL'},
          {**row('LEFT',False),'gold':'UNCERTAIN'}]
    result=summarize(rows)
    assert result['selective_accuracy']==.5 and result['per_class']['LEFT']['recall']==0
    assert result['decision_confusion_matrix'][0]==[0,0,1,0]
    assert result['nonpolitical_false_label_rate']==1
    assert result['uncertain_false_label_rate']==0
    assert result['marginal_binomial_diagnostics']['uncertain_false_label_rate'][1]>.7
    assert result['raw_confusion_matrix'][0]==[1,0,0]


@pytest.mark.parametrize('mutation',[{'decision':'classified','label':None},{'decision':'abstained','label':'LEFT'},
                                     {'raw_label':'UNRECOGNIZED'},{'gold':'BAD'}])
def test_invalid_decisions_fail_closed(mutation):
    with pytest.raises(ValueError):summarize([{**row('LEFT'),**mutation}])


def reports():
    metadata=dict(weights_sha256='w',config_sha256='c',tokenizer_sha256='t',aggregation='a',
                  max_length=512,stride=64,preprocessing='exact-text-v2',id2label={'0':'LEFT','1':'CENTER','2':'RIGHT'})
    policy={**metadata,'schema_version':1,'release_approved':False,'temperature':1.,'min_confidence':.7,
            'min_margin':.2,'min_tokens':30,'validated_modes':['article'],'calibration_data_sha256':'validation'}
    def report(split):
        return dict(model=copy.deepcopy(metadata),split=split,mode='article',data_sha256=split,
                    annotation_provenance={'human_reviewed':True,'reference':'synthetic regression fixture only'},
                    predictions=[{**row('LEFT'), 'id':split,'text_sha256':split,'logits':[10,0,0],'token_count':40}])
    return report('test'),policy,report('validation')


def test_calibration_checkpoint_mismatch_fails():
    test,policy,valid=reports();valid['model']['weights_sha256']='different'
    with pytest.raises(RuntimeError,match='weights_sha256'):evaluate(test,policy,valid)


def test_preprocessing_change_invalidates_old_calibration():
    test,policy,valid=reports();policy['preprocessing']='clean-text-v1'
    with pytest.raises(RuntimeError,match='preprocessing'):evaluate(test,policy,valid)


def test_missing_preprocessing_cannot_implicitly_match_legacy_reports():
    test,policy,valid=reports()
    del policy['preprocessing'];del test['model']['preprocessing'];del valid['model']['preprocessing']
    with pytest.raises(RuntimeError,match='preprocessing'):evaluate(test,policy,valid)


def test_calibration_mode_mismatch_fails():
    test,policy,valid=reports();valid['mode']='sentence'
    with pytest.raises(ValueError,match='modes must match'):evaluate(test,policy,valid)


def test_calibration_label_mapping_mismatch_fails():
    test,policy,valid=reports();valid['model']['id2label']={'0':'RIGHT','1':'CENTER','2':'LEFT'}
    with pytest.raises(ValueError,match='mapping mismatch'):evaluate(test,policy,valid)


def test_missing_uncertainty_protocol_blocks_release_and_keeps_policy_unapproved():
    test,policy,valid=reports();result=evaluate(test,policy,valid)
    assert not result['point_estimate_gates_pass']
    assert not result['proposed_point_estimate_gates']['uncertainty_protocol_frozen']
    assert not result['release_approved'] and not policy['release_approved']


def test_duplicate_test_items_rejected():
    test,policy,valid=reports();test['predictions']*=2
    with pytest.raises(ValueError,match='Duplicate evaluation id'):evaluate(test,policy,valid)
