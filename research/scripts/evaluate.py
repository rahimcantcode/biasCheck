"""Full-document evaluation; raw accuracy is distinct from accepted-label accuracy."""
import argparse, hashlib, json, os, sys, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report


def summarize(rows):
    eligible=[r for r in rows if r['gold'] in ['LEFT','CENTER','RIGHT']]
    accepted=[r for r in eligible if r['decision']=='classified']
    negatives=[r for r in rows if r['gold']=='NONPOLITICAL']
    report={'n':len(rows),'eligible_n':len(eligible),'coverage':len(accepted)/len(eligible) if eligible else None,
        'selective_accuracy':sum(r['label']==r['gold'] for r in accepted)/len(accepted) if accepted else None,
        'nonpolitical_n':len(negatives),'nonpolitical_false_label_rate':sum(r['decision']=='classified' for r in negatives)/len(negatives) if negatives else None}
    if eligible:
        y=[r['gold'] for r in eligible];p=[r['raw_label'] for r in eligible];labels=['LEFT','CENTER','RIGHT']
        for row in eligible:
            if row['decision'] not in {'classified','abstained'} or (row['decision']=='classified' and row['label'] not in labels) or (row['decision']=='abstained' and row['label'] is not None):
                raise ValueError('Inconsistent delivered decision and label')
        delivered=[r['label'] if r['decision']=='classified' else 'ABSTAIN' for r in eligible]
        report.update(raw_accuracy=accuracy_score(y,p),macro_f1=f1_score(y,p,labels=labels,average='macro',zero_division=0),
            confusion_order=labels,confusion_matrix=confusion_matrix(y,p,labels=labels).tolist(),
            per_class=classification_report(y,p,labels=labels,output_dict=True,zero_division=0))
        report['delivered']={
            'correct_fraction':sum(a==b for a,b in zip(y,delivered))/len(y),
            'macro_f1':f1_score(y,delivered,labels=labels,average='macro',zero_division=0),
            'per_class':classification_report(y,delivered,labels=labels,output_dict=True,zero_division=0),
            'confusion_rows':labels,'confusion_columns':labels+['ABSTAIN'],
            'confusion_matrix':confusion_matrix(y,delivered,labels=labels+['ABSTAIN']).tolist()[:3],
            'per_class_coverage':{label:sum(r['decision']=='classified' for r in eligible if r['gold']==label)/y.count(label) if y.count(label) else None for label in labels},
            'definition':'All eligible examples retained; abstentions count as false negatives for their reference class.'}
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
    report={'schema_version':1,'split':a.split,'mode':a.mode,'data_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),
        'annotation_provenance':json.loads(a.annotation_record.read_text()) if a.annotation_record else None,
        'model':model_metadata(),'metrics':summarize(results),'seconds':time.monotonic()-started,'predictions':results}
    a.output.write_text(json.dumps(report,indent=2));print(json.dumps(report['metrics'],indent=2))
if __name__=='__main__':main()
