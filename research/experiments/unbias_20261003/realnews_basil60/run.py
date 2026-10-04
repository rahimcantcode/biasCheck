"""Run the frozen natural-news sample through the unchanged local HTTP API."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from scripts.smoke_unbias_api import sha, wait


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((HERE / 'sample_manifest.json').read_text())
    assert sha(args.cases) == manifest['fixture_sha256']
    assert sha(HERE / 'PROTOCOL.md') == manifest['protocol_sha256']
    cases = json.loads(args.cases.read_text())['cases']
    assert len(cases) == 60 and len({c['event_id'] for c in cases}) == 60
    runtime_manifest = json.loads((HERE.parent / 'native_runtime_manifest.json').read_text())
    binary = Path(runtime_manifest['runtime_server_path'])
    weights = Path(runtime_manifest['weights_path'])
    assert sha(binary) == runtime_manifest['runtime_server_sha256']
    assert sha(weights) == runtime_manifest['weights_sha256']
    print('Frozen sample, runtime, and weight checksums verified.', flush=True)
    for port in [8082, 8093]:
        with socket.socket() as guard:
            guard.bind(('127.0.0.1', port))
    command = [str(binary), '--offline', '-m', str(weights), '--alias', 'unbias-plus-v2',
               '--device', 'none', '-ngl', '0', '-t', '4', '-tb', '4', '-c', '8192',
               '-n', '2048', '-np', '1', '-b', '128', '-ub', '128', '--no-context-shift',
               '--no-warmup', '--no-webui', '--host', '127.0.0.1', '--port', '8082',
               '--no-agent', '--no-ui-mcp-proxy', '--reasoning', 'off', '--temp', '0', '--seed', '0']
    bindings = ['backend/main.py', 'backend/unbias/adapter.py', 'backend/unbias/client.py',
                'backend/unbias/prompt.py', str((HERE / 'run.py').relative_to(ROOT)),
                str((HERE / 'prepare.py').relative_to(ROOT))]
    report = {
        'kind': 'basil60_published_human_reference_http_evaluation',
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'fixture_sha256': manifest['fixture_sha256'],
        'protocol_sha256': manifest['protocol_sha256'],
        'model_id': runtime_manifest['model_id'], 'model_revision': runtime_manifest['model_revision'],
        'weights_sha256': runtime_manifest['weights_sha256'],
        'runtime_server_sha256': runtime_manifest['runtime_server_sha256'],
        'runtime_fingerprint': runtime_manifest['runtime_fingerprint'],
        'source_bindings': {f: sha(ROOT / f) for f in bindings},
        'limitation': 'Single-sentence inputs, published human references with broader source context; '
                      'training independence unknown; unrelated classifier lifespan bypassed; no production validation.',
        'release_approved': False, 'rows': [],
    }
    processes = []
    handles = []
    start_all = time.monotonic()

    def checkpoint():
        target = args.output / 'results.json'
        tmp = target.with_suffix('.tmp')
        tmp.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
        tmp.replace(target)

    try:
        runtime_log = (args.output / 'runtime.log').open('w')
        handles.append(runtime_log)
        runtime = subprocess.Popen(command, env={**os.environ, 'LD_LIBRARY_PATH': str(binary.parent),
                                                'OMP_NUM_THREADS': '4'},
                                   stdout=runtime_log, stderr=runtime_log)
        processes.append(runtime)
        wait('http://127.0.0.1:8082/health', runtime)
        api_log = (args.output / 'api.log').open('w')
        handles.append(api_log)
        api = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host',
                                '127.0.0.1', '--port', '8093', '--lifespan', 'off'], cwd=ROOT,
                               env={**os.environ, 'BIASCHECK_UNBIAS_ENABLED': '1',
                                    'BIASCHECK_UNBIAS_ENDPOINT': 'http://127.0.0.1:8082'},
                               stdout=api_log, stderr=api_log)
        processes.append(api)
        wait('http://127.0.0.1:8093/openapi.json', api)
        report['startup_seconds'] = time.monotonic() - start_all
        for case in cases:
            start = time.monotonic()
            row = {'id': case['id'], 'source_sha256': case['source_sha256']}
            request = urllib.request.Request('http://127.0.0.1:8093/framing',
                data=json.dumps({'text': case['text']}).encode(), headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(request, timeout=240) as response:
                    body = json.load(response)
                    row['http_status'] = response.status
                assert body['resolved_text'] == case['text']
                assert body['source_sha256'] == case['source_sha256']
                assert all(case['text'][s['start']:s['end']] == s['text'] for s in body['spans'])
                row['response'] = body
            except urllib.error.HTTPError as exc:
                row.update(http_status=exc.code, error_body=exc.read().decode(errors='replace'))
            except Exception as exc:
                row.update(error_type=type(exc).__name__, error=str(exc))
            row['seconds'] = time.monotonic() - start
            report['rows'].append(row)
            checkpoint()
            print(json.dumps({'completed': len(report['rows']), 'id': case['id'],
                              'status': row.get('response', {}).get('status', 'failure'),
                              'spans': len(row.get('response', {}).get('spans', [])),
                              'seconds': round(row['seconds'], 2)}), flush=True)
        report['completed_utc'] = datetime.now(timezone.utc).isoformat()
        report['total_seconds_including_startup'] = time.monotonic() - start_all
    finally:
        for process in reversed(processes):
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for handle in handles:
            handle.close()
        report['owned_processes_stopped'] = all(p.poll() is not None for p in processes)
        checkpoint()


if __name__ == '__main__':
    main()
