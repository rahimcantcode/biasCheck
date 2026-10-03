"""Frozen native UnBias-Plus diagnostic, using a local OpenAI-compatible server.

Keep complete HTTP outputs and failures. No retry, cleaning, automatic rewrite,
semantic correction, or attribution inference. Server/model byte provenance is
supplied in the runtime manifest and must be independently verified before use.
"""
import argparse,hashlib,json,time,urllib.request,urllib.parse,urllib.error
from pathlib import Path
from adapter import adapt_unbias_v2,sha,span_metrics
from upstream_prompt import build_messages

HERE=Path(__file__).resolve().parent

def strict_json(s):
    def pairs(values):
        d={}
        for k,v in values:
            if k in d:raise ValueError('duplicate_json_key')
            d[k]=v
        return d
    def bad(v):raise ValueError('nonfinite_json_value')
    return json.loads(s,object_pairs_hook=pairs,parse_constant=bad)


def main():
    p=argparse.ArgumentParser();p.add_argument('--endpoint',default='http://127.0.0.1:8082')
    p.add_argument('--model',default='unbias-plus-v2');p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--timeout',type=float,default=180)
    a=p.parse_args()
    if a.output.exists():raise SystemExit('Refusing to overwrite results')
    if urllib.parse.urlparse(a.endpoint).hostname not in {'127.0.0.1','localhost','::1'}:
        raise SystemExit('Only loopback diagnostic endpoints supported')
    manifest=json.loads((HERE/'candidate_manifest.json').read_text())
    if sha((HERE/'upstream_prompt.py').read_text())!=manifest['prompt_file_sha256']:
        raise SystemExit('Native prompt hash mismatch')
    fixture=json.loads((HERE/'diagnostics.json').read_text());runtime=json.loads(a.runtime.read_text())
    if runtime['model_revision']!=manifest['model_revision']:raise SystemExit('Wrong candidate revision')
    weights=Path(runtime['weights_path']);h=hashlib.sha256()
    with weights.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    if h.hexdigest()!=runtime['weights_sha256']:raise SystemExit('Weight hash mismatch')
    report={'candidate':manifest,'runtime':runtime,'fixture_sha256':sha((HERE/'diagnostics.json').read_text()),
            'provenance':'New AI-authored synthetic diagnostics, not human-validated accuracy','rows':[]}
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for row in fixture['cases']:
        assert sha(row['text'])==row['text_sha256']
        start=time.perf_counter();r={'id':row['id'],'text':row['text'],'text_sha256':row['text_sha256'],'expected_spans':row['expected_spans']}
        try:
            payload={'model':a.model,'messages':build_messages(row['text']),'temperature':0,'max_tokens':manifest['max_output_tokens'],
                     'stream':False,'chat_template_kwargs':{'enable_thinking':False}}
            preflight=urllib.request.Request(a.endpoint.rstrip('/')+'/v1/chat/completions/input_tokens',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            with opener.open(preflight,timeout=30) as res:
                count=strict_json(res.read().decode())['input_tokens']
            if type(count) is not int or count<1 or count+payload['max_tokens']+16>runtime['context_tokens']:
                raise ValueError('context_reservation_overflow')
            r['exact_input_tokens']=count
            req=urllib.request.Request(a.endpoint.rstrip('/')+'/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            with opener.open(req,timeout=a.timeout) as res:
                r['raw_http_status']=res.status
                r['raw_http_body']=res.read().decode()
            output=strict_json(r['raw_http_body'])
            r['raw_response']=output
            if output.get('system_fingerprint')!=runtime['runtime_fingerprint']:
                raise ValueError('runtime_fingerprint_mismatch')
            if output.get('usage',{}).get('prompt_tokens')!=count:
                raise ValueError('prompt_preflight_mismatch')
            choices=output['choices']
            if len(choices)!=1 or choices[0]['finish_reason']!='stop':raise ValueError('incomplete_response')
            if choices[0]['message'].get('reasoning_content'):raise ValueError('unexpected_reasoning')
            result=strict_json(choices[0]['message']['content']);r['native_result']=result
            r.update(adapt_unbias_v2(row['text'],result))
            r['exact_span_metrics']=span_metrics(row['expected_spans'],r['spans'])
        except urllib.error.HTTPError as exc:
            r.update(status='failure',error_type=type(exc).__name__,error=str(exc),raw_http_status=exc.code,
                     raw_http_body=exc.read().decode('utf-8',errors='replace'))
        except Exception as exc:
            r.update(status='failure',error_type=type(exc).__name__,error=str(exc))
        r['elapsed_seconds']=time.perf_counter()-start;report['rows'].append(r)
        a.output.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:r[k] for k in ['id','status','elapsed_seconds']}) ,flush=True)
    report['counts']={'completed':sum(r['status'] in {'suggestions','no_suggestions'} for r in report['rows']),
                      'partial_failure':sum(r['status']=='partial_failure' for r in report['rows']),
                      'failed':sum(r['status']=='failure' for r in report['rows'])}
    a.output.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
