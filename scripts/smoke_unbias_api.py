"""Live quantized model plus real HTTP API. Bypass unrelated classifier startup only."""
import argparse,hashlib,json,os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'research/experiments/unbias_20261003'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def wait(url,proc):
    for _ in range(240):
        if proc.poll() is not None:raise RuntimeError('Owned process exited')
        try:
            with urllib.request.urlopen(url,timeout=1) as r:
                if r.status==200:return
        except OSError:pass
        time.sleep(.25)
    raise RuntimeError('Startup timeout')

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    m=json.loads((EXP/'native_runtime_manifest.json').read_text())
    binary=Path(m['runtime_server_path']);weights=Path(m['weights_path'])
    assert sha(binary)==m['runtime_server_sha256']
    assert sha(weights)==m['weights_sha256']
    print('Runtime and model checksums verified.',flush=True)
    for port in [8082,8093]:
        with socket.socket() as guard:guard.bind(('127.0.0.1',port))
    command=[str(binary),'--offline','-m',str(weights),'--alias','unbias-plus-v2','--device','none',
             '-ngl','0','-t','4','-tb','4','-c','8192','-n','2048','-np','1','-b','128','-ub','128',
             '--no-context-shift','--no-warmup','--no-webui','--host','127.0.0.1','--port','8082',
             '--no-agent','--no-ui-mcp-proxy','--reasoning','off','--temp','0','--seed','0']
    processes=[]
    try:
        with (a.output/'runtime.log').open('w') as log:
            runtime=subprocess.Popen(command,env={**os.environ,'LD_LIBRARY_PATH':str(binary.parent),'OMP_NUM_THREADS':'4'},stdout=log,stderr=log)
            processes.append(runtime);wait('http://127.0.0.1:8082/health',runtime)
        with (a.output/'api.log').open('w') as log:
            api=subprocess.Popen([sys.executable,'-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8093','--lifespan','off'],cwd=ROOT,env={**os.environ,'BIASCHECK_UNBIAS_ENABLED':'1','BIASCHECK_UNBIAS_ENDPOINT':'http://127.0.0.1:8082'},stdout=log,stderr=log)
            processes.append(api);wait('http://127.0.0.1:8093/openapi.json',api)
        report={'kind':'live_quantized_model_http_api_smoke','runtime':m,
                'limitation':'Framing endpoint only; unrelated classifier startup bypassed using lifespan off. No website or quality validation.', 'rows':[]}
        cases=json.loads((EXP/'diagnostics.json').read_text())['cases'][:2]
        for case in cases:
            start=time.monotonic()
            req=urllib.request.Request('http://127.0.0.1:8093/framing',data=json.dumps({'text':case['text']}).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=240) as r:body=json.load(r);status=r.status
            assert body['resolved_text']==case['text']
            assert all(case['text'][s['start']:s['end']]==s['text'] for s in body['spans'])
            report['rows'].append({'id':case['id'],'http_status':status,'seconds':time.monotonic()-start,'response':body})
            (a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps({'case':case['id'],'status':body['status'],'spans':len(body['spans'])}),flush=True)
    finally:
        for proc in reversed(processes):
            proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
if __name__=='__main__':main()
