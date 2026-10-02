"""Fixed zero-shot native UK stance-presence development evaluation.

Never opens the reserved-input or reference files during inference. Original
Proposition and Locution stay local; committed reports omit transcript text.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from research.scripts.prepare_argument_stance import evaluate_files,read_jsonl,evaluate
from backend.json_contract import strict_json_loads

MODEL='Qwen/Qwen3-4B-GGUF'
REVISION='bc640142c66e1fdd12af0bd68f40445458f3869b'
WEIGHTS_SHA='7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5'
FINGERPRINT='b11349-fb4b2737a'
SCHEMA={'type':'object','properties':{'id':{'type':'string','const':'article'},'label':{'type':'integer','enum':[0,1]}},'required':['id','label'],'additionalProperties':False}


def payload(row,prompt,model_id=MODEL):
    if set(row)!={'id','proposition','locution'} or not all(isinstance(row[k],str) for k in row):raise ValueError('Unexpected unblinded input fields')
    return {'model':model_id,'temperature':0,'seed':20261002,'stream':False,'max_tokens':64,
            'chat_template_kwargs':{'enable_thinking':False},
            'messages':[{'role':'system','content':prompt},
                        {'role':'user','content':json.dumps({'id':'article','proposition':row['proposition'],'locution':row['locution']},ensure_ascii=False)}],
            'response_format':{'type':'json_schema','json_schema':{'name':'stance_presence','strict':True,'schema':SCHEMA}}}


def decode(output,tokens):
    if not isinstance(output,dict) or output.get('system_fingerprint')!=FINGERPRINT:raise ValueError('Wrong runtime')
    usage=output.get('usage')
    if not isinstance(usage,dict) or usage.get('prompt_tokens')!=tokens:raise ValueError('Prompt-token mismatch')
    n=usage.get('completion_tokens')
    if type(n) is not int or not 0<=n<=64:raise ValueError('Bad completion token count')
    choices=output.get('choices')
    if not isinstance(choices,list) or len(choices)!=1:raise ValueError('Expected one choice')
    choice=choices[0]
    if not isinstance(choice,dict) or choice.get('finish_reason')!='stop':raise ValueError('Incomplete completion')
    message=choice.get('message')
    if not isinstance(message,dict) or message.get('tool_calls') or message.get('reasoning_content'):raise ValueError('Unexpected response fields')
    if not isinstance(message.get('content'),str):raise ValueError('Expected final JSON text')
    value=strict_json_loads(message['content'])
    if (not isinstance(value,dict) or set(value)!={'id','label'} or value['id']!='article'
            or type(value['label']) is not int or value['label'] not in (0,1)):
        raise ValueError('Invalid native-task classification')
    return value['label']


def run(prepared,protocol_path,runtime_path,output_dir,model_key="qwen3_4b"):
    catalog=json.loads((ROOT/"research/local_phrase_runtime.json").read_text())
    if model_key not in catalog["models"]:raise ValueError("Unknown pinned model")
    metadata=catalog["models"][model_key]
    if output_dir.exists():raise ValueError('Use a fresh output directory')
    protocol_bytes=protocol_path.read_bytes();protocol=json.loads(protocol_bytes)
    data_path=prepared/'dev.inputs.jsonl';data=data_path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=protocol['prepared_file_sha256']['dev.inputs.jsonl']:raise ValueError('Input is not frozen development partition')
    rows=[json.loads(s) for s in data.decode().splitlines() if s.strip()]
    prompt=protocol['zero_shot_prompt']
    if hashlib.sha256(prompt.encode()).hexdigest()!=protocol['zero_shot_prompt_sha256']:raise ValueError('Prompt changed')
    spec=importlib.util.spec_from_file_location('fixed_cpu_runtime',runtime_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    weights=runtime_path.parent/'models'/metadata['file']
    h=hashlib.sha256()
    with weights.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
    if h.hexdigest()!=metadata['sha256'] or weights.stat().st_size!=metadata['bytes']:raise ValueError('Local weights differ from frozen candidate')
    candidate={'candidate_id':model_key+'-zero-shot-native-stance-v1','model_id':metadata['model_id'],'model_revision':metadata['model_revision'],'weights_sha256':metadata['sha256'],'model_provenance':metadata,
               'prompt_sha256':protocol['zero_shot_prompt_sha256'],'decoding':{'temperature':0,'seed':20261002,'max_tokens':64,'thinking':False},
               'runtime':FINGERPRINT,'runtime_wrapper_sha256':hashlib.sha256(runtime_path.read_bytes()).hexdigest(),
               'protocol_sha256':hashlib.sha256(protocol_bytes).hexdigest(),'input_sha256':hashlib.sha256(data).hexdigest(),
               'context_tokens':4096,'schema':SCHEMA,
               'code_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),ROOT/'research/scripts/prepare_argument_stance.py',ROOT/'backend/json_contract.py',ROOT/'research/local_phrase_runtime.json']},
               'python_version':sys.version,'frozen_before_inference':True,'created_utc':datetime.now(timezone.utc).isoformat()}
    output_dir.mkdir(parents=True)
    (output_dir/'candidate.json').write_text(json.dumps(candidate,indent=2)+'\n')
    summary={'purpose':'Human-majority reference agreement on UK stance-presence DEVELOPMENT data; not absolute ideology or product accuracy',
             'candidate':candidate,'attempts':[],'complete':False,'release_approved':False}
    predicted=[]
    def save():
        (output_dir/'predictions.jsonl').write_text(''.join(json.dumps(p)+'\n' for p in predicted))
        (output_dir/'run.json').write_text(json.dumps(summary,indent=2)+'\n')
    save()
    runtime=module.LlamaRuntime(log_name='argument_stance_dev.log')
    runtime.command[runtime.command.index('-m')+1]=str(weights)
    with runtime:
        props=runtime.request('/props')
        settings=props.get('default_generation_settings') if isinstance(props,dict) else None
        if not isinstance(settings,dict) or type(settings.get('n_ctx')) is not int or settings['n_ctx']!=4096 or props.get('build_info')!=FINGERPRINT or props.get('total_slots')!=1 or Path(props.get('model_path','')).name!=weights.name:raise ValueError('Actual runtime mismatch')
        summary['runtime_command']=runtime.command;summary['startup_seconds']=runtime.startup_seconds
        for index,row in enumerate(rows):
            if hashlib.sha256(protocol_path.read_bytes()).hexdigest()!=candidate['protocol_sha256']:raise ValueError('Protocol modified during inference')
            attempt={'id':row['id'],'status':'invalid','raw_response':None};start=time.monotonic();label=None
            try:
                body=payload(row,prompt,metadata['model_id']);count=runtime.exact_input_tokens(body);attempt['prompt_tokens']=count
                if type(count) is not int or count+64+16>4096:raise ValueError('Complete input exceeds context budget')
                response=runtime.request('/v1/chat/completions',body,timeout=120)
                attempt['raw_response']=response;label=decode(response,count);attempt['status']='valid'
            except (OSError,ValueError,TypeError,TimeoutError) as exc:attempt['error']=f'{type(exc).__name__}: {exc}'
            attempt['seconds']=time.monotonic()-start;summary['attempts'].append(attempt)
            predicted.append({'id':row['id'],'label':label,'error':attempt.get('error')});save()
            if index<3 or (index+1)%25==0:print(f'evaluated {index+1}/{len(rows)}; valid {sum(x["status"]=="valid" for x in summary["attempts"])}',flush=True)
    # Reference labels are opened only after all predictions have been preserved.
    result=evaluate_files(prepared/'dev.gold.jsonl',output_dir/'predictions.jsonl',protocol_path,prepared)
    gold=read_jsonl(prepared/'dev.gold.jsonl')
    result['baselines']={f'constant_{label}':evaluate(gold,[{'id':r['id'],'label':label} for r in gold])['metrics']['all'] for label in (0,1)}
    result['balanced_random_expected_balanced_accuracy']=.5
    summary['evaluation']=result;summary['complete']=True;summary['completed_utc']=datetime.now(timezone.utc).isoformat();save()
    print(json.dumps(result['metrics']['all'],indent=2));return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--model-key',default='qwen3_4b');a=p.parse_args()
    run(a.prepared.resolve(),a.protocol.resolve(),a.runtime.resolve(),a.output.resolve(),a.model_key)
