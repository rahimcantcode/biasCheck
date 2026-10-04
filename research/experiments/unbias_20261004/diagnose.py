"""Reproduce the eight previously failed/partial cases, retaining native evidence."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from unittest.mock import patch
from runtime import ROOT, checkpoint, owned_runtime, sha
from backend.unbias import client


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--structured', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    data = ROOT / 'research/data/unbias_realnews_basil'
    cases_path, baseline_path = data / 'cases.json', data / 'run_v1/results.json'
    manifest = json.loads((ROOT / 'research/experiments/unbias_20261003/realnews_basil60/sample_manifest.json').read_text())
    if sha(cases_path) != manifest['fixture_sha256']:
        raise ValueError('Original case fixture changed')
    if sha(baseline_path) != 'ed50387d6751dbe611239229913a15b629d7abeeade1c7d56e28692ae77f22a3':
        raise ValueError('Original baseline changed')
    cases = {c['id']: c for c in json.loads(cases_path.read_text())['cases']}
    original = json.loads(baseline_path.read_text())['rows']
    selected = [r for r in original if r.get('http_status') != 200 or r.get('response', {}).get('status') == 'partial_failure']
    if len(selected) != 8:
        raise ValueError('Expected exactly seven failures and one partial failure')
    bindings = ['backend/unbias/client.py', 'backend/unbias/adapter.py', 'backend/unbias/prompt.py',
                'backend/unbias/native_schema.py', 'research/experiments/unbias_20261004/diagnose.py',
                'research/experiments/unbias_20261004/runtime.py']
    report = {'kind': 'failure_reproduction_not_replacement_evaluation', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'baseline_sha256': sha(baseline_path), 'fixture_sha256': sha(cases_path),
              'code_sha256': {p: sha(ROOT / p) for p in bindings}, 'structured_output': args.structured,
              'release_approved': False, 'rows': []}
    os.environ['BIASCHECK_UNBIAS_ENABLED'] = '1'
    os.environ['BIASCHECK_UNBIAS_ENDPOINT'] = 'http://127.0.0.1:8082'
    os.environ['BIASCHECK_UNBIAS_STRUCTURED'] = '1' if args.structured else '0'
    with owned_runtime(args.output) as runtime:
        report['runtime'] = runtime
        for prior in selected:
            case = cases[prior['id']]
            row = {'id': case['id'], 'source_sha256': case['source_sha256'], 'transport': []}
            original_post = client._post
            def observe(session, endpoint, path, payload):
                value = original_post(session, endpoint, path, payload)
                row['transport'].append({'path': path, 'payload': payload, 'response': value})
                return value
            start = time.monotonic()
            try:
                with patch.object(client, '_post', side_effect=observe):
                    row['response'] = client.analyze(case['text'])
                row['status'] = row['response']['status']
            except Exception as exc:
                row.update(status='failure', error_code=str(exc), error_type=type(exc).__name__)
                row['cause_chain'] = []
                while exc is not None:
                    row['cause_chain'].append({'type': type(exc).__name__, 'detail': str(exc)})
                    exc = exc.__cause__
            row['seconds'] = time.monotonic() - start
            report['rows'].append(row)
            checkpoint(args.output / 'results.json', report)
            print(json.dumps({'completed': len(report['rows']), 'status': row['status'], 'seconds': round(row['seconds'], 2)}), flush=True)
    report['code_unchanged'] = all(sha(ROOT / p) == h for p, h in report['code_sha256'].items())
    report['completed_utc'] = datetime.now(timezone.utc).isoformat()
    checkpoint(args.output / 'results.json', report)


if __name__ == '__main__':
    main()
