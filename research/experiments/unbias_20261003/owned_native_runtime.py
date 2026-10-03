"""Launch one verified CPU-only server and stop it after diagnostic inference."""
import argparse,hashlib,json,os,resource,socket,subprocess,sys,time,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,default=HERE)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    runtime_path=HERE/'native_runtime_manifest.json';m=json.loads(runtime_path.read_text())
    p=ROOT/'research/checkpoints/unbias-runtime/bin/llama-b11349/llama-server'
    expected=json.loads((ROOT/'research/local_phrase_runtime.json').read_text())['runtime']['server_sha256']
    if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise RuntimeError('Server checksum mismatch')
    log=args.output_dir/'native_server.log';out=args.output_dir/'native_results.json';stats=args.output_dir/'native_runtime_measurement.json'
    if any(x.exists() for x in [log,out,stats]):raise RuntimeError('Refusing to overwrite run artifacts')
    command=[str(p),'--offline','-m',m['weights_path'],'--alias','unbias-plus-v2','--device','none','-ngl','0',
             '-t','4','-tb','4','-c','8192','-n','2048','-np','1','-b','128','-ub','128',
             '--no-context-shift','--no-warmup','--no-webui','--host','127.0.0.1','--port','8082',
             '--cors-origins','http://127.0.0.1:8082','--no-cors-credentials','--no-agent',
             '--no-ui-mcp-proxy','--reasoning','off','--temp','0','--seed','0']
    env={'PATH':os.defpath,'LANG':'C.UTF-8','OMP_NUM_THREADS':'4','LD_LIBRARY_PATH':str(p.parent)}
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));start=time.monotonic()
    record={'command':command,'model_revision':m['model_revision'],'peak_sampled_server_rss_bytes':0,'ready':False}
    with socket.socket() as guard:
        guard.bind(('127.0.0.1',8082))
    child=None
    with log.open('x') as lf:
        server=subprocess.Popen(command,env=env,stdout=lf,stderr=lf)
        try:
            while time.monotonic()-start<120:
                if server.poll() is not None:raise RuntimeError('Server exited; inspect native_server.log')
                try:
                    with opener.open('http://127.0.0.1:8082/health',timeout=1) as r:
                        if json.load(r).get('status')=='ok':
                            if server.poll() is not None:raise RuntimeError('Owned server exited before health verification')
                            record['ready']=True;break
                except OSError:pass
                time.sleep(.25)
            if not record['ready']:raise TimeoutError('Server startup timed out')
            record['startup_seconds']=time.monotonic()-start
            print('Verified CPU server ready; starting six native diagnostics.',flush=True)
            child=subprocess.Popen([sys.executable,str(HERE/'run_native.py'),'--runtime',str(runtime_path),'--output',str(out)],cwd=ROOT)
            while child.poll() is None:
                try:
                    for line in Path(f'/proc/{server.pid}/status').read_text().splitlines():
                        if line.startswith(('VmRSS:','VmHWM:')):
                            record['peak_sampled_server_rss_bytes']=max(record['peak_sampled_server_rss_bytes'],int(line.split()[1])*1024)
                except FileNotFoundError:pass
                if time.monotonic()-start>1500:raise TimeoutError('Whole diagnostic run exceeded25minutes')
                time.sleep(.5)
            record['runner_exit_code']=child.returncode
        finally:
            if child is not None and child.poll() is None:
                child.terminate()
                try:child.wait(timeout=10)
                except subprocess.TimeoutExpired:child.kill();child.wait()
            server.terminate()
            try:server.wait(timeout=10)
            except subprocess.TimeoutExpired:server.kill();server.wait()
            record['elapsed_seconds']=time.monotonic()-start
            record['children_peak_rss_bytes']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*1024
            stats.write_text(json.dumps(record,indent=2)+'\n')
    if record.get('runner_exit_code')!=0:raise RuntimeError('Diagnostic runner failed')
if __name__=='__main__':main()
