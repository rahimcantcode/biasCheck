"""One paired refinement pass over archived accepted spans, with all 60 outcomes."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import requests
from runtime import ROOT, checkpoint, owned_runtime, sha
from backend.unbias import client
from backend.unbias.refinement import build_refinement_request, validate_model_refinement


def infer(text, candidates, trace):
    payload = build_refinement_request(text, candidates)
    trace['payload'] = payload
    with requests.Session() as session:
        session.trust_env = False
        preflight = client._post(session, 'http://127.0.0.1:8082', '/v1/chat/completions/input_tokens', payload)
        trace['preflight'] = preflight
        count = preflight['input_tokens']
        if type(count) is not int or count < 1 or count + payload['max_tokens'] + 16 > client.CONTEXT:
            raise ValueError('context_preflight_rejected')
        output = client._post(session, 'http://127.0.0.1:8082', '/v1/chat/completions', payload)
    trace['output'] = output
    if output.get('system_fingerprint') != client.FINGERPRINT or output.get('model') != 'unbias-plus-v2':
        raise ValueError('runtime_identity_mismatch')
    usage = output.get('usage', {})
    if type(usage.get('prompt_tokens')) is not int or usage['prompt_tokens'] != count:
        raise ValueError('prompt_preflight_mismatch')
    generated = usage.get('completion_tokens')
    if type(generated) is not int or not 1 <= generated <= payload['max_tokens']:
        raise ValueError('invalid_completion_tokens')
    choices = output['choices']
    if len(choices) != 1 or choices[0]['finish_reason'] != 'stop':
        raise ValueError('incomplete_response')
    message = choices[0]['message']
    if message.get('reasoning_content') or message.get('tool_calls'):
        raise ValueError('unexpected_reasoning_or_tools')
    native = client.strict_json(message['content'])
    trace['native'] = native
    return validate_model_refinement(text, candidates, native)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    base = ROOT / 'research/data/unbias_realnews_basil'
    cases_path, baseline_path = base / 'cases.json', base / 'run_v1/results.json'
    if sha(baseline_path) != 'ed50387d6751dbe611239229913a15b629d7abeeade1c7d56e28692ae77f22a3':
        raise ValueError('Original baseline changed')
    baseline = json.loads(baseline_path.read_text())
    if sha(cases_path) != baseline['fixture_sha256']:
        raise ValueError('Original fixture changed')
    cases = json.loads(cases_path.read_text())['cases']
    if len(cases) != 60 or [c['id'] for c in cases] != [r['id'] for r in baseline['rows']]:
        raise ValueError('Baseline identities changed')
    bindings = ['backend/unbias/refinement.py', 'backend/unbias/adapter.py', 'backend/unbias/client.py',
                'research/experiments/unbias_20261004/refine.py', 'research/experiments/unbias_20261004/runtime.py']
    report = {'kind': 'paired_lexical_refinement_development', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'status_origin': 'derived_pipeline_outcome_not_http',
              'protocol_sha256': sha(Path(__file__).with_name('PROTOCOL.md')),
              'scorer_sha256_before_inference': sha(Path(__file__).with_name('compare.py')),
              'baseline_sha256': sha(baseline_path), 'fixture_sha256': sha(cases_path),
              'code_sha256': {p: sha(ROOT / p) for p in bindings},
              'release_approved': False, 'rows': []}
    with owned_runtime(args.output) as runtime:
        report['runtime'] = runtime
        for case, prior in zip(cases, baseline['rows']):
            row = deepcopy(prior)
            row.update(original_http_status=prior.get('http_status'), refinement_seconds=0,
                       status_origin='derived_pipeline_outcome_not_http')
            spans = prior.get('response', {}).get('spans', [])
            if prior.get('http_status') != 200:
                row['refinement_status'] = 'skipped_upstream_failure'
            elif not spans:
                row['refinement_status'] = 'skipped_no_spans'
            else:
                row['research_trace'] = {}
                start = time.monotonic()
                try:
                    refined = infer(case['text'], spans, row['research_trace'])
                    row['refinement_result'] = refined
                    row['refinement_status'] = 'succeeded'
                    row['response']['spans'] = refined['spans']
                    row['response']['status'] = ('partial_failure' if prior['response']['status'] == 'partial_failure'
                        else 'suggestions' if refined['spans'] else 'no_suggestions')
                except Exception as exc:
                    row.update(refinement_status='failed', http_status=503, response={},
                               refinement_error_type=type(exc).__name__, refinement_error=str(exc))
                row['refinement_seconds'] = time.monotonic() - start
            # This sum is an illustrative sequential budget, not a freshly timed end-to-end API call.
            row['illustrative_sequential_seconds'] = prior['seconds'] + row['refinement_seconds']
            report['rows'].append(row)
            checkpoint(args.output / 'results.json', report)
            print(json.dumps({'completed': len(report['rows']), 'refinement_status': row['refinement_status'],
                              'seconds': round(row['refinement_seconds'], 2)}), flush=True)
    report['code_unchanged'] = all(sha(ROOT / p) == h for p, h in report['code_sha256'].items())
    report['completed_utc'] = datetime.now(timezone.utc).isoformat()
    checkpoint(args.output / 'results.json', report)


if __name__ == '__main__':
    main()
