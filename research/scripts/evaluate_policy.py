"""Offline candidate threshold evaluation. Never writes an approved policy."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from research.scripts.evaluate import summarize
from research.scripts.report_contract import require_matching_reports

def point_estimate_gates(metrics):
    delivered=metrics.get('delivered',{})
    return {'raw_accuracy':(metrics.get('raw_accuracy') or 0)>=.9,
      'macro_f1':metrics.get('macro_f1',0)>=.85,
      'per_class_recall':all(metrics.get('per_class',{}).get(k,{}).get('recall',0)>=.8 for k in ['LEFT','CENTER','RIGHT']),
      'delivered_macro_f1':delivered.get('macro_f1',0)>=.85,
      'delivered_per_class_recall':all(delivered.get('per_class',{}).get(k,{}).get('recall',0)>=.8 for k in ['LEFT','CENTER','RIGHT']),
      'selective_accuracy':(metrics.get('selective_accuracy') or 0)>=.9,
      'coverage':(metrics.get('coverage') or 0)>=.8,
      'nonpolitical_false_labels':metrics['nonpolitical_n']>=100 and metrics['nonpolitical_false_label_rate']<=.05,
      'political_sample_size':metrics['eligible_n']>=300}

def evaluate(report,policy,validation):
    require_matching_reports(report,validation)
    from backend.model import validate_policy,classify_scores
    validate_policy(policy,report['model'])
    if report['split']!='test' or validation['split']!='validation':raise ValueError('Separate test and validation reports required')
    if policy['calibration_data_sha256']!=validation['data_sha256']:raise ValueError('Wrong calibration dataset')
    if report['data_sha256']==validation['data_sha256']:raise ValueError('Test and validation are identical')
    for field in ['id','text_sha256']:
        if {r[field] for r in report['predictions']}&{r[field] for r in validation['predictions']}:raise ValueError(f'Test/validation overlap: {field}')
    if report['mode'] not in policy['validated_modes']:raise ValueError('Mode not calibrated')
    # In-memory simulation only. The source policy stays unapproved on disk.
    candidate={**policy,'release_approved':True};rows=[]
    labels={int(k):v for k,v in report['model']['id2label'].items()}
    for row in report['predictions']:
        scores,reason=classify_scores(row['logits'],row['token_count'],report['mode'],candidate)
        rows.append({**row,'label':labels[int(scores.argmax())] if reason is None else None,'decision':'classified' if reason is None else 'abstained','reason':reason})
    metrics=summarize(rows)
    unknown=[r for r in rows if r['gold']=='UNCERTAIN']
    metrics['uncertain_n']=len(unknown)
    metrics['uncertain_false_label_rate']=sum(r['decision']=='classified' for r in unknown)/len(unknown) if unknown else None
    requirements=point_estimate_gates(metrics)
    return {'metrics':metrics,'proposed_point_estimate_gates':requirements,'point_estimate_gates_pass':all(requirements.values()),'release_approved':False,
      'limitations':['Requires confidence intervals, source/event/time leakage review, per-slice review and operational validation before approval','Provenance fields are supplied assertions requiring human audit'],'predictions':rows}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',type=Path,required=True);p.add_argument('--validation',type=Path,required=True);p.add_argument('--policy',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=evaluate(json.loads(a.test.read_text()),json.loads(a.policy.read_text()),json.loads(a.validation.read_text()))
    result['input_sha256']={k:hashlib.sha256(getattr(a,k).read_bytes()).hexdigest() for k in ['test','validation','policy']}
    a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result['metrics'],indent=2))
