"""Frozen, actual CPU model diagnostics; never reads reserved corpus partitions.

The supplied runtime owns its local process inside this execution namespace.
Model prompts contain only input IDs/text, never synthetic expected judgments.
All outputs/errors are preserved; fixed synthetic exact boundaries are not human gold.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.evidence import EVIDENCE_SYSTEM_PROMPT, model_output_schema, validate_batch, validate_prediction
from research.scripts.probe_phrase_evidence import evaluate


def load_suite(suite):
    if suite == 'original':
        path=ROOT/'research/fixtures/phrase_evidence_20261002.json'
        return json.loads(path.read_text()), hashlib.sha256(path.read_bytes()).hexdigest()
    record=json.loads((ROOT/'research/results/phrase_evidence_20261002.json').read_text())['held_aside_transfer']
    return record['frozen_fixture'],record['fixture_sha256']


def payload_for(row, protocol):
    return {'model':protocol['model'], 'temperature':protocol['temperature'], 'seed':protocol['seed'],
            'max_tokens':protocol['output_token_limit'], 'stream':False,
            'chat_template_kwargs':{'enable_thinking':False},
            'messages':[{'role':'system','content':protocol['prompt']},
                        {'role':'user','content':json.dumps([{'id':row['id'],'text':row['text']}],ensure_ascii=False)}],
            'response_format':{'type':'json_schema','json_schema':{'name':'phrase_evidence','strict':True,'schema':protocol['schema']}}}


def decode_response(row, output, exact_tokens):
    if not isinstance(output,dict) or len(output.get('choices',[]))!=1:
        raise ValueError('Expected one model choice')
    choice=output['choices'][0]
    if choice.get('finish_reason')!='stop':raise ValueError('Truncated or incomplete response')
    if output.get('usage',{}).get('prompt_tokens')!=exact_tokens:
        raise ValueError('Generation prompt token count differs from preflight')
    message=choice.get('message',{})
    if message.get('tool_calls') or not isinstance(message.get('content'),str):raise ValueError('Expected structured text, not tools')
    decoded=json.loads(message['content'])
    return validate_batch([{'id':row['id'],'text':row['text']}],decoded)[row['id']]


def rss_kib(pid):
    try:
        lines=Path(f'/proc/{pid}/status').read_text().splitlines()
        return int(next(line.split()[1] for line in lines if line.startswith('VmRSS:')))
    except (OSError,StopIteration,ValueError):return None


def run(runtime_file,protocol_path,output_dir):
    if output_dir.exists():raise ValueError('Use a fresh output directory; never overwrite prior outputs')
    protocol_bytes=protocol_path.read_bytes();protocol=json.loads(protocol_bytes)
    if not protocol.get('frozen_before_first_semantic_inference'):raise ValueError('Pre-register before semantic calls')
    if protocol['prompt']!=EVIDENCE_SYSTEM_PROMPT or protocol['schema']!=model_output_schema():
        raise ValueError('Serving prompt/schema changed after baseline freeze')
    suites={name:load_suite(name) for name in ('original','transfer')}
    if suites['original'][1]!=protocol['fixture_26_sha256']:raise ValueError('Original fixture changed')
    if suites['transfer'][0]!=protocol['transfer_12']['frozen_fixture']:raise ValueError('Transfer fixture changed')
    for fixture,_ in suites.values():
        if not fixture['frozen_before_first_model_call']:raise ValueError('Fixture not frozen')
        evaluate(fixture['rows'],{})
    spec=importlib.util.spec_from_file_location('fixed_cpu_runtime',runtime_file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    output_dir.mkdir(parents=True)
    results={'purpose':'Actual frozen local CPU phrase extraction; synthetic development diagnostics, not human-gold accuracy',
             'created_utc':datetime.now(timezone.utc).isoformat(),'protocol':protocol,
             'protocol_sha256':hashlib.sha256(protocol_bytes).hexdigest(),
             'runtime_wrapper_sha256':hashlib.sha256(runtime_file.read_bytes()).hexdigest(),
             'release_approved':False,'suites':{},'complete':False}
    destination=output_dir/'results.json'
    def save():destination.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    save()
    with module.LlamaRuntime(log_name='phrase_baseline_server.log') as runtime:
        results['runtime_command']=runtime.command;results['startup_seconds']=runtime.startup_seconds
        props=runtime.request('/props');results['runtime_props']=props
        actual_context=props.get('default_generation_settings',{}).get('n_ctx')
        if actual_context!=protocol['context_tokens']:raise ValueError('Actual per-slot context differs from frozen protocol')
        for name,(fixture,digest) in suites.items():
            predictions={};suite={'fixture_sha256':digest,'fixture':fixture,'attempts':[],'predictions':{},'complete':False}
            results['suites'][name]=suite;save()
            for row in fixture['rows']:
                if hashlib.sha256(protocol_path.read_bytes()).hexdigest()!=results['protocol_sha256']:raise ValueError('Protocol changed during run')
                attempt={'id':row['id'],'status':'failed','raw_response':None};started=time.monotonic()
                try:
                    body=payload_for(row,protocol)
                    token_count=runtime.exact_input_tokens(body)
                    attempt['exact_input_tokens']=token_count
                    if token_count+body['max_tokens']+16>actual_context:raise ValueError('Full-context reservation plus safety margin exceeds model context')
                    output=runtime.request('/v1/chat/completions',body,timeout=120)
                    attempt['raw_response']=output
                    predictions[row['id']]=decode_response(row,output,token_count)
                    attempt['status']='validated'
                except (OSError,ValueError,TimeoutError) as exc:
                    attempt['error']=f'{type(exc).__name__}: {exc}'
                attempt['elapsed_seconds']=time.monotonic()-started
                attempt['runtime_rss_kib']=rss_kib(runtime.proc.pid)
                suite['attempts'].append(attempt);suite['predictions']=predictions
                suite['evaluation']=evaluate(fixture['rows'],predictions);save()
                print(name,row['id'],attempt['status'],round(attempt['elapsed_seconds'],2),flush=True)
            suite['complete']=True;save()
        results['complete']=True;results['completed_utc']=datetime.now(timezone.utc).isoformat();save()
    print(json.dumps({k:v['evaluation']['totals'] for k,v in results['suites'].items()},indent=2))
    return results


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runtime',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    run(a.runtime.resolve(),a.protocol.resolve(),a.output.resolve())
