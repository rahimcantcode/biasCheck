"""Pre-registered, preserved v2 development diagnostics on exactly the baseline 38.

Prepare freezes the record before model calls. Run refuses changed frozen code,
fixtures, protocol, model/runtime hashes, or resumed/overwritten semantic runs.
No reserved examples, user credentials, account tools, or external inference.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.evidence import validate_prediction
from backend.phrase_contract_v2 import (CONTRACT, PROMPT, model_output_schema,
                                       recover_unique_quotes, validate_v2_completion)
from research.scripts.probe_phrase_evidence import evaluate
from research.scripts.probe_local_phrase_evidence import rss_kib

BASELINE = ROOT / 'research/checkpoints/qwen3-4b-phrase-baseline-20261002/run-001/results.json'
DEFAULT_OUTPUT = ROOT / 'research/checkpoints/phrase-contract-v2-new-run.json'
OWN_FILES = ('backend/phrase_contract_v2.py', 'research/scripts/probe_phrase_contract_v2.py', 'tests/test_phrase_contract_v2.py')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def boundary_metrics(rows, predictions):
    """Secondary only: labeled+attributed IoU>=.5 maximum-cardinality matching.

    Exact metrics stay primary. A high overlap score does not certify negation,
    speaker attribution, or minimality. All missing/invalid cases stay in totals.
    """
    totals = {'cases': len(rows), 'covered_cases': len(predictions), 'expected_spans': 0,
              'predicted_spans': 0, 'matched_spans': 0, 'all_spans_overlap_matched_cases': 0,
              'expected_labeled_characters': 0, 'predicted_labeled_characters': 0,
              'matched_labeled_characters': 0}
    cases = []
    for row in rows:
        want = validate_prediction(row['text'], {'reason': 'Frozen development expectation',
            'spans': [{**s, 'reason': 'Frozen development expectation'} for s in row['expected']]})
        got = validate_prediction(row['text'], predictions[row['id']]) if row['id'] in predictions else []
        edges = []
        for predicted in got:
            edges.append([j for j, expected in enumerate(want)
                if predicted['label'] == expected['label'] and predicted['attribution'] == expected['attribution']
                and max(0, min(predicted['end'], expected['end']) - max(predicted['start'], expected['start'])) /
                (max(predicted['end'], expected['end']) - min(predicted['start'], expected['start'])) >= 0.5])
        matched = {}
        def assign(i, visited):
            for j in edges[i]:
                if j in visited:
                    continue
                visited.add(j)
                if j not in matched or assign(matched[j], visited):
                    matched[j] = i
                    return True
            return False
        for i in range(len(got)):
            assign(i, set())
        want_chars = {(s['label'], s['attribution'], c) for s in want for c in range(s['start'], s['end'])}
        got_chars = {(s['label'], s['attribution'], c) for s in got for c in range(s['start'], s['end'])}
        totals['expected_spans'] += len(want)
        totals['predicted_spans'] += len(got)
        totals['matched_spans'] += len(matched)
        totals['all_spans_overlap_matched_cases'] += int(row['id'] in predictions and len(matched) == len(want) == len(got))
        totals['expected_labeled_characters'] += len(want_chars)
        totals['predicted_labeled_characters'] += len(got_chars)
        totals['matched_labeled_characters'] += len(want_chars & got_chars)
        cases.append({'id': row['id'], 'covered': row['id'] in predictions, 'expected_spans': len(want),
                      'predicted_spans': len(got), 'matched_spans': len(matched),
                      'pairs': [{'expected_index': j, 'predicted_index': i,
                                 'boundary_exact': (want[j]['start'], want[j]['end']) == (got[i]['start'], got[i]['end'])}
                                for j, i in sorted(matched.items())]})
    for name, numerator, denominator in (
        ('span_recall', 'matched_spans', 'expected_spans'),
        ('span_precision', 'matched_spans', 'predicted_spans'),
        ('labeled_character_recall', 'matched_labeled_characters', 'expected_labeled_characters'),
        ('labeled_character_precision', 'matched_labeled_characters', 'predicted_labeled_characters')):
        totals[name] = totals[numerator] / totals[denominator] if totals[denominator] else None
    return {'interpretation': 'SECONDARY diagnostic only: same label+attribution, one-to-one span IoU >=0.5. Does not validate negation preservation/minimality. Never a release gate or substitute for exact results.',
            'totals': totals, 'cases': cases}


def format_recovery(baseline):
    result = {}
    for name, suite in baseline['suites'].items():
        predictions = {}
        attempts = []
        by_id = {a['id']: a for a in suite['attempts']}
        for row in suite['fixture']['rows']:
            attempt = {'id': row['id'], 'status': 'invalid', 'changes': []}
            try:
                raw = by_id[row['id']]['raw_response']
                parsed = json.loads(raw['choices'][0]['message']['content'])
                if not isinstance(parsed, dict) or set(parsed) != {'predictions'} or len(parsed['predictions']) != 1:
                    raise ValueError('Invalid original batch response')
                original = parsed['predictions'][0]
                if set(original) != {'id', 'spans', 'reason'} or original['id'] != row['id']:
                    raise ValueError('Original response identity mismatch')
                prediction, changes = recover_unique_quotes(row['text'], {'spans': original['spans'], 'reason': original['reason']})
                predictions[row['id']] = prediction
                attempt.update(status='validated', changes=changes)
            except (ValueError, TypeError, KeyError, IndexError) as exc:
                attempt['error'] = f'{type(exc).__name__}: {exc}'
            attempts.append(attempt)
        result[name] = {'interpretation': 'FORMAT-only deterministic replay of saved model outputs; no inference, label/attribution/text/rationale corrections. This can expose false positives previously hidden by invalid formatting.',
                        'baseline_evaluation': suite['evaluation'],
                        'baseline_secondary': boundary_metrics(suite['fixture']['rows'], suite['predictions']),
                        'attempts': attempts, 'predictions': predictions,
                        'evaluation': evaluate(suite['fixture']['rows'], predictions),
                        'secondary': boundary_metrics(suite['fixture']['rows'], predictions)}
    return result


def prepare(destination, runtime_file):
    if destination.exists():
        raise ValueError('Refusing to overwrite a frozen record')
    baseline = json.loads(BASELINE.read_text())
    if baseline.get('complete') is not True:
        raise ValueError('Baseline must be complete')
    old = baseline['protocol']
    protocol = {key: deepcopy(old[key]) for key in (
        'model', 'model_revision', 'file', 'model_bytes', 'model_sha256', 'model_license',
        'runtime', 'runtime_release', 'runtime_revision', 'context_tokens', 'output_token_limit',
        'temperature', 'seed', 'parallel_slots', 'cpu_threads', 'chat_template', 'overflow_policy')}
    protocol.update(contract=CONTRACT, prompt=PROMPT, prompt_sha256=hashlib.sha256(PROMPT.encode()).hexdigest(),
        schema=model_output_schema(), opaque_model_input_id='article',
        runtime_fingerprint=baseline['runtime_props']['build_info'],
        changes_from_baseline=['Shorter explicit attribution/abstention/minimal-clause prompt',
            'Unique exact text plus disambiguating context replaces model occurrence counting',
            'Constant opaque API article ID removes descriptive diagnostic-ID leakage'],
        causal_limit='Bundled development iteration; no causal attribution to any one changed factor',
        metrics={'primary': 'Existing exact source span + label + attribution; all 26/12 cases and 18/9 expected spans remain denominator, invalid outputs never dropped',
                 'secondary': 'Same-label-and-attribution maximum-cardinality one-to-one span IoU >=0.5 and labeled-attributed character overlap. Boundary differences still fail exact criteria.',
                 'safety': 'Report every negation, quotation, prompt-injection and neutral-padding case; structural validity or overlap does not certify semantics'},
        release_approved=False, frozen_before_first_semantic_inference=True,
        code_sha256={name: sha(ROOT / name) for name in OWN_FILES},
        runtime_wrapper_sha256=sha(runtime_file), baseline_sha256=sha(BASELINE),
        fixture_snapshots={name: deepcopy(suite['fixture']) for name, suite in baseline['suites'].items()},
        fixture_sha256={name: suite['fixture_sha256'] for name, suite in baseline['suites'].items()},
        suites_status={'original': 'development after baseline inspection; 26 cases',
                       'transfer': 'development after baseline inspection; 12 cases, no longer held-out'},
        reserved_data='No 66 reused-validation or 89 reserved corpus reads or evaluations',
        reviewer='Independent AI-assisted methodological review of exact anchoring, primary exact metrics and completion checks; not human annotation or release approval',
        frozen_utc=datetime.now(timezone.utc).isoformat())
    result = {'purpose': 'Focused v2 actual-model development iteration; synthetic expectations, not human gold or deployment accuracy',
              'protocol': protocol, 'protocol_sha256': stable_hash(protocol),
              'format_recovery_only': format_recovery(baseline), 'suites': {},
              'run_started': False, 'complete': False, 'release_approved': False}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
    return result


def payload_for(row, protocol):
    return {'model': protocol['model'], 'temperature': protocol['temperature'], 'seed': protocol['seed'],
            'max_tokens': protocol['output_token_limit'], 'stream': False,
            'chat_template_kwargs': {'enable_thinking': False},
            'messages': [{'role': 'system', 'content': protocol['prompt']},
                         {'role': 'user', 'content': json.dumps([{'id': 'article', 'text': row['text']}], ensure_ascii=False)}],
            'response_format': {'type': 'json_schema', 'json_schema': {'name': 'phrase_evidence', 'strict': True, 'schema': protocol['schema']}}}


def verify_frozen(result, runtime_file):
    protocol = result['protocol']
    if stable_hash(protocol) != result['protocol_sha256']:
        raise ValueError('Protocol changed after freeze')
    if protocol['prompt'] != PROMPT or protocol['schema'] != model_output_schema():
        raise ValueError('Current contract differs from frozen protocol')
    if not protocol['frozen_before_first_semantic_inference']:
        raise ValueError('Missing freeze')
    if sha(BASELINE) != protocol['baseline_sha256'] or sha(runtime_file) != protocol['runtime_wrapper_sha256']:
        raise ValueError('Baseline or runtime wrapper changed')
    for name, digest in protocol['code_sha256'].items():
        if sha(ROOT / name) != digest:
            raise ValueError('Code changed after freeze: ' + name)
    runtime_root = runtime_file.parent
    if sha(runtime_root / 'models' / protocol['file']) != protocol['model_sha256']:
        raise ValueError('Model file hash differs from verified baseline')


def run(destination, runtime_file):
    result = json.loads(destination.read_text())
    if result['run_started'] or result['complete']:
        raise ValueError('No reruns or resumption in an existing semantic record')
    verify_frozen(result, runtime_file)
    protocol = result['protocol']
    spec = importlib.util.spec_from_file_location('fixed_cpu_runtime_v2', runtime_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    def save():
        destination.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    result.update(run_started=True, started_utc=datetime.now(timezone.utc).isoformat())
    save()
    with module.LlamaRuntime(log_name='phrase_contract_v2_server.log') as runtime:
        props = runtime.request('/props')
        result.update(runtime_command=runtime.command, runtime_props=props, startup_seconds=runtime.startup_seconds)
        actual_context = props.get('default_generation_settings', {}).get('n_ctx')
        if (type(actual_context) is not int or actual_context != protocol['context_tokens']
                or props.get('build_info') != protocol['runtime_fingerprint'] or props.get('total_slots') != 1):
            raise ValueError('Runtime identity, actual context or slot count mismatch')
        for name, fixture in protocol['fixture_snapshots'].items():
            predictions = {}
            suite = {'status': 'development', 'fixture_sha256': protocol['fixture_sha256'][name],
                     'attempts': [], 'predictions': {}, 'complete': False}
            result['suites'][name] = suite
            for row in fixture['rows']:
                if stable_hash(json.loads(destination.read_text())['protocol']) != result['protocol_sha256']:
                    raise ValueError('Protocol changed during run')
                attempt = {'id': row['id'], 'model_input_id': 'article', 'status': 'failed', 'raw_response': None}
                started = time.monotonic()
                try:
                    body = payload_for(row, protocol)
                    count = runtime.exact_input_tokens(body)
                    attempt['exact_input_tokens'] = count
                    if type(count) is not int or count < 1 or count + body['max_tokens'] + 16 > actual_context:
                        raise ValueError('Full prompt plus reserved output and margin exceeds actual context')
                    output = runtime.request('/v1/chat/completions', body, timeout=120)
                    attempt['raw_response'] = output
                    predictions[row['id']] = validate_v2_completion(row['text'], output, count, actual_context,
                                                                  body['max_tokens'], protocol['runtime_fingerprint'])
                    attempt['status'] = 'validated'
                except (OSError, ValueError, TypeError, TimeoutError, RecursionError) as exc:
                    attempt['error'] = f'{type(exc).__name__}: {exc}'
                attempt.update(elapsed_seconds=time.monotonic() - started, runtime_rss_kib=rss_kib(runtime.proc.pid))
                suite['attempts'].append(attempt)
                suite['predictions'] = predictions
                suite['evaluation'] = evaluate(fixture['rows'], predictions)
                suite['secondary'] = boundary_metrics(fixture['rows'], predictions)
                save()
                print(name, row['id'], attempt['status'], round(attempt['elapsed_seconds'], 2), flush=True)
            suite['complete'] = True
            save()
        result.update(complete=True, completed_utc=datetime.now(timezone.utc).isoformat())
        save()
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--runtime', type=Path, required=True)
    args = parser.parse_args()
    result = (prepare if args.action == 'prepare' else run)(args.output.resolve(), args.runtime.resolve())
    sections = result['format_recovery_only'] if args.action == 'prepare' else result['suites']
    print(json.dumps({name: value['evaluation']['totals'] for name, value in sections.items()}, indent=2))
