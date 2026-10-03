"""One frozen six-case CPU diagnostic run. Never opens reserved datasets."""
from __future__ import annotations
import argparse,hashlib,json,os,platform,resource,time
from pathlib import Path
import torch,transformers
from transformers import AutoModelForTokenClassification,AutoTokenizer
from adapter import decode_bio,span_metrics,sha

HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model-dir',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    if args.output.exists():raise SystemExit('Refusing to overwrite recorded results')
    fixture_path=HERE/'diagnostics.json';fixture=json.loads(fixture_path.read_text())
    verified=json.loads((HERE/'ner_verified_files.json').read_text())
    for rec in verified['files']:
        p=args.model_dir/rec['file'];h=hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
        if h.hexdigest()!=rec['sha256']:raise SystemExit('Model artifact hash mismatch')
    torch.set_num_threads(4);torch.set_num_interop_threads(1);torch.manual_seed(0)
    start=time.perf_counter()
    tok=AutoTokenizer.from_pretrained(args.model_dir,use_fast=True,local_files_only=True,trust_remote_code=False)
    assert tok.is_fast
    model=AutoModelForTokenClassification.from_pretrained(args.model_dir,local_files_only=True,trust_remote_code=False,weights_only=True).eval()
    assert model.config.id2label=={0:'O',1:'B-BIAS',2:'I-BIAS'}
    report={'experiment':'new synthetic fallback diagnostic; not the unavailable 30-passage comparison',
            'model_id':verified['model_id'],'revision':verified['revision'],'fixture_sha256':sha(fixture_path.read_text()),
            'runtime':{'torch':torch.__version__,'transformers':transformers.__version__,'python':platform.python_version(),
                       'device':'cpu','threads':4,'cuda_available':torch.cuda.is_available()},
            'load_seconds':time.perf_counter()-start,'human_validated':False,'rows':[]}
    for row in fixture['cases']:
        assert sha(row['text'])==row['text_sha256']
        t=time.perf_counter();result={'id':row['id'],'text':row['text'],'text_sha256':row['text_sha256']}
        try:
            encoded=tok(row['text'],return_tensors='pt',return_offsets_mapping=True,truncation=False)
            offsets=encoded.pop('offset_mapping')[0].tolist();count=encoded['input_ids'].shape[1]
            result['input_tokens']=count
            if count>min(tok.model_max_length,model.config.max_position_embeddings):raise ValueError('input_too_long')
            with torch.inference_mode():
                ids=model(**encoded).logits.argmax(-1)[0].tolist()
            labels=[model.config.id2label[x] for x in ids]
            result.update(decode_bio(row['text'],offsets,labels))
            result['raw_tokens']=[{'token_id':int(i),'offset':o,'label':l} for i,o,l in zip(encoded['input_ids'][0],offsets,labels)]
            result['exact_span_metrics']=span_metrics(row['expected_spans'],result['spans'])
            result['expected_spans']=row['expected_spans']
        except Exception as e:
            result.update(status='failure',error_type=type(e).__name__,error=str(e))
        result['elapsed_seconds']=time.perf_counter()-t
        report['rows'].append(result)
        print(json.dumps({'id':row['id'],'status':result['status'],'spans':result.get('spans'),'elapsed_seconds':result['elapsed_seconds']}),flush=True)
        report['peak_process_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        args.output.write_text(json.dumps(report,indent=2)+'\n')
    totals={k:sum(r.get('exact_span_metrics',{}).get(k,0) for r in report['rows']) for k in ['true_positive','false_positive','false_negative']}
    report['counts']={'completed':sum(r['status']!='failure' for r in report['rows']),'failed':sum(r['status']=='failure' for r in report['rows']),**totals}
    report['interpretation']='Six AI-authored synthetic cases only. Exact boundaries are diagnostic; no model ranking or general accuracy estimate. Speaker attribution is unsupported.'
    args.output.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
