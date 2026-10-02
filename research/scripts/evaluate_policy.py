"""Offline candidate threshold evaluation. Never writes an approved policy."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.model import validate_policy,classify_scores
from research.scripts.evaluate import summarize


def evaluate(report,policy,validation):
    validate_policy(policy,report['model'])
    validate_policy(policy,validation['model'])
    if report['model']['id2label']!=validation['model']['id2label']:raise ValueError('Calibration label mapping mismatch')
    if report['split']!='test' or validation['split']!='validation':raise ValueError('Separate test and validation reports required')
    for item in [report,validation]:
        record=item.get('annotation_provenance') or {}
        if not record.get('human_reviewed') or not record.get('reference'):raise ValueError('Actual human annotation provenance required')
    if policy['calibration_data_sha256']!=validation['data_sha256']:raise ValueError('Wrong calibration dataset')
    if report['data_sha256']==validation['data_sha256']:raise ValueError('Test and validation are identical')
    if report['mode']!=validation['mode']:raise ValueError('Test and calibration modes must match')
    if validation['mode'] not in policy['validated_modes']:raise ValueError('Calibration mode not validated')
    for field in ['id','text_sha256']:
        for item in [report,validation]:
            values=[r[field] for r in item['predictions']]
            if len(values)!=len(set(values)):raise ValueError(f'Duplicate evaluation {field}')
        if {r[field] for r in report['predictions']}&{r[field] for r in validation['predictions']}:raise ValueError(f'Test/validation overlap: {field}')
    if report['mode'] not in policy['validated_modes']:raise ValueError('Mode not calibrated')
    # In-memory simulation only. The source policy stays unapproved on disk.
    candidate={**policy,'release_approved':True};rows=[]
    labels={int(k):v for k,v in report['model']['id2label'].items()}
    for row in report['predictions']:
        scores,reason=classify_scores(row['logits'],row['token_count'],report['mode'],candidate)
        rows.append({**row,'label':labels[int(scores.argmax())] if reason is None else None,
                     'decision':'classified' if reason is None else 'abstained','reason':reason,
                     'probabilities':{labels[i]:float(score) for i,score in enumerate(scores)},
                     'calibrated':True,'policy_simulation':True})
    metrics=summarize(rows)
    requirements={'political_macro_f1':(metrics.get('political_macro_f1') or 0)>=.85,'political_per_class_recall':all(metrics.get('political_per_class',{}).get(k,{}).get('recall',0)>=.8 for k in ['LEFT','CENTER','RIGHT']),
      'political_selective_accuracy':(metrics.get('political_selective_accuracy') or 0)>=.9,'political_coverage':(metrics.get('political_coverage') or 0)>=.8,
      'nonpolitical_false_labels':metrics['nonpolitical_n']>=100 and metrics['nonpolitical_false_label_rate']<=.05,
      'political_sample_size':metrics['political_n']>=300,
      # No post-hoc tolerance may be invented after seeing final-test outcomes.
      # Both intentionally stay false until reviewed all-population and uncertainty criteria are frozen.
      'uncertainty_protocol_frozen':False,
      'all_population_acceptance_criterion_frozen':False}
    return {'metrics':metrics,'proposed_point_estimate_gates':requirements,'point_estimate_gates_pass':all(requirements.values()),'release_approved':False,
      'limitations':['Point-estimate goals are provisional, not evidence that population error limits pass',
                     'Preregister an all-population accepted-label criterion and uncertainty acceptance treatment before final testing; no threshold is supplied here',
                     'UNCERTAIN is not reliable negative gold; strict all-accepted reference match is not established correctness on those items',
                     'Metrics depend on the evaluation mix and do not establish representative traffic performance',
                     'Uncertainty tolerance, interval rules, per-class supports and independent cluster counts must be frozen before final testing',
                     'Requires confidence intervals, source/event/time leakage review, per-slice review and operational validation before approval','Provenance fields are supplied assertions requiring human audit'],'predictions':rows}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',type=Path,required=True);p.add_argument('--validation',type=Path,required=True);p.add_argument('--policy',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=evaluate(json.loads(a.test.read_text()),json.loads(a.policy.read_text()),json.loads(a.validation.read_text()))
    result['input_sha256']={k:hashlib.sha256(getattr(a,k).read_bytes()).hexdigest() for k in ['test','validation','policy']}
    a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result['metrics'],indent=2))
