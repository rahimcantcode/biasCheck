"""Frozen one-shot direction prompt experiment; sealed fixture opens after freeze."""
from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from backend.phrase_pipeline_v3 import PROMPTS, validate_extraction, extraction_schema
from research.scripts.probe_phrase_pipeline_v3 import run_case,evaluate_all,sha,stable_hash,verify_runtime_props

BASELINE=ROOT/'research/checkpoints/phrase-recall-v4-20261002/results.json'
DEFAULT=ROOT/'results_v5.json'
SOURCES=('v5_experiment.py','direction_demonstrations.json','V5_PLAN.md','tests/test_phrase_precision_v5.py',
 'backend/phrase_pipeline_v3.py','backend/evidence.py','backend/phrase_contract_v2.py',
 'research/scripts/probe_phrase_pipeline_v3.py','research/scripts/probe_phrase_contract_v2.py',
 'research/scripts/probe_phrase_evidence.py','research/scripts/probe_local_phrase_evidence.py')


def arm_prompts(baseline, demos):
    """Exactly one intervention: append direction-stage demonstration text."""
    base=deepcopy(baseline)
    suffix='\nExamples of this direction task follow. These illustrate the contract, not the current article. NO_DIRECTION is a required substantive decision when appropriate, not a processing failure.\n'
    for ex in demos:
        candidates=validate_extraction(ex['source'],{'spans':[{'text':ex['candidate'],'context':''}],'reason':'Contract demonstration'})
        content={'source':ex['source'],'candidates':candidates}
        answer={'c000':{'direction':ex['direction'],'reason':ex['reason']}}
        suffix+='INPUT: '+json.dumps(content,ensure_ascii=False)+'\nOUTPUT: '+json.dumps(answer,ensure_ascii=False)+'\n'
    suffix+='Now decide every supplied candidate from the full source in the user message.\n'
    changed=deepcopy(base);changed['direction']+=suffix
    return {'v4':base,'v5':changed}


def set_arm(protocol,arm):
    PROMPTS.clear();PROMPTS.update(deepcopy(protocol['prompts'][arm]))


def prepare(destination,runtime_file,sealed_file,sealed_sha,case_count,manifest):
    if destination.exists():raise ValueError('Refusing to overwrite frozen experiment')
    baseline=json.loads(BASELINE.read_text())
    if not baseline['complete'] or baseline['protocol']['prompts']!=PROMPTS:raise ValueError('Baseline or prompt identity mismatch')
    if sha(sealed_file)!=sealed_sha:raise ValueError('Sealed fixture hash mismatch')
    # Hashing opaque bytes is not inspecting the sealed examples or judgments.
    # No json.loads/read_text of the sealed case file occurs before run().
    demos=json.loads((ROOT/'direction_demonstrations.json').read_text())
    prompts=arm_prompts(baseline['protocol']['prompts'],demos)
    keys=('model','model_revision','file','model_bytes','model_sha256','model_provenance',
      'runtime','runtime_release','runtime_revision','context_tokens','output_token_limit',
      'temperature','seed','parallel_slots','cpu_threads','runtime_fingerprint')
    p={k:deepcopy(baseline['protocol'][k]) for k in keys}
    p.update(experiment='v5-direction-balanced-demonstrations',prompts=prompts,
      prompt_sha256={a:{s:hashlib.sha256(t.encode()).hexdigest() for s,t in v.items()} for a,v in prompts.items()},
      baseline_record_sha256=sha(BASELINE),extraction_schema=extraction_schema(),
      source_sha256={f:sha(ROOT/f) for f in SOURCES},
      runtime_wrapper_sha256=sha(runtime_file),runtime_binary_sha256=sha(runtime_file.parent/'b11349/llama-b11349/llama-server'),
      sealed_fixture_path=str(sealed_file),sealed_fixture_sha256=sealed_sha,sealed_case_count=case_count,
      sealed_manifest_path=str(manifest),sealed_manifest_sha256=sha(manifest),
      development_fixture_snapshots=deepcopy(baseline['protocol']['fixture_snapshots']),
      execution_order=['v5_development_original','v5_development_transfer','v4_sealed_transfer','v5_sealed_transfer'],
      contrast='Only append direction prompt demonstrations to v4; extraction, speaker, schemas, model, decoding, validation and metric functions unchanged',
      hypothesis='Concrete NO_DIRECTION examples may improve rejection of policy facts, unsafe scope, ambiguous views and classifier instructions while retaining valid stance recall',
      reviewer='Independent AI design review passed before freeze; new transfer authored by independent AI reviewer, not human annotation',
      sealed_use='Contents and expected judgments are not inspected by candidate engineer before freeze or between transfer arms; all cases evaluated once per arm with no adaptive tuning',
      data_status='Existing38 repeatedly reused development; new32 reviewer-authored one-use transfer diagnostic, never independent human gold',
      metric_policy='Unchanged exact span+direction+speaker and author-only fixed denominators primary; original overlap secondary; no repair or semantic rescoring',
      failure_policy='Every case retained; no stage retry or silent skip. Any stage failure invalidates final case. No resume or overwrite of semantic run.',
      context_policy='Full source per stage, exact token preflight +1024 output +16 margin <=4096, no truncation or context shift; cap16 rejects excess',
      reserved_data='No sealed89 or726 corpus data accessed',release_approved=False,
      frozen_before_first_model_call=True,frozen_utc=datetime.now(timezone.utc).isoformat())
    out={'protocol':p,'protocol_sha256':stable_hash(p),'run_started':False,'complete':False,'release_approved':False,'suites':{}}
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('x') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    return out


def verify(out,runtime_file,weights=True):
    p=out['protocol']
    if stable_hash(p)!=out['protocol_sha256'] or not p['frozen_before_first_model_call']:raise ValueError('Protocol changed')
    for f,digest in p['source_sha256'].items():
        if sha(ROOT/f)!=digest:raise ValueError('Source changed: '+f)
    if sha(BASELINE)!=p['baseline_record_sha256']:raise ValueError('Baseline changed')
    if sha(Path(p['sealed_fixture_path']))!=p['sealed_fixture_sha256']:raise ValueError('Sealed fixture changed')
    if sha(Path(p['sealed_manifest_path']))!=p['sealed_manifest_sha256']:raise ValueError('Sealed manifest changed')
    if sha(runtime_file)!=p['runtime_wrapper_sha256']:raise ValueError('Runtime wrapper changed')
    if sha(runtime_file.parent/'b11349/llama-b11349/llama-server')!=p['runtime_binary_sha256']:raise ValueError('Runtime binary changed')
    demos=json.loads((ROOT/'direction_demonstrations.json').read_text())
    base=json.loads(BASELINE.read_text())
    if arm_prompts(base['protocol']['prompts'],demos)!=p['prompts']:raise ValueError('Prompt construction changed')
    if weights:
        weight=runtime_file.parent/'models'/p['file']
        if weight.stat().st_size!=p['model_bytes'] or sha(weight)!=p['model_sha256']:raise ValueError('Model changed')


def load_sealed(out):
    if not out['protocol'].get('frozen_before_first_model_call'):raise ValueError('Must freeze candidate first')
    p=out['protocol'];fixture=json.loads(Path(p['sealed_fixture_path']).read_text())
    rows=fixture['rows']
    if len(rows)!=p['sealed_case_count'] or len({r['id'] for r in rows})!=len(rows):raise ValueError('Sealed case identity/count mismatch')
    if any(not isinstance(r['text'],str) or not isinstance(r['expected'],list) for r in rows):raise ValueError('Malformed fixture')
    old_ids={r['id'] for f in p['development_fixture_snapshots'].values() for r in f['rows']}
    if old_ids&{r['id'] for r in rows}:raise ValueError('New fixture IDs collide with development')
    # Validate reference schema and fixed denominators only; no arm outputs exist
    # here and this is not model scoring or an adaptive selection signal.
    evaluate_all(rows,{},[])
    return fixture


def run(destination,runtime_file):
    out=json.loads(destination.read_text())
    if out['run_started'] or out['complete']:raise ValueError('No repeat, overwrite or semantic-run resume')
    verify(out,runtime_file)
    p=out['protocol'];sealed=load_sealed(out)
    jobs=[('v5_development_original','v5',p['development_fixture_snapshots']['original']),
          ('v5_development_transfer','v5',p['development_fixture_snapshots']['transfer']),
          ('v4_sealed_transfer','v4',sealed),('v5_sealed_transfer','v5',sealed)]
    spec=importlib.util.spec_from_file_location('v5_runtime',runtime_file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    runtime=module.LlamaRuntime(log_name='phrase_precision_v5_server.log')
    runtime.command[runtime.command.index('-m')+1]=str(runtime_file.parent/'models'/p['file'])
    def save():destination.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    out.update(run_started=True,started_utc=datetime.now(timezone.utc).isoformat());save()
    try:
        with runtime:
            props=runtime.request('/props');verify_runtime_props(props,p)
            out.update(runtime_command=runtime.command,runtime_props=props,startup_seconds=runtime.startup_seconds)
            for name,arm,fixture in jobs:
                set_arm(p,arm)
                suite={'arm':arm,'complete':False,'attempts':[],'predictions':{},'fixture_sha256':stable_hash(fixture)}
                out['suites'][name]=suite
                for i,row in enumerate(fixture['rows']):
                    verify(out,runtime_file,weights=False)
                    if PROMPTS!=p['prompts'][arm]:raise ValueError('Active inference prompts changed')
                    if stable_hash(json.loads(destination.read_text())['protocol'])!=out['protocol_sha256']:raise ValueError('Disk protocol changed during run')
                    attempt,prediction=run_case(runtime,row,p)
                    suite['attempts'].append(attempt)
                    if prediction is not None:suite['predictions'][row['id']]=prediction
                    # Deliberately do not score or reveal sealed predictions between arms.
                    if not name.endswith('sealed_transfer'):
                        suite['metrics']=evaluate_all(fixture['rows'],suite['predictions'],suite['attempts'])
                    save();print(name,'case',i+1,'of',len(fixture['rows']),attempt['status'],flush=True)
                suite['complete']=True;save()
            # Evaluate sealed results only after both arms have completed inference.
            for name,arm,fixture in jobs:
                suite=out['suites'][name];suite['metrics']=evaluate_all(fixture['rows'],suite['predictions'],suite['attempts'])
            out.update(complete=True,completed_utc=datetime.now(timezone.utc).isoformat());save()
    except BaseException as exc:
        out.update(run_error=f'{type(exc).__name__}: {exc}',interrupted_utc=datetime.now(timezone.utc).isoformat());save();raise
    finally:
        set_arm(p,'v4')
    return out


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','run','verify'])
    parser.add_argument('--output',type=Path,default=DEFAULT);parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--sealed',type=Path);parser.add_argument('--sealed-sha');parser.add_argument('--case-count',type=int);parser.add_argument('--manifest',type=Path)
    a=parser.parse_args();runtime=a.runtime.resolve()
    if a.action=='prepare':
        if not all([a.sealed,a.sealed_sha,a.case_count,a.manifest]):parser.error('prepare requires sealed path/hash/count/manifest')
        result=prepare(a.output.resolve(),runtime,a.sealed.resolve(),a.sealed_sha,a.case_count,a.manifest.resolve())
    elif a.action=='run':result=run(a.output.resolve(),runtime)
    else:result=json.loads(a.output.read_text());verify(result,runtime)
    print(json.dumps({'complete':result['complete'],'protocol_sha256':result['protocol_sha256']},indent=2))
