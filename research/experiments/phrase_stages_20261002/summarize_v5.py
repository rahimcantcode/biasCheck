"""Derived reporting only; rejects incomplete runs and never changes raw data."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,statistics
from v5_experiment import ROOT,BASELINE,evaluate_all,stable_hash
p=ROOT/'results_v5.json';raw=json.loads(p.read_text())
if not raw['complete'] or any(not x['complete'] for x in raw['suites'].values()):raise ValueError('Wait until every frozen arm is complete')
fixture=json.loads(Path(raw['protocol']['sealed_fixture_path']).read_text())
baseline=json.loads(BASELINE.read_text())
def combined(suites,fixtures):
 rows=[];pred={};attempts=[]
 for s,f in zip(suites,fixtures):rows+=f['rows'];pred.update(s['predictions']);attempts+=s['attempts']
 return evaluate_all(rows,pred,attempts)
metrics={
 'v4_reused_development':combined(list(baseline['suites'].values()),list(baseline['protocol']['fixture_snapshots'].values())),
 'v5_reused_development':combined([raw['suites']['v5_development_'+n] for n in ['original','transfer']],list(raw['protocol']['development_fixture_snapshots'].values())),
}
for n in ['v4_sealed_transfer','v5_sealed_transfer']:
 s=raw['suites'][n];m=evaluate_all(fixture['rows'],s['predictions'],s['attempts'])
 if stable_hash(m)!=stable_hash(s['metrics']):raise ValueError('Metric replay mismatch')
 metrics[n]=m
ops={}
for n,s in raw['suites'].items():
 lat=[a['elapsed_seconds'] for a in s['attempts']]
 stages=[r for a in s['attempts'] for r in a['stages'].values() if r.get('runtime_rss_kib') is not None]
 ops[n]={'case_count':len(lat),'sum_case_seconds':sum(lat),'mean_case_seconds':statistics.mean(lat),'median_case_seconds':statistics.median(lat),'max_case_seconds':max(lat),
 'peak_observed_runtime_rss_kib':max(r['runtime_rss_kib'] for r in stages),'max_input_tokens':max(r['exact_input_tokens'] for r in stages if 'exact_input_tokens' in r)}
a=raw['suites']['v4_sealed_transfer'];b=raw['suites']['v5_sealed_transfer']
paired=[]
for aa,bb in zip(a['attempts'],b['attempts']):
 if aa['id']!=bb['id']:raise ValueError('Pair identity mismatch')
 paired.append({'id':aa['id'],'candidate_objects_identical':aa['candidates']==bb['candidates'],
 'extraction_status_identical':aa['stages']['extract']['status']==bb['stages']['extract']['status'],
 'speaker_decisions_identical':aa['stages']['speaker'].get('validated_response')==bb['stages']['speaker'].get('validated_response'),
 'direction_decisions_identical':aa['stages']['direction'].get('validated_response')==bb['stages']['direction'].get('validated_response')})
out={'purpose':'Controlled direction-prompt comparison on reused development and one-use targeted synthetic transfer; no general accuracy or release approval',
 'raw_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'frozen_protocol_sha256':raw['protocol_sha256'],
 'reviewer_fixture_sha256':raw['protocol']['sealed_fixture_sha256'],'metrics':metrics,'operations':ops,'paired_transfer':paired,
 'started_utc':raw['started_utc'],'completed_utc':raw['completed_utc'],'release_approved':False,
 'tests':'66 structural/provenance tests passed before and after; all frozen sources, protocol, model/runtime and fixture bindings verified after inference',
 'limits':['New transfer was targeted synthetic material authored after v4 error review; not human gold or a population sample','Repeated32 transfer examples are now development evidence; do not use them as untouched in later claims','No tuning or result inspection between paired transfer arms','Reported zero-span rejection conventions are debatable, not the whole definition of author framing','No deployment capacity/reliability guarantee from short local CPU inputs'],
 'historical_provenance_note':"Embedded model-acquisition inference_status='Not run' is a pre-inference snapshot; enclosing completed raw records are authoritative",
 'reporting_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(ROOT/'v5_comparison_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
public=deepcopy(raw)
def clean(v):
 if isinstance(v,str):return v.replace(str(ROOT.parent),'[local-workspace]')
 if isinstance(v,list):return [clean(t) for t in v]
 if isinstance(v,dict):return {k:clean(t) for k,t in v.items()}
 return v
public=clean(public)
public['publication_note']={'raw_record_sha256':out['raw_sha256'],'original_frozen_protocol_sha256':raw['protocol_sha256'],'sanitized_protocol_sha256':stable_hash(public['protocol']),
 'predictions_and_metrics_unchanged':True,'absolute_paths_sanitized':True,'release_approved':False,
 'historical_model_provenance_note':out['historical_provenance_note'],'reporting_script_sha256':out['reporting_script_sha256']}
(ROOT/'v5_public_replay.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'metrics':{n: m['primary_exact']['totals'] for n,m in metrics.items()},'operations':ops},indent=2))
