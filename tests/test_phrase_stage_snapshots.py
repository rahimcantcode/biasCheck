"""Historical development replay, isolated from the serving backend namespace."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'research/experiments/phrase_stages_20261002'


def test_publication_snapshot_hashes():
    manifest = json.loads((SNAPSHOT / 'publication_manifest.json').read_text())
    assert manifest['release_approved'] is False
    for record in manifest['files']:
        path = SNAPSHOT / record['path']
        assert path.resolve().is_relative_to(SNAPSHOT.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['publication_sha256']


def test_historical_pipeline_invariants_in_isolated_process():
    env = {**os.environ, 'PYTHONPATH': str(SNAPSHOT)}
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', '-q', 'tests', '--disable-socket',
         '--allow-hosts=127.0.0.1', '--allow-unix-socket'],
        cwd=SNAPSHOT, env=env, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr


def test_all_publication_metric_replays_in_isolated_process():
    code = '''
import json
from pathlib import Path
from research.scripts.probe_phrase_pipeline_v3 import evaluate_all, stable_hash
records = [Path('research/checkpoints/phrase-pipeline-v3-20261002/results.json'),
           Path('research/checkpoints/phrase-recall-v4-20261002/results.json'),
           Path('results_v5.json')]
for path in records:
    record = json.loads(path.read_text())
    assert record['release_approved'] is False
    for name, suite in record['suites'].items():
        protocol = record['protocol']
        if 'fixture_snapshots' in protocol:
            rows = protocol['fixture_snapshots'][name]['rows']
        elif name.startswith('v5_development_'):
            rows = protocol['development_fixture_snapshots'][name.removeprefix('v5_development_')]['rows']
        else:
            fixture = Path('transfer32_fixture.json')
            from hashlib import sha256
            assert sha256(fixture.read_bytes()).hexdigest() == protocol['sealed_fixture_sha256']
            rows = json.loads(fixture.read_text())['rows']
        replay = evaluate_all(rows, suite['predictions'], suite['attempts'])
        assert stable_hash(replay) == stable_hash(suite['metrics']), (str(path), name)
'''
    result = subprocess.run([sys.executable, '-c', code], cwd=SNAPSHOT,
                            env={**os.environ, 'PYTHONPATH': str(SNAPSHOT)},
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
