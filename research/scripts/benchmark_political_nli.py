"""Fixed hypothesis public article comparison. No independent release claim."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import torch
from transformers import AutoModelForSequenceClassification,AutoTokenizer
from sklearn.metrics import accuracy_score,f1_score,classification_report,confusion_matrix
HYPOTHESES={
 'politics':'This text is about politics.',
 'policy':'This text is about government policy.',
 'LEFT':'The author of this text supports politically liberal positions.',
 'RIGHT':'The author of this text supports politically conservative positions.',
 'CENTER':'This text reports political information without taking a political side.'}
p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
torch.set_num_threads(2);tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True);model=AutoModelForSequenceClassification.from_pretrained(a.model,local_files_only=True);model.eval()
ids=json.loads(Path('research/results/context_comparison.json').read_text())['first512']['predictions'];labels=['LEFT','CENTER','RIGHT']
report={'model':'mlburnham/Political_DEBATE_large_v1.0','revision':'1a3aff1ecb97ad93a6de598f7414b1707de7e7c3','hypotheses':HYPOTHESES,'purpose':'Same 60 public development articles; training overlap unknown; first paired-token window only','max_pair_tokens':512,'predictions':[]}
for i,item in enumerate(ids):
 d=json.loads((a.dataset/'data/jsons'/f"{item['id']}.json").read_text());text=d['content_original'].strip();scores={};start=time.monotonic()
 for offset in range(0,len(HYPOTHESES),2):
  keys=list(HYPOTHESES)[offset:offset+2];encoded=tok([text]*len(keys),[HYPOTHESES[k] for k in keys],padding=True,truncation='only_first',max_length=512,return_tensors='pt')
  with torch.inference_mode():values=model(**encoded).logits.softmax(-1)[:,0].tolist()
  scores.update(zip(keys,values))
 report['predictions'].append({'id':item['id'],'gold':item['gold'],'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'raw_label':max(labels,key=lambda k:scores[k]),'scores':scores,'seconds':time.monotonic()-start})
 a.output.write_text(json.dumps(report,indent=2));print(i+1,item['gold'],report['predictions'][-1]['raw_label'],flush=True)
y=[r['gold'] for r in report['predictions']];pred=[r['raw_label'] for r in report['predictions']]
report['metrics']={'accuracy':accuracy_score(y,pred),'macro_f1':f1_score(y,pred,labels=labels,average='macro'),'per_class':classification_report(y,pred,output_dict=True),'confusion_order':labels,'confusion_matrix':confusion_matrix(y,pred,labels=labels).tolist()};a.output.write_text(json.dumps(report,indent=2));print(json.dumps(report['metrics'],indent=2))
