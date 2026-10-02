"""Full-document evaluation; raw accuracy is distinct from accepted-label accuracy."""
import argparse, hashlib, json, math, os, sys, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report


def wilson_interval(successes, n):
    """Marginal 95% binomial diagnostic only; ignores event/source dependence."""
    if not n:
        return None
    z=1.959963984540054;p=successes/n;den=1+z*z/n
    middle=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,middle-half),min(1.,middle+half)]


def summarize(rows):
    labels=['LEFT','CENTER','RIGHT']
    for row in rows:
        if row['gold'] not in labels+['NONPOLITICAL','UNCERTAIN']:
            raise ValueError('Unknown reference label')
        if row['raw_label'] not in labels or row['decision'] not in ['classified','abstained']:
            raise ValueError('Invalid model output')
        if ((row['decision']=='classified' and row['label'] not in labels)
                or (row['decision']=='abstained' and row['label'] is not None)):
            raise ValueError('Inconsistent decision and label')
    eligible=[r for r in rows if r['gold'] in ['LEFT','CENTER','RIGHT']]
    accepted=[r for r in eligible if r['decision']=='classified']
    negatives=[r for r in rows if r['gold']=='NONPOLITICAL']
    unknown=[r for r in rows if r['gold']=='UNCERTAIN']
    report={'n':len(rows),'eligible_n':len(eligible),'coverage':len(accepted)/len(eligible) if eligible else None,
        'accepted_n':len(accepted),'abstained_political_n':len(eligible)-len(accepted),
        'selective_accuracy':sum(r['label']==r['gold'] for r in accepted)/len(accepted) if accepted else None,
        'nonpolitical_n':len(negatives),'nonpolitical_false_label_rate':sum(r['decision']=='classified' for r in negatives)/len(negatives) if negatives else None,
        'uncertain_n':len(unknown),'uncertain_false_label_rate':sum(r['decision']=='classified' for r in unknown)/len(unknown) if unknown else None}
    report['marginal_binomial_diagnostics']={
        'method':'Wilson 95%; illustrative only, ignores source/episode dependence and repeated model selection',
        'selective_accuracy':wilson_interval(sum(r['label']==r['gold'] for r in accepted),len(accepted)),
        'coverage':wilson_interval(len(accepted),len(eligible)),
        'nonpolitical_false_label_rate':wilson_interval(sum(r['decision']=='classified' for r in negatives),len(negatives)),
        'uncertain_false_label_rate':wilson_interval(sum(r['decision']=='classified' for r in unknown),len(unknown))}
    if eligible:
        y=[r['gold'] for r in eligible];p=[r['raw_label'] for r in eligible];labels=['LEFT','CENTER','RIGHT']
        raw_f1=f1_score(y,p,labels=labels,average='macro',zero_division=0)
        raw_per_class=classification_report(y,p,labels=labels,output_dict=True,zero_division=0)
        decisions=[r['label'] if r['decision']=='classified' else 'ABSTAIN' for r in eligible]
        product_per_class=classification_report(y,decisions,labels=labels,output_dict=True,zero_division=0)
        matrix=confusion_matrix(y,decisions,labels=labels+['ABSTAIN']).tolist()[:3]
        report.update(raw_accuracy=accuracy_score(y,p),raw_macro_f1=raw_f1,raw_per_class=raw_per_class,
            macro_f1=f1_score(y,decisions,labels=labels,average='macro',zero_division=0),
            raw_confusion_order=labels,raw_confusion_matrix=confusion_matrix(y,p,labels=labels).tolist(),
            per_class=product_per_class,
            decision_confusion_rows=labels,decision_confusion_columns=labels+['ABSTAIN'],decision_confusion_matrix=matrix,
            metrics_schema='v2: macro_f1 and per_class are decision-aware; raw_* retain unthresholded metrics',
            per_class_coverage={label:sum(r['decision']=='classified' for r in eligible if r['gold']==label)/sum(r['gold']==label for r in eligible)
                                if any(r['gold']==label for r in eligible) else None for label in labels})
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--split',choices=['validation','test','stress'],required=True);p.add_argument('--mode',choices=['article','sentence','paragraph'],default='article');p.add_argument('--annotation-record',type=Path,help='Actual annotation provenance JSON, not model-generated labels.');a=p.parse_args()
    os.environ['BIASCHECK_MODEL_DIR']=str(a.model.resolve())
    from backend.model import predict_text,model_metadata
    rows=[json.loads(line) for line in a.input.read_text().splitlines() if line.strip()]
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate IDs')
    results=[];started=time.monotonic()
    for i,row in enumerate(rows):
        output=predict_text(row['text'],a.mode)
        results.append({'id':row['id'],'gold':row['label'],'source':row.get('source','unknown'),
            'source_group':row.get('source_group','unknown'),'text_sha256':hashlib.sha256(row['text'].encode()).hexdigest(),**output})
        if (i+1)%10==0:print('evaluated',i+1,flush=True)
    report={'schema_version':2,'split':a.split,'mode':a.mode,'data_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),
        'annotation_provenance':json.loads(a.annotation_record.read_text()) if a.annotation_record else None,
        'model':model_metadata(),'metrics':summarize(results),'seconds':time.monotonic()-started,'predictions':results}
    a.output.write_text(json.dumps(report,indent=2));print(json.dumps(report['metrics'],indent=2))
if __name__=='__main__':main()
