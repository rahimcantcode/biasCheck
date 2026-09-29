"""Guard hypotheses designed after observing v1 failures. Development only, not held out."""
import argparse,hashlib,json,time
from pathlib import Path
import torch
from transformers import AutoModelForSequenceClassification,AutoTokenizer
HYPOTHESES={
 'mixed':'The author endorses a combination of both liberal and conservative political positions.',
 'specific':'The author advocates a specific ideological position on government policy.',
 'everyday':'This text is mainly about everyday life rather than politics.'}

p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
torch.set_num_threads(2);tok=AutoTokenizer.from_pretrained(a.model,local_files_only=True)
model,info=AutoModelForSequenceClassification.from_pretrained(a.model,local_files_only=True,output_loading_info=True)
assert not any(info.get(k) for k in ['missing_keys','unexpected_keys','mismatched_keys','error_msgs']),info
assert model.config.id2label[0]=='entailment';model.eval()
items=[x for x in json.loads(Path('research/annotation/pilot_manifest.json').read_text())['items'] if x['kind']=='controlled_example']
report={'model':'mlburnham/Political_DEBATE_large_v1.0','revision':'1a3aff1ecb97ad93a6de598f7414b1707de7e7c3','hypotheses':HYPOTHESES,'purpose':'Unlabeled controlled development examples, not accuracy','predictions':[]}
for item in items:
 start=time.monotonic();scores={}
 for offset in range(0,len(HYPOTHESES),2):
  keys=list(HYPOTHESES)[offset:offset+2];inputs=tok([item['text']]*len(keys),[HYPOTHESES[k] for k in keys],padding=True,truncation='only_first',max_length=512,return_tensors='pt')
  with torch.inference_mode():values=model(**inputs).logits.softmax(-1)[:,0].tolist()
  scores.update(zip(keys,values))
 result={'id':item['id'],'case_id':item['case_id'],'text_sha256':item['text_sha256'],'scores':scores,'seconds':time.monotonic()-start};report['predictions'].append(result)
 a.output.write_text(json.dumps(report,indent=2));print(item['case_id'],{k:round(v,3) for k,v in scores.items()},flush=True)
