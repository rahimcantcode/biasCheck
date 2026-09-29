"""Synthetic deployed-API diagnostics, never human gold labels or accuracy.

Sequential requests only. Checkpoint every response; stop after three consecutive
failures. Keep outputs outside the annotation materials to avoid priming reviewers.
"""
import argparse,datetime,hashlib,json,time,urllib.request
from collections import Counter
from pathlib import Path


def run(manifest_path,output,base_url):
    manifest=json.loads(manifest_path.read_text());items=[x for x in manifest['items'] if x['kind']=='controlled_example']
    report={'schema_version':1,'purpose':'unlabeled synthetic deployment diagnostics; not an accuracy benchmark',
      'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'endpoint':base_url+'/predict',
      'pilot_id':manifest['pilot_id'],'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
      'human_reviewed':False,'server_model_provenance':'unavailable unless health supplies it','predictions':[]}
    try:
        with urllib.request.urlopen(base_url+'/health',timeout=15) as r:report['health']=json.load(r)
    except Exception as e:report['health_error']=str(e)
    failures=0;output.parent.mkdir(parents=True,exist_ok=True)
    for item in items:
        started=time.monotonic();row={'id':item['id'],'case_id':item['case_id'],'text_sha256':item['text_sha256']}
        request=urllib.request.Request(base_url+'/predict',data=json.dumps({'input':item['text'],'mode':'article'}).encode(),headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=25) as response:body=json.load(response)
            row['response']=body;failures=0
        except Exception as e:
            row['error']=str(e);failures+=1
        row['seconds']=time.monotonic()-started;report['predictions'].append(row)
        report['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        output.write_text(json.dumps(report,indent=2)+'\n');print(item['id'],'error' if 'error' in row else 'ok',round(row['seconds'],2),flush=True)
        if failures>=3:
            report['stopped_reason']='Three consecutive failures; avoid burdening deployed service';break
    report['attempted_n']=len(report['predictions']);report['error_n']=sum('error' in r for r in report['predictions'])
    distribution=Counter();high=0
    for row in report['predictions']:
        body=row.get('response',{});prediction=body.get('overall') or (body.get('results') or [{}])[0]
        if prediction.get('label'):distribution[prediction['label']]+=1
        scores=prediction.get('probabilities',{})
        if scores and max(scores.values())>=.95:high+=1
    report['observed_label_counts']=dict(distribution);report['top_score_at_least_095_n']=high
    report['limitations']=['Synthetic convenience sample, not representative of real news','No independent human labels; accuracy is not computed','Model version cannot be established from legacy health endpoint','Raw softmax scores are not probabilities of correctness']
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['predictions']},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,default=Path('research/annotation/pilot_manifest.json'));p.add_argument('--output',type=Path,required=True);p.add_argument('--base-url',default='https://bias.r4him.tech/api');a=p.parse_args();run(a.manifest,a.output,a.base_url.rstrip('/'))
