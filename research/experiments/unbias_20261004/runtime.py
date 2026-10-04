"""Own one checksum-verified local research runtime; never reuse another server."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.smoke_unbias_api import sha, wait


@contextmanager
def owned_runtime(output):
    manifest = json.loads((ROOT / 'research/experiments/unbias_20261003/native_runtime_manifest.json').read_text())
    binary, weights = Path(manifest['runtime_server_path']), Path(manifest['weights_path'])
    if sha(binary) != manifest['runtime_server_sha256'] or sha(weights) != manifest['weights_sha256']:
        raise ValueError('Runtime or model checksum mismatch')
    with socket.socket() as guard:
        guard.bind(('127.0.0.1', 8082))
    command = [str(binary), '--offline', '-m', str(weights), '--alias', 'unbias-plus-v2',
               '--device', 'none', '-ngl', '0', '-t', '4', '-tb', '4', '-c', '8192',
               '-n', '2048', '-np', '1', '-b', '128', '-ub', '128', '--no-context-shift',
               '--no-warmup', '--no-webui', '--host', '127.0.0.1', '--port', '8082',
               '--no-agent', '--no-ui-mcp-proxy', '--reasoning', 'off', '--temp', '0', '--seed', '0']
    def stop(signum, frame):
        raise SystemExit(128 + signum)
    previous = {s: signal.signal(s, stop) for s in (signal.SIGTERM, signal.SIGHUP)}
    process = None
    record = {'manifest': manifest, 'command': command, 'owned_process_stopped': False}
    try:
        with (output / 'runtime.log').open('x') as log:
            process = subprocess.Popen(command, stdout=log, stderr=log,
                env={'PATH': os.defpath, 'LANG': 'C.UTF-8', 'OMP_NUM_THREADS': '4',
                     'LD_LIBRARY_PATH': str(binary.parent)})
            wait('http://127.0.0.1:8082/health', process)
            if process.poll() is not None:
                raise RuntimeError('Owned model process exited during startup')
            yield record
    finally:
        if process is not None:
            try:
                status = Path(f'/proc/{process.pid}/status').read_text()
                record['peak_model_rss_kib'] = int(next(l.split()[1] for l in status.splitlines() if l.startswith('VmHWM:')))
            except (OSError, StopIteration):
                pass
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            record['owned_process_stopped'] = process.poll() is not None
        for s, handler in previous.items():
            signal.signal(s, handler)


def checkpoint(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
