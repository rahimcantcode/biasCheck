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


def row(gold, accepted=True, prediction=None):
    prediction = prediction or (gold if gold in ['LEFT','CENTER','RIGHT'] else 'LEFT')
    return dict(gold=gold, raw_label=prediction, decision='classified' if accepted else 'abstained',
                label=prediction if accepted else None)


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


def test_out_of_scope_acceptance_cannot_inflate_all_accepted_reference_match():
    result = summarize([row('LEFT'), row('NONPOLITICAL'), row('UNCERTAIN')])
    assert result['political_selective_accuracy'] == 1
    assert result['political_n'] == result['political_accepted_n'] == 1
    assert result['political_coverage'] == 1
    assert result['all_accepted_n'] == 3 and result['all_input_coverage'] == 1
    assert result['all_accepted_reference_match_n'] == 1
    assert result['all_accepted_reference_match'] == pytest.approx(1/3)
    assert result['non_uncertain_accepted_n'] == 2
    assert result['non_uncertain_accepted_reference_match_n'] == 1
    assert result['accepted_reference_match_excluding_uncertain'] == .5
    assert result['uncertain_accepted_n'] == 1 and result['uncertain_acceptance_rate'] == 1
    assert result['full_population_decision_confusion_rows'] == ['LEFT','CENTER','RIGHT','NONPOLITICAL','UNCERTAIN']
    assert result['full_population_decision_confusion_columns'] == ['LEFT','CENTER','RIGHT','ABSTAIN']
    assert result['full_population_decision_confusion_matrix'] == [
        [1,0,0,0], [0,0,0,0], [0,0,0,0], [1,0,0,0], [1,0,0,0]]
    for alias, target in result['metric_aliases'].items():
        assert result[alias] == result[target]
    intervals = result['marginal_binomial_diagnostics']
    assert intervals['all_accepted_reference_match'][1] < intervals['political_selective_accuracy'][1]
    assert intervals['uncertain_false_label_rate'] == intervals['uncertain_acceptance_rate']
    assert 'not established classification errors' in result['metric_definitions']['all_accepted_reference_match']


def test_full_population_matrix_preserves_wrong_labels_and_all_abstention_rows():
    result = summarize([
        row('LEFT', prediction='RIGHT'), row('CENTER'), row('RIGHT', False),
        row('NONPOLITICAL', prediction='CENTER'), row('NONPOLITICAL', False),
        row('UNCERTAIN', prediction='RIGHT'), row('UNCERTAIN', False),
    ])
    assert result['political_selective_accuracy'] == .5
    assert result['political_coverage'] == pytest.approx(2/3)
    assert result['all_accepted_n'] == 4 and result['all_input_coverage'] == pytest.approx(4/7)
    assert result['all_accepted_reference_match'] == .25
    assert result['accepted_reference_match_excluding_uncertain'] == pytest.approx(1/3)
    assert result['non_uncertain_accepted_n'] == 3
    assert result['nonpolitical_false_label_rate'] == result['uncertain_acceptance_rate'] == .5
    assert result['full_population_decision_confusion_matrix'] == [
        [0,0,1,0], [0,1,0,0], [0,0,0,1], [0,1,0,1], [0,0,1,1]]
    assert sum(map(sum, result['full_population_decision_confusion_matrix'])) == result['n']


def test_every_reference_prediction_pair_has_a_population_matrix_cell():
    rows = [row(gold, prediction != 'ABSTAIN', None if prediction == 'ABSTAIN' else prediction)
            for gold in ['LEFT','CENTER','RIGHT','NONPOLITICAL','UNCERTAIN']
            for prediction in ['LEFT','CENTER','RIGHT','ABSTAIN']]
    result = summarize(rows)
    assert result['full_population_decision_confusion_matrix'] == [[1,1,1,1]] * 5
    assert result['n'] == 20 and result['all_accepted_n'] == 15
    assert result['political_n'] == 12 and result['political_accepted_n'] == 9
    assert result['non_uncertain_accepted_n'] == 12
    assert result['all_accepted_reference_match_n'] == 3
    assert result['political_selective_accuracy'] == pytest.approx(1/3)
    assert result['all_accepted_reference_match'] == .2
    assert result['accepted_reference_match_excluding_uncertain'] == .25
    assert result['all_input_coverage'] == result['political_coverage'] == .75


def test_all_abstained_population_has_no_accepted_precision():
    result = summarize([row(gold, False) for gold in ['LEFT','CENTER','RIGHT','NONPOLITICAL','UNCERTAIN']])
    assert result['all_accepted_n'] == result['non_uncertain_accepted_n'] == 0
    assert result['all_input_coverage'] == result['political_coverage'] == 0
    assert result['all_accepted_reference_match'] is None
    assert result['accepted_reference_match_excluding_uncertain'] is None
    assert result['political_selective_accuracy'] is None
    assert result['nonpolitical_false_label_rate'] == result['uncertain_acceptance_rate'] == 0
    assert result['full_population_decision_confusion_matrix'] == [[0,0,0,1]] * 5
    for metric in ['all_accepted_reference_match', 'accepted_reference_match_excluding_uncertain', 'political_selective_accuracy']:
        assert result['marginal_binomial_diagnostics'][metric] is None


def test_empty_population_keeps_complete_matrix_and_undefined_rates():
    result = summarize([])
    assert result['n'] == result['all_accepted_n'] == result['non_uncertain_accepted_n'] == 0
    assert result['full_population_decision_confusion_matrix'] == [[0,0,0,0]] * 5
    assert result['decision_confusion_matrix'] == [[0,0,0,0]] * 3
    for metric in ['political_selective_accuracy', 'political_coverage', 'all_input_coverage',
                   'all_accepted_reference_match', 'accepted_reference_match_excluding_uncertain',
                   'nonpolitical_false_label_rate', 'uncertain_acceptance_rate']:
        assert result[metric] is None
        assert result['marginal_binomial_diagnostics'][metric] is None


@pytest.mark.parametrize('accepted', [True, False])
def test_all_uncertain_population_does_not_invent_reference_precision(accepted):
    result = summarize([row('UNCERTAIN', accepted), row('UNCERTAIN', accepted, prediction='RIGHT')])
    assert result['political_n'] == result['political_accepted_n'] == result['non_uncertain_accepted_n'] == 0
    assert result['political_selective_accuracy'] is None and result['political_coverage'] is None
    assert result['accepted_reference_match_excluding_uncertain'] is None
    assert result['all_accepted_n'] == result['uncertain_accepted_n'] == (2 if accepted else 0)
    assert result['all_input_coverage'] == result['uncertain_acceptance_rate'] == (1 if accepted else 0)
    if accepted:
        assert result['all_accepted_reference_match'] == 0
    else:
        assert result['all_accepted_reference_match'] is None
    assert sum(map(sum, result['full_population_decision_confusion_matrix'])) == 2


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
    assert not result['proposed_point_estimate_gates']['all_population_acceptance_criterion_frozen']
    assert 'political_selective_accuracy' in result['proposed_point_estimate_gates']
    assert 'political_coverage' in result['proposed_point_estimate_gates']
    assert 'selective_accuracy' not in result['proposed_point_estimate_gates']
    assert any('Preregister an all-population' in note for note in result['limitations'])
    assert not result['release_approved'] and not policy['release_approved']


def test_provisional_political_gates_cannot_certify_all_population_acceptance():
    test, policy, valid = reports()
    test['predictions'] = []
    for gold, logits, count in [('LEFT', [10,0,0], 100), ('CENTER', [0,10,0], 100),
                               ('RIGHT', [0,0,10], 100), ('NONPOLITICAL', [0,0,0], 100),
                               ('UNCERTAIN', [10,0,0], 100)]:
        for index in range(count):
            item_id = f'test-{gold}-{index}'
            test['predictions'].append({**row(gold), 'id': item_id, 'text_sha256': item_id,
                                        'logits': logits, 'token_count': 40})
    result = evaluate(test, policy, valid)
    gates = result['proposed_point_estimate_gates']
    for gate in ['political_macro_f1', 'political_per_class_recall', 'political_selective_accuracy',
                 'political_coverage', 'nonpolitical_false_labels', 'political_sample_size']:
        assert gates[gate]
    assert result['metrics']['political_selective_accuracy'] == 1
    assert result['metrics']['all_accepted_n'] == 400
    assert result['metrics']['all_accepted_reference_match'] == .75
    assert result['metrics']['accepted_reference_match_excluding_uncertain'] == 1
    assert result['metrics']['uncertain_acceptance_rate'] == 1
    assert not gates['uncertainty_protocol_frozen']
    assert not gates['all_population_acceptance_criterion_frozen']
    assert not result['point_estimate_gates_pass']
    assert not result['release_approved'] and not policy['release_approved']


def test_duplicate_test_items_rejected():
    test,policy,valid=reports();test['predictions']*=2
    with pytest.raises(ValueError,match='Duplicate evaluation id'):evaluate(test,policy,valid)
