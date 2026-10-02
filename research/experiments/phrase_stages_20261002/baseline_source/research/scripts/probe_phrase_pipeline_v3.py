"""Freeze/run/publish a three-task research pipeline on all 38 reused dev cases.

No external inference, model selection on held-out data, runtime retries, repair,
source truncation, failed-case omission, or production integration. Original and
former-transfer suites remain separate development sets throughout.
"""
from __future__ import annotations

import argparse
from collections import Counter
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
from backend.phrase_pipeline_v3 import (CONTRACT, MAX_CANDIDATES, PROMPTS, STAGES,
    assemble_prediction, decision_schema, extraction_schema, payload_for,
    validate_completion, validate_decisions, validate_extraction)
from research.scripts.probe_phrase_contract_v2 import boundary_metrics
from research.scripts.probe_phrase_evidence import evaluate
from research.scripts.probe_local_phrase_evidence import rss_kib

PRIOR = ROOT / 'research/results/phrase_instruct2507_comparison_20261002.json'
V2_PRIOR = ROOT / 'research/results/phrase_contract_v2_20261002_publication.json'
DEFAULT_RUN = ROOT / 'research/checkpoints/phrase-pipeline-v3-20261002/results.json'
DEFAULT_PUBLICATION = ROOT / 'research/results/phrase_pipeline_v3_20261002.json'
OWN_FILES = ('backend/phrase_pipeline_v3.py', 'research/scripts/probe_phrase_pipeline_v3.py',
             'tests/test_phrase_pipeline_v3.py')
DEPENDENCIES = ('backend/evidence.py', 'backend/phrase_contract_v2.py',
    'research/scripts/probe_phrase_contract_v2.py', 'research/scripts/probe_phrase_evidence.py',
    'research/scripts/probe_local_phrase_evidence.py')
MODEL_SHA = '3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode('utf-8')).hexdigest()


def exact_diagnostic(rows, predictions, keys):
    """Secondary exact-boundary metric with a declared subset of semantic axes."""
    totals = dict(cases=len(rows), covered_cases=0, exact_cases=0, expected_spans=0,
                  predicted_spans=0, recovered_spans=0, false_spans=0, missed_spans=0)
    cases = []
    for row in rows:
        want = validate_prediction(row['text'], {'spans': [dict(s, reason='Frozen synthetic expectation')
            for s in row['expected']], 'reason': 'Frozen synthetic expectation'})
        covered = row['id'] in predictions
        got = validate_prediction(row['text'], predictions[row['id']]) if covered else []
        expected = {tuple(s[k] for k in keys) for s in want}
        predicted = {tuple(s[k] for k in keys) for s in got}
        case = dict(id=row['id'], covered=covered, exact=covered and expected == predicted,
            expected_spans=len(expected), predicted_spans=len(predicted),
            recovered_spans=len(expected & predicted), false_spans=len(predicted - expected),
            missed_spans=len(expected - predicted))
        totals['covered_cases'] += int(covered)
        totals['exact_cases'] += int(case['exact'])
        for key in ('expected_spans', 'predicted_spans', 'recovered_spans', 'false_spans', 'missed_spans'):
            totals[key] += case[key]
        cases.append(case)
    totals['span_recall'] = totals['recovered_spans'] / totals['expected_spans'] if totals['expected_spans'] else None
    totals['span_precision'] = totals['recovered_spans'] / totals['predicted_spans'] if totals['predicted_spans'] else None
    return {'interpretation': 'SECONDARY exact-boundary diagnostic only; omitted axes are not certified',
            'signature_fields': keys, 'totals': totals, 'cases': cases}


def evaluate_all(rows, predictions, attempts):
    primary = evaluate(rows, predictions)
    totals = primary['totals']
    totals['no_expected_span_cases'] = totals.pop('neutral_cases')
    totals['no_expected_span_cases_with_false_highlights'] = totals.pop('neutral_cases_with_false_highlights')
    totals['no_expected_span_covered_cases'] = sum(c['covered'] for c in primary['cases'] if not c['expected_spans'])
    totals['expected_positive_cases'] = sum(bool(row['expected']) for row in rows)
    totals['covered_expected_positive_cases'] = sum(row['id'] in predictions for row in rows if row['expected'])
    totals['expected_positive_cases_with_any_prediction'] = sum(bool(predictions.get(row['id'], {}).get('spans')) for row in rows if row['expected'])
    totals['no_expected_span_false_highlights'] = sum(c['false_highlights'] for c in primary['cases'] if not c['expected_spans'])
    primary['no_expected_span_note'] = ('Zero-expected-span cases include negation, ambiguity, facts and nonpolitical inputs; '
        'not a population nonpolitical false-positive rate. Simple-rejection expectations are debatable AI-authored conventions.')
    stages = {}
    for stage in STAGES:
        records = [a['stages'][stage] for a in attempts]
        status = dict(Counter(r['status'] for r in records))
        durations = [r['elapsed_seconds'] for r in records if 'elapsed_seconds' in r]
        stages[stage] = {'all_fixture_cases': len(rows), 'processed_cases': len(records), 'status_counts': status,
            'total_seconds': sum(durations), 'mean_attempt_seconds': sum(durations) / len(durations) if durations else None,
            'max_attempt_seconds': max(durations) if durations else None,
            'attempted_cases': sum(r['status'] in ('validated', 'failed') for r in records)}
    attribution_counts = dict(Counter(s['attribution'] for p in predictions.values() for s in p['spans']))
    by_id = {r['id']: r for r in rows}
    candidate_counts = {'all_expected_spans': sum(len(r['expected']) for r in rows), 'validated_candidates': 0,
        'exact_expected_boundaries_extracted': 0, 'exact_expected_boundaries_with_valid_speaker_decision': 0,
        'exact_expected_boundaries_with_correct_speaker': 0, 'speaker_decisions': {}, 'direction_decisions': {}}
    speaker_values, direction_values = Counter(), Counter()
    for attempt in attempts:
        candidates = attempt.get('candidates', [])
        candidate_counts['validated_candidates'] += len(candidates)
        row = by_id[attempt['id']]
        expected = validate_prediction(row['text'], {'spans': [dict(s, reason='Frozen expectation') for s in row['expected']], 'reason': 'Frozen expectation'})
        expected_by_bounds = {(s['start'], s['end']): s for s in expected}
        names = {'author': 'NARRATOR', 'quoted': 'DIRECT_QUOTED_SPEAKER', 'unknown': 'UNRESOLVED'}
        for candidate in candidates:
            truth = expected_by_bounds.get((candidate['start'], candidate['end']))
            if truth is not None:
                candidate_counts['exact_expected_boundaries_extracted'] += 1
            stage = attempt['stages']['speaker']
            if stage['status'] == 'validated':
                speaker = stage['validated_response'][candidate['id']]['speaker']
                speaker_values[speaker] += 1
                if truth is not None:
                    candidate_counts['exact_expected_boundaries_with_valid_speaker_decision'] += 1
                    candidate_counts['exact_expected_boundaries_with_correct_speaker'] += int(speaker == names[truth['attribution']])
            stage = attempt['stages']['direction']
            if stage['status'] == 'validated':
                direction_values[stage['validated_response'][candidate['id']]['direction']] += 1
    candidate_counts['speaker_decisions'] = dict(speaker_values)
    candidate_counts['direction_decisions'] = dict(direction_values)
    candidate_counts['note'] = 'Stage-only diagnostics are conditional on extracted candidates; fixed all-expected denominator and end-to-end exact metrics remain primary'
    by_category = {}
    for row in rows:
        if row['category'] not in by_category:
            category_rows = [r for r in rows if r['category'] == row['category']]
            values = evaluate(category_rows, {r['id']: predictions[r['id']] for r in category_rows if r['id'] in predictions})['totals']
            values['no_expected_span_cases'] = values.pop('neutral_cases')
            values['no_expected_span_cases_with_false_highlights'] = values.pop('neutral_cases_with_false_highlights')
            by_category[row['category']] = values
    return {'primary_exact': primary,
        'direction_only_secondary': exact_diagnostic(rows, predictions, ('start', 'end', 'label')),
        'speaker_only_secondary': exact_diagnostic(rows, predictions, ('start', 'end', 'attribution')),
        'label_and_speaker_overlap_secondary': boundary_metrics(rows, predictions),
        'stage_accounting': stages, 'candidate_diagnostics': candidate_counts,
        'attribution_counts': attribution_counts, 'by_category': by_category}


def prepare(destination, runtime_file):
    if destination.exists():
        raise ValueError('Refusing to overwrite a frozen run')
    prior = json.loads(PRIOR.read_text())
    if not prior.get('complete'):
        raise ValueError('Prior comparison must be complete')
    old = prior['protocol']
    protocol = {key: deepcopy(old[key]) for key in ('model', 'model_revision', 'file', 'model_bytes',
        'model_sha256', 'model_provenance', 'runtime', 'runtime_release', 'runtime_revision',
        'context_tokens', 'output_token_limit', 'temperature', 'seed', 'parallel_slots',
        'cpu_threads', 'runtime_fingerprint')}
    if protocol['model_sha256'] != MODEL_SHA:
        raise ValueError('Unexpected research checkpoint')
    protocol.update(contract=CONTRACT, stage_order=list(STAGES), prompts=deepcopy(PROMPTS),
        prompt_sha256={k: hashlib.sha256(v.encode()).hexdigest() for k, v in PROMPTS.items()},
        extraction_schema=extraction_schema(), decision_schema_examples={
            stage: decision_schema(stage, [{'id': 'c000'}, {'id': 'c001'}]) for stage in ('direction', 'speaker')},
        candidate_limit=MAX_CANDIDATES, candidate_limit_enforcement='Validator-only cap; entire >16-candidate article fails, never truncate or grammar-coerce its length',
        extraction_completeness_limit='A valid <=16 candidate list is not proof of exhaustive extraction; fixed positive recall is required. Per-stage full-context reservation limits practical supported length.',
        output_token_reservation_per_stage=1024,
        full_original_source_every_stage=True, source_normalization=False,
        candidate_source='Model extraction only; no ideological keywords or inherited article labels',
        speaker_mapping={'NARRATOR': 'author', 'DIRECT_QUOTED_SPEAKER': 'quoted', 'UNRESOLVED': 'unknown'},
        scope_limit='Indirectly attributed opinions remain UNRESOLVED, not narrator; no general-news attribution claim',
        composition='Three separate model tasks on the same checkpoint; no assumption of statistically independent errors',
        empty_extraction='Valid spans=[] is an explicit negative; direction and speaker not_required_empty_candidates',
        failure_policy='No retry or repair. Any attempted stage failure invalidates end-to-end case coverage. After extraction failure dependent stages are blocked; direction and speaker both run for every validated nonempty candidate set even if either fails.',
        overflow_policy='Exact per-stage token preflight +1024 output +16 safety margin <=4096; never truncate source or candidates; excess candidates reject',
        chat_template='Checkpoint embedded template, enable_thinking=false and runtime reasoning off',
        metrics={'primary': 'All38 fixed development cases, full exact source+direction+speaker and author-only rendering; all failures remain uncovered',
                 'secondary': 'Exact direction-only and speaker-only, labeled-attributed IoU, stage conditional diagnostics; never substitute for primary',
                 'negative': 'No-expected-span false highlights; includes debatable synthetic rejection conventions, not all nonpolitical',
                 'safety': 'All cases and categories retained, including negation, quotes, injection and padding; no human accuracy claim'},
        fixture_snapshots=deepcopy(old['fixture_snapshots']),
        fixture_content_sha256={name: stable_hash(fixture) for name, fixture in old['fixture_snapshots'].items()},
        suites_status={'original': '26 already-reused development cases', 'transfer': '12 former-transfer, already-reused development cases'},
        reserved_data='No validation, test, embargoed89, or other held-out examples used',
        model_license='Apache-2.0 official Qwen base; third-party Unsloth GGUF, retain licenses/notices',
        changes_from_prior='Task decomposition, narrowed schemas, narrator terminology and explicit NO_DIRECTION; bundled experiment, no single-factor causal claim',
        reviewer='Accuracy-gates design review before model inference; AI review, not human annotation or release approval',
        code_sha256={name: sha(ROOT / name) for name in OWN_FILES + DEPENDENCIES},
        runtime_wrapper_sha256=sha(runtime_file),
        runtime_binary_sha256=sha(runtime_file.parent / 'b11349/llama-b11349/llama-server'),
        prior_record_sha256=sha(PRIOR), prior_v2_record_sha256=sha(V2_PRIOR),
        frozen_before_first_model_call=True, frozen_utc=datetime.now(timezone.utc).isoformat(), release_approved=False)
    if [(name, len(fixture['rows'])) for name, fixture in protocol['fixture_snapshots'].items()] != [('original', 26), ('transfer', 12)]:
        raise ValueError('Expected unchanged 26/12 development fixture ordering')
    for fixture in protocol['fixture_snapshots'].values():
        evaluate(fixture['rows'], {})
    result = {'purpose': 'Three-task phrase research on fixed reused synthetic development diagnostics; not independent or deployment accuracy',
        'protocol': protocol, 'protocol_sha256': stable_hash(protocol), 'run_started': False,
        'complete': False, 'release_approved': False, 'suites': {}}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    return result


def verify_frozen(result, runtime_file, verify_weights=True):
    protocol = result['protocol']
    if stable_hash(protocol) != result['protocol_sha256'] or not protocol['frozen_before_first_model_call']:
        raise ValueError('Protocol changed after freeze')
    if protocol['prompts'] != PROMPTS or protocol['extraction_schema'] != extraction_schema():
        raise ValueError('Current prompt or schema differs from freeze')
    for name, digest in protocol['code_sha256'].items():
        if sha(ROOT / name) != digest:
            raise ValueError('Code changed after freeze: ' + name)
    for name, fixture in protocol['fixture_snapshots'].items():
        if stable_hash(fixture) != protocol['fixture_content_sha256'][name]:
            raise ValueError('Fixture changed: ' + name)
    if sha(PRIOR) != protocol['prior_record_sha256'] or sha(V2_PRIOR) != protocol['prior_v2_record_sha256']:
        raise ValueError('Prior evidence record changed')
    if sha(runtime_file) != protocol['runtime_wrapper_sha256']:
        raise ValueError('Runtime wrapper changed')
    if sha(runtime_file.parent / 'b11349/llama-b11349/llama-server') != protocol['runtime_binary_sha256']:
        raise ValueError('Runtime executable changed')
    if verify_weights:
        weights = runtime_file.parent / 'models' / protocol['file']
        if weights.stat().st_size != protocol['model_bytes'] or sha(weights) != protocol['model_sha256']:
            raise ValueError('Checkpoint bytes differ from frozen identity')


def run_case(runtime, row, protocol):
    """Always returns accounting; no stage retry and no predicted result on failure."""
    start = time.monotonic()
    attempt = {'id': row['id'], 'source_text_sha256': hashlib.sha256(row['text'].encode()).hexdigest(),
        'status': 'failed', 'candidates': [], 'stages': {s: {'status': 'pending'} for s in STAGES}}
    decisions = {}
    for stage in STAGES:
        record = attempt['stages'][stage]
        if stage != 'extract' and attempt['stages']['extract']['status'] != 'validated':
            record.update(status='blocked_extraction_failure')
            continue
        if stage != 'extract' and not attempt['candidates']:
            record.update(status='not_required_empty_candidates')
            decisions[stage] = {}
            continue
        started = time.monotonic()
        record.update(status='failed', raw_response=None)
        try:
            body = payload_for(stage, row['text'], attempt['candidates'], protocol)
            record.update(request_sha256=stable_hash(body), schema=body['response_format']['json_schema']['schema'],
                source_text_sha256=attempt['source_text_sha256'], candidate_sha256=stable_hash(attempt['candidates']),
                reserved_output_tokens=body['max_tokens'])
            count = runtime.exact_input_tokens(body)
            record['exact_input_tokens'] = count
            if type(count) is not int or count < 1 or count + body['max_tokens'] + 16 > protocol['context_tokens']:
                raise ValueError('Full source prompt plus output reservation exceeds context')
            output = runtime.request('/v1/chat/completions', body, timeout=180)
            record['raw_response'] = output
            decoded = validate_completion(output, count, protocol['context_tokens'], body['max_tokens'], protocol['runtime_fingerprint'])
            if stage == 'extract':
                if isinstance(decoded, dict) and isinstance(decoded.get('spans'), list):
                    record['raw_candidate_count'] = len(decoded['spans'])
                attempt['candidates'] = validate_extraction(row['text'], decoded)
            else:
                decisions[stage] = validate_decisions(stage, attempt['candidates'], decoded)
            record.update(status='validated', validated_response=decoded)
        except (OSError, ValueError, TypeError, TimeoutError, RecursionError) as exc:
            record['error'] = f'{type(exc).__name__}: {exc}'
        record['elapsed_seconds'] = time.monotonic() - started
        if getattr(runtime, 'proc', None) is not None:
            record['runtime_rss_kib'] = rss_kib(runtime.proc.pid)
    prediction = None
    if all(s['status'] in ('validated', 'not_required_empty_candidates') for s in attempt['stages'].values()):
        try:
            prediction = assemble_prediction(row['text'], attempt['candidates'], decisions['direction'], decisions['speaker'])
            attempt['status'] = 'validated'
        except (ValueError, TypeError) as exc:
            attempt['assembly_error'] = f'{type(exc).__name__}: {exc}'
    attempt['elapsed_seconds'] = time.monotonic() - start
    return attempt, prediction


def verify_runtime_props(props, protocol):
    if not isinstance(props, dict) or not isinstance(props.get('default_generation_settings'), dict):
        raise ValueError('Malformed runtime properties')
    actual_context = props['default_generation_settings'].get('n_ctx')
    slots = props.get('total_slots')
    model_path = props.get('model_path')
    if (type(actual_context) is not int or actual_context != protocol['context_tokens'] or
            props.get('build_info') != protocol['runtime_fingerprint'] or
            type(slots) is not int or slots != 1 or not isinstance(model_path, str) or
            Path(model_path).name != protocol['file']):
        raise ValueError('Runtime model, context, fingerprint or slots mismatch')


def run(destination, runtime_file):
    result = json.loads(destination.read_text())
    if result['run_started'] or result['complete']:
        raise ValueError('No overwriting, resuming or repeating a semantic run')
    verify_frozen(result, runtime_file)
    protocol = result['protocol']
    spec = importlib.util.spec_from_file_location('pipeline_v3_runtime', runtime_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    runtime = module.LlamaRuntime(log_name='phrase_pipeline_v3_server.log')
    runtime.command[runtime.command.index('-m') + 1] = str(runtime_file.parent / 'models' / protocol['file'])
    def save():
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    result.update(run_started=True, started_utc=datetime.now(timezone.utc).isoformat())
    save()
    try:
        with runtime:
            props = runtime.request('/props')
            result.update(runtime_command=runtime.command, runtime_props=props, startup_seconds=runtime.startup_seconds)
            verify_runtime_props(props, protocol)
            for name, fixture in protocol['fixture_snapshots'].items():
                predictions = {}
                suite = {'status': protocol['suites_status'][name], 'attempts': [], 'predictions': {}, 'complete': False}
                result['suites'][name] = suite
                for row in fixture['rows']:
                    if stable_hash(json.loads(destination.read_text())['protocol']) != result['protocol_sha256']:
                        raise ValueError('Protocol changed during run')
                    # Imported source must stay frozen across every case, too.
                    for source, digest in protocol['code_sha256'].items():
                        if sha(ROOT / source) != digest:
                            raise ValueError('Code changed during run: ' + source)
                    attempt, prediction = run_case(runtime, row, protocol)
                    suite['attempts'].append(attempt)
                    if prediction is not None:
                        predictions[row['id']] = prediction
                    suite['predictions'] = predictions
                    suite['metrics'] = evaluate_all(fixture['rows'], predictions, suite['attempts'])
                    save()
                    print(name, row['id'], attempt['status'], {s: a['status'] for s, a in attempt['stages'].items()},
                          round(attempt['elapsed_seconds'], 2), flush=True)
                suite['complete'] = True
                save()
            result.update(complete=True, completed_utc=datetime.now(timezone.utc).isoformat())
            save()
    except BaseException as exc:
        result.update(run_error=f'{type(exc).__name__}: {exc}', interrupted_utc=datetime.now(timezone.utc).isoformat())
        save()
        raise
    return result


def publish(source, destination):
    if destination.exists():
        raise ValueError('Refusing to overwrite publication')
    result = json.loads(source.read_text())
    if not result.get('complete') or any(not suite['complete'] for suite in result['suites'].values()):
        raise ValueError('Only complete runs can be published')
    result['publication_note'] = {'source_record_sha256': sha(source), 'predictions_and_metrics_unchanged': True,
        'absolute_environment_paths_removed': True, 'release_approved': False,
        'interpretation': 'Reused synthetic development only; no independent accuracy or release approval',
        'primary_target': 'Author/narrator framing only; quoted views diagnostic, serving unchanged'}
    def clean(value):
        if isinstance(value, str):
            return value.replace(str(ROOT.parent), '[local-workspace]')
        if isinstance(value, list):
            return [clean(v) for v in value]
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        return value
    result = clean(result)
    result['publication_note']['original_frozen_protocol_sha256'] = result['protocol_sha256']
    result['publication_note']['sanitized_public_protocol_sha256'] = stable_hash(result['protocol'])
    result['publication_note']['publisher_script_sha256'] = sha(Path(__file__))
    result['publication_note']['publisher_revision_note'] = ('Post-inference publication-only fix: compare canonical JSON metric hashes so Python tuples and their saved JSON arrays agree. Original frozen source snapshots and model record retained unchanged; no inference or metric changes.')
    # Recompute metrics from final predictions to catch stale/incomplete summaries.
    for name, suite in result['suites'].items():
        expected = evaluate_all(result['protocol']['fixture_snapshots'][name]['rows'], suite['predictions'], suite['attempts'])
        if stable_hash(expected) != stable_hash(suite['metrics']):
            raise ValueError('Publication metric replay mismatch: ' + name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run', 'publish'])
    parser.add_argument('--output', type=Path, default=DEFAULT_RUN)
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--publication', type=Path, default=DEFAULT_PUBLICATION)
    args = parser.parse_args()
    if args.action == 'publish':
        record = publish(args.output.resolve(), args.publication.resolve())
    else:
        if args.runtime is None:
            parser.error('--runtime is required for prepare/run')
        record = (prepare if args.action == 'prepare' else run)(args.output.resolve(), args.runtime.resolve())
    print(json.dumps({'complete': record['complete'], 'protocol_sha256': record['protocol_sha256'],
        'totals': {name: suite['metrics']['primary_exact']['totals'] for name, suite in record['suites'].items()}}, indent=2))
