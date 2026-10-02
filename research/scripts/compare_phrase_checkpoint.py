"""Freeze and compare one new checkpoint with the unchanged v2 phrase contract."""
import argparse
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from backend.phrase_contract_v2 import PROMPT,model_output_schema,validate_v2_completion
from research.scripts.probe_phrase_contract_v2 import boundary_metrics,payload_for
from research.scripts.probe_phrase_evidence import evaluate
from research.scripts.probe_local_phrase_evidence import rss_kib


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda:source.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def run(model_manifest,runtime_path,prior_path,output_dir):
    if output_dir.exists():raise ValueError('Use a new run directory')
    metadata=json.loads(model_manifest.read_text());prior=json.loads(prior_path.read_text())
    protocol=deepcopy(prior['protocol'])
    if protocol['prompt']!=PROMPT or protocol['schema']!=model_output_schema():raise ValueError('Comparator prompt/schema mismatch')
    weights=runtime_path.parent/'models'/metadata['file']
    if weights.stat().st_size!=metadata['bytes'] or sha(weights)!=metadata['sha256']:raise ValueError('Wrong new checkpoint')
    protocol.update(model=metadata['model_id'],model_revision=metadata['model_revision'],file=metadata['file'],
                    model_sha256=metadata['sha256'],model_bytes=metadata['bytes'],model_provenance=metadata,
                    chat_template='New checkpoint embedded template; non-thinking instruction model; reasoning off',
                    checkpoint_comparison='Same v2 prompt/schema/decoding/runtime; checkpoint, publisher quantization and its embedded template change',
                    comparator_record_sha256=sha(prior_path),frozen_utc=datetime.now(timezone.utc).isoformat(),
                    code_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'backend/phrase_contract_v2.py',ROOT/'backend/evidence.py',ROOT/'research/scripts/probe_phrase_contract_v2.py',ROOT/'research/scripts/probe_phrase_evidence.py',ROOT/'research/scripts/probe_local_phrase_evidence.py']},
                    runtime_wrapper_sha256=sha(runtime_path),release_approved=False)
    record={'purpose':'Controlled checkpoint comparison on already-used synthetic DEVELOPMENT diagnostics, not independent accuracy',
            'protocol':protocol,'protocol_sha256':hashlib.sha256(json.dumps(protocol,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
            'suites':{},'complete':False,'release_approved':False}
    output_dir.mkdir(parents=True);out=output_dir/'results.json'
    def save():out.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    save()
    spec=importlib.util.spec_from_file_location('fixed_cpu_runtime',runtime_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    runtime=module.LlamaRuntime(log_name='instruct2507_phrase_comparison.log')
    runtime.command[runtime.command.index('-m')+1]=str(weights)
    with runtime:
        props=runtime.request('/props')
        if props.get('default_generation_settings',{}).get('n_ctx')!=4096 or props.get('build_info')!=protocol['runtime_fingerprint'] or props.get('total_slots')!=1:raise ValueError('Runtime mismatch')
        if Path(props.get('model_path','')).name!=weights.name:raise ValueError('Server reports a different checkpoint')
        record.update(runtime_command=runtime.command,runtime_props=props,startup_seconds=runtime.startup_seconds)
        for name,fixture in protocol['fixture_snapshots'].items():
            predictions={};suite={'attempts':[],'predictions':{},'complete':False,'status':'development'};record['suites'][name]=suite
            for row in fixture['rows']:
                started=time.monotonic();attempt={'id':row['id'],'model_input_id':'article','status':'failed','raw_response':None}
                try:
                    body=payload_for(row,protocol);count=runtime.exact_input_tokens(body);attempt['exact_input_tokens']=count
                    if type(count) is not int or count+body['max_tokens']+16>4096:raise ValueError('Context budget overflow')
                    result=runtime.request('/v1/chat/completions',body,timeout=120);attempt['raw_response']=result
                    predictions[row['id']]=validate_v2_completion(row['text'],result,count,4096,body['max_tokens'],protocol['runtime_fingerprint']);attempt['status']='validated'
                except (OSError,ValueError,TypeError,TimeoutError,RecursionError) as exc:attempt['error']=f'{type(exc).__name__}: {exc}'
                attempt.update(elapsed_seconds=time.monotonic()-started,runtime_rss_kib=rss_kib(runtime.proc.pid))
                suite['attempts'].append(attempt);suite['predictions']=predictions;suite['evaluation']=evaluate(fixture['rows'],predictions);suite['secondary']=boundary_metrics(fixture['rows'],predictions);save()
                print(name,row['id'],attempt['status'],round(attempt['elapsed_seconds'],2),flush=True)
            suite['complete']=True;save()
        record.update(complete=True,completed_utc=datetime.now(timezone.utc).isoformat());save()
    print(json.dumps({k:v['evaluation']['totals'] for k,v in record['suites'].items()},indent=2));return record

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model-manifest',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--prior',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    run(a.model_manifest.resolve(),a.runtime.resolve(),a.prior.resolve(),a.output.resolve())
