"""Document-weighted window training. Uses validation only; never opens test.jsonl.

Intended for a GPU runner. Checkpoint selection by article macro F1. This does not
certify a release, train political relevance, or resolve data licensing.
"""
import argparse,hashlib,json,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
import torch
from transformers import AutoTokenizer,AutoModelForSequenceClassification,set_seed
from sklearn.metrics import f1_score,accuracy_score
from backend.model import token_windows
LABELS=['LEFT','CENTER','RIGHT']


def windows(tokenizer,text):
    ids=tokenizer(text,add_special_tokens=False,truncation=False,verbose=False)['input_ids']
    capacity=512-tokenizer.num_special_tokens_to_add(pair=False)
    result=list(token_windows(ids,capacity))
    if not result or len(result)>64:raise ValueError('Training document outside supported window limits')
    return result,len(ids)


def run(a):
    if a.output.exists() and any(a.output.iterdir()):raise ValueError('Use an empty output directory to preserve experiments')
    set_seed(a.seed);torch.set_num_threads(2)
    train=[json.loads(x) for x in (a.data/'train.jsonl').read_text().splitlines()]
    valid=[json.loads(x) for x in (a.data/'valid.jsonl').read_text().splitlines()]
    for field in ['source_group','text_sha256']:
        if {r[field] for r in train}&{r[field] for r in valid}:raise ValueError(f'Leaking {field}')
    if set(r['label'] for r in train)!=set(LABELS):raise ValueError('Training must contain all classes')
    kwargs={'revision':a.revision} if a.revision else {}
    if not Path(a.base).exists() and not a.revision:raise ValueError('Remote base requires immutable --revision')
    tokenizer=AutoTokenizer.from_pretrained(a.base,**kwargs)
    model=AutoModelForSequenceClassification.from_pretrained(a.base,num_labels=3,id2label=dict(enumerate(LABELS)),label2id={v:k for k,v in enumerate(LABELS)},**kwargs)
    device=torch.device(a.device);model.to(device);optimizer=torch.optim.AdamW(model.parameters(),lr=a.learning_rate,weight_decay=.01)
    a.output.mkdir(parents=True,exist_ok=True);best=-1.;stale=0;history=[]
    for epoch in range(a.epochs):
        model.train();indices=list(range(len(train)));random.Random(a.seed+epoch).shuffle(indices);loss_sum=0.
        for step,index in enumerate(indices):
            row=train[index];parts,total=windows(tokenizer,row['text']);optimizer.zero_grad(set_to_none=True)
            for start in range(0,len(parts),a.batch_size):
                batch=parts[start:start+a.batch_size]
                features=[{'input_ids':tokenizer.build_inputs_with_special_tokens(w)} for w,_,_,_ in batch]
                encoded=tokenizer.pad(features,padding=True,return_tensors='pt',verbose=False).to(device)
                logits=model(**encoded).logits;target=torch.full((len(batch),),LABELS.index(row['label']),dtype=torch.long,device=device)
                losses=torch.nn.functional.cross_entropy(logits,target,reduction='none')
                weights=torch.tensor([w/total for _,_,_,w in batch],device=device)
                loss=(losses*weights).sum();loss.backward();loss_sum+=loss.item()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step()
            if (step+1)%100==0:print(f'epoch {epoch+1} documents {step+1}/{len(train)}',flush=True)
        model.eval();pred=[];gold=[]
        with torch.inference_mode():
            for row in valid:
                parts,total=windows(tokenizer,row['text']);aggregate=np.zeros(3)
                for start in range(0,len(parts),a.batch_size):
                    batch=parts[start:start+a.batch_size];features=[{'input_ids':tokenizer.build_inputs_with_special_tokens(w)} for w,_,_,_ in batch]
                    logits=model(**tokenizer.pad(features,padding=True,return_tensors='pt',verbose=False).to(device)).logits.cpu().numpy()
                    for scores,(_,_,_,weight) in zip(logits,batch):aggregate+=scores*weight/total
                pred.append(LABELS[int(aggregate.argmax())]);gold.append(row['label'])
        metric=float(f1_score(gold,pred,labels=LABELS,average='macro',zero_division=0));history.append({'epoch':epoch+1,'train_loss':loss_sum/len(train),'validation_macro_f1':metric,'validation_accuracy':accuracy_score(gold,pred)})
        if metric>best:
            best=metric;stale=0;model.save_pretrained(a.output/'best',safe_serialization=True);tokenizer.save_pretrained(a.output/'best')
        else:stale+=1
        record={'arguments':{k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},'history':history,'data_sha256':{s:hashlib.sha256((a.data/f'{s}.jsonl').read_bytes()).hexdigest() for s in ['train','valid']},'release_approved':False,'limitations':['Window labels inherited from article; possible label noise','Relevance classifier not trained','Human-reviewed independent evaluation required']}
        (a.output/'training_record.json').write_text(json.dumps(record,indent=2));print(json.dumps(history[-1]),flush=True)
        if stale>=a.patience:break

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--base',required=True);p.add_argument('--revision');p.add_argument('--epochs',type=int,default=3);p.add_argument('--patience',type=int,default=2);p.add_argument('--batch-size',type=int,default=4);p.add_argument('--learning-rate',type=float,default=2e-5);p.add_argument('--seed',type=int,default=20260929);p.add_argument('--device',default='cuda' if torch.cuda.is_available() else 'cpu');run(p.parse_args())
