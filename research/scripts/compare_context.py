"""Exploratory paired comparison; public labels may overlap checkpoint training."""
import argparse,csv,json,random,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import torch
import numpy as np
from backend.model import get_tokenizer,get_model,predict_text,model_metadata
from research.scripts.evaluate import summarize
p=argparse.ArgumentParser();p.add_argument('--repository',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
items=list(csv.DictReader((a.repository/'data/splits/media/valid.tsv').open(),delimiter='\t'));random.Random(20260929).shuffle(items)
rows=[];counts={x:0 for x in ['LEFT','CENTER','RIGHT']}
for r in items:
    d=json.loads((a.repository/'data/jsons'/f"{r['ID']}.json").read_text());label=d['bias_text'].upper();text=d['content_original'].strip()
    if len(text.split())>=30 and counts[label]<20: rows.append((d,text,label));counts[label]+=1
    if len(rows)==60:break
tokenizer,model=get_tokenizer(),get_model();first=[];full=[];start=time.monotonic()
for i,(d,text,label) in enumerate(rows):
    common={'id':d['ID'],'gold':label,'source':d['source']}
    with torch.inference_mode():
        encoded=tokenizer(text,truncation=True,max_length=512,return_tensors='pt');scores=model(**encoded).logits.softmax(-1)[0].tolist()
    first.append({**common,'raw_label':model.config.id2label[max(range(3),key=lambda k:scores[k])].upper(),'probabilities':scores,'decision':'abstained','label':None})
    full.append({**common,**predict_text(text)})
    print('evaluated',i+1,flush=True)
report={'purpose':'Exploratory only; training overlap unknown','seed':20260929,'model':model_metadata(),'seconds':time.monotonic()-start,'first512':{'metrics':summarize(first),'predictions':first},'full_document':{'metrics':summarize(full),'predictions':full}}
rng=np.random.default_rng(20260929)
first_correct=np.array([r['raw_label']==r['gold'] for r in first],dtype=float)
full_correct=np.array([r['raw_label']==r['gold'] for r in full],dtype=float)
indices=rng.integers(0,len(rows),size=(10000,len(rows)))
delta=(full_correct-first_correct)[indices].mean(axis=1)
report['paired_accuracy_delta']={'full_minus_first':float((full_correct-first_correct).mean()),'bootstrap_95_percentile_ci':np.quantile(delta,[.025,.975]).tolist(),'resamples':10000,'seed':20260929,'limitations':'Unclustered exploratory interval; publisher/story dependence and training contamination not accounted for'}
a.output.write_text(json.dumps(report,indent=2));print(json.dumps({k:v['metrics'] for k,v in report.items() if k in ['first512','full_document']},indent=2))
