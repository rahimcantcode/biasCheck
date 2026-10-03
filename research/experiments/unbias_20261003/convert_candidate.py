"""Measured, recoverable conversion of the verified official V2 checkpoint.

This performs no inference. It preserves source and output hashes, uses the
pinned upstream converter unchanged, and removes only verified, regenerable
downloaded safetensors after a successful Q8 structural/numeric validation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = Path(__file__).resolve().parent
SOURCE = Path('/tmp/llama-b11349-conversion-source/llama.cpp-fb4b2737a808a3fb7c2117a498f43815dc9be53e')
PYTHON = Path('/tmp/bias-eval-venv/bin/python')
MODEL = Path('/tmp/unbias-v2-bf16')
RUNTIME = ROOT / 'research/checkpoints/unbias-runtime/bin/llama-b11349'
OUTPUT = Path('/tmp/unbias-v2-q4')
Q8 = OUTPUT / 'Qwen3-8B-UnBias-Plus-SFT-Instruct-V2-Q8_0.gguf'
Q4 = OUTPUT / 'Qwen3-8B-UnBias-Plus-SFT-Instruct-V2-Q4_K_M.gguf'
MANIFEST = EXPERIMENT / 'conversion_manifest.json'
RUNTIME_MANIFEST = EXPERIMENT / 'native_runtime_manifest.json'
REVISION = 'fb4b2737a808a3fb7c2117a498f43815dc9be53e'


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        while chunk := handle.read(4 * 1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def save(value):
    temporary = MANIFEST.with_suffix('.json.partial')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(MANIFEST)


def memory_values(pid):
    try:
        values = {}
        for line in Path(f'/proc/{pid}/status').read_text().splitlines():
            if line.startswith(('VmRSS:', 'VmHWM:', 'RssAnon:')):
                key, amount, *_ = line.split()
                values[key[:-1]] = int(amount) * 1024
        return values
    except (FileNotFoundError, ProcessLookupError):
        return {}


def run_stage(command, name, record, env):
    log = EXPERIMENT / f'{name}.log'
    if log.exists():
        raise RuntimeError(f'Refusing to overwrite {log}')
    stage = {'name': name, 'command': command, 'started_utc': utc(),
             'log': str(log.relative_to(ROOT)), 'peak_sampled_rss_bytes': 0,
             'peak_sampled_anon_bytes': 0, 'complete': False}
    record['stages'].append(stage)
    save(record)
    started = time.monotonic()
    print(f'START {name}', flush=True)
    with log.open('x') as handle:
        proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=handle,
                                stderr=subprocess.STDOUT)
        while proc.poll() is None:
            usage = memory_values(proc.pid)
            stage['peak_sampled_rss_bytes'] = max(stage['peak_sampled_rss_bytes'], usage.get('VmRSS', 0), usage.get('VmHWM', 0))
            stage['peak_sampled_anon_bytes'] = max(stage['peak_sampled_anon_bytes'], usage.get('RssAnon', 0))
            if usage.get('RssAnon', 0) > 7 * 1024 ** 3:
                proc.terminate()
                stage['terminated_for_resource_limit'] = 'Anonymous memory exceeded 7 GiB.'
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            if time.monotonic() - started > 3600:
                proc.terminate()
                stage['terminated_for_resource_limit'] = 'One-hour conversion-stage limit.'
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            time.sleep(0.5)
        stage['exit_code'] = proc.returncode
    stage['elapsed_seconds'] = time.monotonic() - started
    stage['completed_utc'] = utc()
    stage['complete'] = proc.returncode == 0
    stage['children_cumulative_peak_rss_kib'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    save(record)
    print(f"END {name} exit={proc.returncode} seconds={stage['elapsed_seconds']:.2f} peak_rss={stage['peak_sampled_rss_bytes']}", flush=True)
    if proc.returncode:
        raise RuntimeError(f'{name} failed; see {log}')


def source_tensor_summary(files):
    tensors = {}
    for entry in files:
        if not entry['file'].endswith('.safetensors'):
            continue
        with (MODEL / entry['file']).open('rb') as handle:
            size = int.from_bytes(handle.read(8), 'little')
            header = json.loads(handle.read(size))
        for name, value in header.items():
            if name != '__metadata__':
                if name in tensors:
                    raise ValueError(f'Duplicate source tensor {name}')
                tensors[name] = value
    return {'tensor_count': len(tensors),
            'parameter_count': sum(math.prod(v['shape']) for v in tensors.values()),
            'dtype_counts': dict(Counter(v['dtype'] for v in tensors.values()))}


def validate_gguf(path, expected, check_q8=False):
    sys.path.insert(0, str(SOURCE / 'gguf-py'))
    import gguf
    import numpy as np
    started = time.monotonic()
    reader = gguf.GGUFReader(path)
    field = lambda key: reader.fields[key].contents()
    assert field('general.architecture') == 'qwen3'
    assert field('qwen3.block_count') == 36
    assert field('qwen3.embedding_length') == 4096
    assert len(reader.tensors) == expected['tensor_count']
    assert sum(t.n_elements for t in reader.tensors) == expected['parameter_count']
    assert len({t.name for t in reader.tensors}) == len(reader.tensors)
    assert 'tokenizer.chat_template' in reader.fields
    for tensor in reader.tensors:
        assert tensor.data_offset + tensor.n_bytes <= path.stat().st_size
        if check_q8 and tensor.tensor_type == gguf.GGMLQuantizationType.Q8_0:
            blocks = tensor.data.reshape(-1, 34)
            for start in range(0, len(blocks), 65536):
                scales = blocks[start:start + 65536, :2].copy().view(np.float16)
                assert np.isfinite(scales).all(), tensor.name
                assert (scales >= 0).all(), tensor.name
        elif check_q8 and tensor.tensor_type == gguf.GGMLQuantizationType.F32:
            values = tensor.data.reshape(-1)
            for start in range(0, len(values), 1048576):
                assert np.isfinite(values[start:start + 1048576]).all(), tensor.name
        elif check_q8:
            raise ValueError(f'Unexpected Q8 tensor dtype {tensor.tensor_type}')
    result = {'path': str(path), 'bytes': path.stat().st_size,
              'sha256': digest(path), 'tensor_count': len(reader.tensors),
              'parameter_count': sum(t.n_elements for t in reader.tensors),
              'tensor_type_counts': dict(Counter(t.tensor_type.name for t in reader.tensors)),
              'architecture': field('general.architecture'),
              'numeric_q8_scales_and_f32_checked': check_q8,
              'elapsed_seconds': time.monotonic() - started,
              'validation_scope': 'All tensor ranges, count, parameter count, architecture, chat template; all Q8 scales and F32 values finite when requested. This is not inference or model-quality validation.'}
    del reader
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wait-for-marker', action='store_true')
    args = parser.parse_args()
    marker = MODEL / 'VERIFIED.json'
    if args.wait_for_marker:
        print(f'Waiting for verified source marker {marker}', flush=True)
        deadline = time.monotonic() + 7200
        while not marker.is_file():
            if time.monotonic() > deadline:
                raise TimeoutError('Verified source marker did not arrive within two hours.')
            time.sleep(2)
    verified = json.loads(marker.read_text())
    for path in [MANIFEST, RUNTIME_MANIFEST, Q8, Q4]:
        if path.exists():
            raise RuntimeError(f'Refusing to overwrite {path}')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    record = {'schema_version': 1, 'started_utc': utc(), 'complete': False,
              'model_id': verified['model_id'], 'model_revision': verified['model_revision'],
              'input_manifest': verified, 'input_manifest_sha256': digest(marker),
              'conversion_source_revision': REVISION,
              'conversion_source': json.loads((SOURCE.parent / 'source_manifest.json').read_text()),
              'source_converter_sha256': digest(SOURCE / 'convert_hf_to_gguf.py'),
              'script_sha256': digest(Path(__file__)),
              'dependencies': {name: importlib.metadata.version(name) for name in ['torch', 'transformers', 'numpy', 'sentencepiece', 'huggingface_hub', 'safetensors']},
              'stages': [], 'deleted_regenerable_source_shards': [],
              'quality_caveat': 'Locally derived Q8_0 then Q4_K_M requantization of the pinned official V2 checkpoint; not the full-precision original and not a claim of equivalent model quality.',
              'memory_policy': '4 CPU threads; default lazy converter; no temp copy; stop if child anonymous memory exceeds 7 GiB; Q4 quantizer buffer 512 MiB.'}
    save(record)
    try:
        print('Verifying downloaded source hashes before conversion.', flush=True)
        for entry in verified['files']:
            path = MODEL / entry['file']
            assert path.resolve().parent == MODEL.resolve()
            assert not path.is_symlink()
            assert path.stat().st_size == entry['bytes'], entry['file']
            assert digest(path) == entry['sha256'], entry['file']
        record['source_hashes_reverified_utc'] = utc()
        record['source_tensor_summary'] = source_tensor_summary(verified['files'])
        spec = json.loads((ROOT / 'research/local_phrase_runtime.json').read_text())['runtime']
        assert digest(RUNTIME / 'llama-server') == spec['server_sha256']
        record['runtime'] = {'fingerprint': spec['fingerprint'], 'server_sha256': spec['server_sha256'],
                             'quantizer_sha256': digest(RUNTIME / 'llama-quantize')}
        record['disk_available_before_conversion_bytes'] = shutil.disk_usage(OUTPUT).free
        if shutil.disk_usage(OUTPUT).free < 10 * 10 ** 9:
            raise RuntimeError('Need at least 10 GB free for Q8 output plus margin.')
        save(record)
        env = os.environ.copy()
        env.update(OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4',
                   HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                   LD_LIBRARY_PATH=str(RUNTIME))
        run_stage([str(PYTHON), str(SOURCE / 'convert_hf_to_gguf.py'), str(MODEL),
                   '--outfile', str(Q8), '--outtype', 'q8_0'], 'conversion_q8', record, env)
        record['q8_validation'] = validate_gguf(Q8, record['source_tensor_summary'], check_q8=True)
        save(record)
        print('Q8 structural, finite-value, source-count and hash checks passed.', flush=True)
        # Only these exact downloaded, verified, reproducible files are removed.
        for entry in verified['files']:
            if entry['file'].endswith('.safetensors'):
                path = MODEL / entry['file']
                assert path.resolve().parent == MODEL.resolve() and not path.is_symlink()
                path.unlink()
                record['deleted_regenerable_source_shards'].append(entry)
                save(record)
        record['disk_available_before_q4_bytes'] = shutil.disk_usage(OUTPUT).free
        save(record)
        run_stage([str(RUNTIME / 'llama-quantize'), '--allow-requantize', '--max-buffer-size',
                   '512', str(Q8), str(Q4), 'Q4_K_M', '4'], 'conversion_q4', record, env)
        record['q4_validation'] = validate_gguf(Q4, record['source_tensor_summary'])
        record['complete'] = True
        record['completed_utc'] = utc()
        save(record)
        native = {'schema_version': 1, 'model_id': verified['model_id'],
                  'model_revision': verified['model_revision'], 'weights_path': str(Q4),
                  'weights_sha256': record['q4_validation']['sha256'],
                  'weights_bytes': Q4.stat().st_size,
                  'quantization': 'Q4_K_M requantized from locally generated Q8_0',
                  'conversion_source_revision': REVISION,
                  'runtime_fingerprint': spec['fingerprint'],
                  'context_tokens': 8192, 'threads': 4,
                  'max_output_tokens': 2048,
                  'runtime_server_path': str(RUNTIME / 'llama-server'),
                  'runtime_server_sha256': spec['server_sha256'],
                  'conversion_manifest': str(MANIFEST.relative_to(ROOT)),
                  'quality_caveat': record['quality_caveat']}
        RUNTIME_MANIFEST.write_text(json.dumps(native, indent=2) + '\n')
        print(json.dumps({'complete': True, 'runtime_manifest': str(RUNTIME_MANIFEST),
                          'weights_path': str(Q4), 'weights_sha256': native['weights_sha256']}, indent=2), flush=True)
    except BaseException as exc:
        record['error'] = f'{type(exc).__name__}: {exc}'
        record['failed_utc'] = utc()
        save(record)
        raise


if __name__ == '__main__':
    main()
