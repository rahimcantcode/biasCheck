#!/usr/bin/env python3
"""Own one CPU llama.cpp process and its client in the same execution namespace.

Usage: python research/scripts/local_cpu_runtime.py -- python /path/to/evaluation.py
Run setup_local_phrase_runtime.py first. Import LlamaRuntime for same-process
direct access. No credentials, remote tools or public listener are used.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY))
ROOT = Path(os.environ.get('BIASCHECK_LOCAL_RUNTIME_DIR', str(REPOSITORY / 'research/checkpoints/local-phrase-runtime'))).resolve()
BASE_URL = 'http://127.0.0.1:8081'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'Runtime redirects are disabled', headers, fp)

class LlamaRuntime:
    def __init__(self, log_name='owned_server.log', startup_timeout=90):
        model_key=os.environ.get('BIASCHECK_LOCAL_MODEL', 'qwen3_4b')
        catalog_bytes=(REPOSITORY/'research/local_phrase_runtime.json').read_bytes()
        catalog=json.loads(catalog_bytes)
        if model_key not in catalog['models']:
            raise ValueError('Unknown pinned model key')
        installed=json.loads((ROOT/(model_key+'.installed.json')).read_text())
        if (installed.get('manifest_sha256')!=hashlib.sha256(catalog_bytes).hexdigest()
                or installed.get('model_key')!=model_key or installed.get('release_approved') is not False
                or installed.get('model')!=catalog['models'][model_key]
                or installed.get('runtime')!=catalog['runtime']):
            raise ValueError('Installation record differs from pinned catalog')
        self.weights=ROOT/'models'/catalog['models'][model_key]['file']
        self.server=ROOT/'runtime'/catalog['runtime']['server_relative_path']
        if not self.weights.resolve().is_relative_to(ROOT) or not self.server.resolve().is_relative_to(ROOT):
            raise ValueError('Runtime/model path escapes installation directory')
        self.expected_weights_sha=catalog['models'][model_key]['sha256']
        self.expected_server_sha=catalog['runtime']['server_sha256']
        requested_log=Path(log_name)
        self.log_path=ROOT/f'{requested_log.stem}_{time.time_ns()}_{uuid.uuid4().hex[:8]}.log'
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        self.startup_timeout=startup_timeout
        self.command=[str(self.server), '--offline',
            '-m',str(self.weights), '--device','none','-ngl','0',
            '-t','4','-tb','4','-c','4096','-n','1024','-np','1', '--no-context-shift',
            '--no-warmup','--no-webui','--host','127.0.0.1','--port','8081',
            '--cors-origins','http://127.0.0.1:8081','--no-cors-credentials',
            '--no-agent','--no-ui-mcp-proxy','--reasoning','off','--temp','0','--seed','0']
        self.proc=None
        self.log=None

    def request(self,path,payload=None,timeout=120):
        request=urllib.request.Request(BASE_URL+path,
            data=None if payload is None else json.dumps(payload).encode('utf-8'),
            headers={'Content-Type':'application/json'})
        with self.opener.open(request,timeout=timeout) as response:
            return json.load(response)

    def __enter__(self):
        from research.scripts.setup_local_phrase_runtime import digest
        if digest(self.server)!=self.expected_server_sha or digest(self.weights)!=self.expected_weights_sha:
            raise ValueError('Installed runtime/model changed; refusing to launch')
        self.log=self.log_path.open('x')
        # Keep the child independent of account tokens and model/tool environment.
        env={'PATH':os.defpath, 'LANG':'C.UTF-8', 'OMP_NUM_THREADS':'4'}
        self.proc=subprocess.Popen(self.command,stdout=self.log,stderr=self.log,env=env)
        start=time.monotonic()
        try:
            while time.monotonic()-start < self.startup_timeout:
                if self.proc.poll() is not None:
                    raise RuntimeError(f'CPU runtime exited {self.proc.returncode}; see {self.log_path}')
                try:
                    if self.request('/health',timeout=1).get('status')=='ok':
                        self.startup_seconds=time.monotonic()-start
                        return self
                except (OSError,ValueError):
                    pass
                time.sleep(0.25)
            raise TimeoutError(f'CPU runtime health timeout; see {self.log_path}')
        except BaseException:
            self.__exit__(None,None,None)
            raise

    def __exit__(self,*args):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait()
        if self.log:self.log.close()

    def exact_input_tokens(self,body):
        result=self.request('/v1/chat/completions/input_tokens',body)
        count=result.get('input_tokens')
        if not isinstance(count,int) or count<0:raise ValueError('Invalid exact token count')
        return count

    def checked_chat(self,body,timeout=120):
        if body.get('stream',False):raise ValueError('Use non-streaming responses for strict validation')
        output=body.get('max_tokens')
        if not isinstance(output,int) or not 1 <= output <= 1024:
            raise ValueError('max_tokens must be explicitly within 1..1024')
        count=self.exact_input_tokens(body)
        if count+output > 4096:
            raise ValueError(f'Context reservation overflow: {count}+{output}>4096')
        start=time.monotonic()
        response=self.request('/v1/chat/completions',body,timeout=timeout)
        response['_runtime_wall_seconds']=time.monotonic()-start
        response['_exact_prompt_tokens']=count
        return response


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    command=args.command
    if command and command[0]=='--':command=command[1:]
    if not command:parser.error('Provide a child command after --')
    with LlamaRuntime() as runtime:
        print(json.dumps({'runtime_ready':BASE_URL,'startup_seconds':runtime.startup_seconds}),file=sys.stderr,flush=True)
        env=dict(os.environ,LLAMA_BASE_URL=BASE_URL,LLAMA_CPP_BASE_URL=BASE_URL,LOCAL_LLM_BASE_URL=BASE_URL)
        return subprocess.call(command,env=env)

if __name__=='__main__':raise SystemExit(main())
