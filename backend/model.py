"""Full-document inference and model-bound calibration, with no silent truncation."""
from functools import lru_cache
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import math
import os
import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
try:
    from .config import get_settings
except ImportError:
    from config import get_settings

MAX_LENGTH = 512
AGGREGATION = 'new_token_weighted_logit_mean_v1'
PREPROCESSING = 'plain_text_exact_url_article_extraction_v2'
WINDOW_PREPARATION_LEGACY = 'transformers_special_token_builder_v1'
WINDOW_PREPARATION_PROCESSOR = 'tokenizers_verified_post_processor_v1'
INFERENCE_RUNTIME_FIELDS = frozenset({
    'schema_version', 'torch', 'transformers', 'tokenizers',
    'window_preparation', 'device', 'dtype', 'attention_implementation', 'batch_size',
})


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def get_model_dir():
    path = get_settings().model_dir
    for name in ('config.json', 'model.safetensors'):
        if not (path / name).is_file():
            raise RuntimeError(f'Missing model artifact: {name}')
    if (path / 'model.safetensors').stat().st_size < 1024:
        raise RuntimeError('Weights are a Git LFS pointer. Run git lfs pull.')
    return path


@lru_cache(maxsize=1)
def get_tokenizer():
    return AutoTokenizer.from_pretrained(get_model_dir(), local_files_only=True, use_fast=True)


@lru_cache(maxsize=1)
def get_model():
    torch.set_num_threads(max(1, int(os.getenv('BIASCHECK_TORCH_THREADS', '2'))))
    model, info = AutoModelForSequenceClassification.from_pretrained(
        get_model_dir(), local_files_only=True, output_loading_info=True)
    if any(info.get(k) for k in ('missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs')):
        raise RuntimeError(f'Checkpoint loading mismatch: {info}')
    labels = {int(k): str(v).upper() for k, v in model.config.id2label.items()}
    if set(labels) != {0, 1, 2} or set(labels.values()) != {'LEFT', 'CENTER', 'RIGHT'}:
        raise RuntimeError('Checkpoint requires an explicit LEFT/CENTER/RIGHT label mapping.')
    model.eval()
    return model


@lru_cache(maxsize=1)
def model_metadata():
    import transformers, tokenizers
    path = get_model_dir()
    files = sorted(p for p in path.iterdir() if p.name in {
        'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json',
        'vocab.json', 'merges.txt', 'spm.model', 'added_tokens.json'})
    return {
        'weights_sha256': sha256(path / 'model.safetensors'),
        'config_sha256': sha256(path / 'config.json'),
        'tokenizer_sha256': hashlib.sha256(''.join(p.name + sha256(p) for p in files).encode()).hexdigest(),
        'id2label': {str(k): str(v).upper() for k,v in get_model().config.id2label.items()},
        'aggregation': AGGREGATION, 'preprocessing': PREPROCESSING, 'max_length': MAX_LENGTH, 'stride': 64,
        'demo_mode': os.getenv('BIASCHECK_DEMO_MODE', '0') == '1',
        'transformers': transformers.__version__, 'torch': torch.__version__,
        'tokenizers': tokenizers.__version__,
        'inference_runtime': inference_runtime(get_model(), get_tokenizer()),
    }


def validate_inference_runtime(runtime):
    """Require a complete versioned identity, including for legacy-vs-legacy use."""
    if not isinstance(runtime, dict) or set(runtime) != INFERENCE_RUNTIME_FIELDS:
        raise RuntimeError('Missing or incomplete inference_runtime identity; regenerate legacy evaluation reports')
    if type(runtime['schema_version']) is not int or runtime['schema_version'] != 1:
        raise RuntimeError('Unsupported inference_runtime schema_version')
    for key in INFERENCE_RUNTIME_FIELDS - {'schema_version', 'batch_size'}:
        if not isinstance(runtime[key], str) or not runtime[key].strip() or runtime[key] != runtime[key].strip():
            raise RuntimeError(f'Invalid inference_runtime identity: {key}')
    for key in INFERENCE_RUNTIME_FIELDS - {'schema_version', 'batch_size'}:
        if runtime[key].lower() in {'unknown', 'none', 'null', 'unset', 'unavailable', 'auto'}:
            raise RuntimeError(f'Unobserved inference_runtime identity: {key}')
    if runtime['window_preparation'] not in {WINDOW_PREPARATION_LEGACY, WINDOW_PREPARATION_PROCESSOR}:
        raise RuntimeError('Unsupported inference_runtime window_preparation')
    if type(runtime['batch_size']) is not int or not 1 <= runtime['batch_size'] <= 8:
        raise RuntimeError('Invalid inference_runtime identity: batch_size')
    return runtime


def inference_runtime(model, tokenizer):
    """Describe the loaded model's actual numeric/runtime configuration."""
    import transformers, tokenizers
    devices = {str(parameter.device) for parameter in model.parameters()}
    dtypes = {str(parameter.dtype) for parameter in model.parameters()}
    if len(devices) != 1 or len(dtypes) != 1:
        raise RuntimeError('Cannot bind calibration to a mixed or unknown model device/dtype')
    return validate_inference_runtime({
        'schema_version': 1, 'torch': str(torch.__version__),
        'transformers': transformers.__version__, 'tokenizers': tokenizers.__version__,
        'window_preparation': WINDOW_PREPARATION_LEGACY if callable(
            getattr(tokenizer, 'build_inputs_with_special_tokens', None)) else WINDOW_PREPARATION_PROCESSOR,
        'device': devices.pop(), 'dtype': dtypes.pop(),
        'attention_implementation': getattr(model.config, '_attn_implementation', None),
        'batch_size': get_settings().batch_size,
    })


def token_windows(ids, capacity=510, stride=64):
    if capacity <= 0 or not 0 <= stride < capacity:
        raise ValueError('Invalid token window configuration')
    previous_end = 0
    for start in range(0, len(ids), capacity - stride):
        end = min(start + capacity, len(ids))
        yield ids[start:end], start, end, end - previous_end
        previous_end = end
        if end == len(ids):
            break


def prepare_window_features(tokenizer, encoded_text, windows, capacity, stride=64):
    """Add special tokens without decoding or changing already-tokenized windows.

    Transformers v4 exposes a builder; v5 uses the Tokenizers post-processor.
    The fallback checks every content ID against our existing coverage windows
    and fails closed if the tokenizer produces a different partition.
    """
    builder = getattr(tokenizer, 'build_inputs_with_special_tokens', None)
    if callable(builder):
        return [{'input_ids': builder(ids)} for ids, _, _, _ in windows]
    encodings = getattr(encoded_text, 'encodings', None)
    backend = getattr(tokenizer, 'backend_tokenizer', None)
    processor = getattr(backend, 'post_processor', None)
    if not encodings or len(encodings) != 1 or processor is None:
        raise RuntimeError('Tokenizer cannot safely prepare token windows')
    encoding = deepcopy(encodings[0])
    encoding.truncate(capacity, stride=stride, direction='right')
    partitions = [encoding, *encoding.overflowing]
    if len(partitions) != len(windows):
        raise RuntimeError('Tokenizer changed token window boundaries')
    features = []
    special_count = tokenizer.num_special_tokens_to_add(pair=False)
    for partition, (ids, _, _, _) in zip(partitions, windows):
        if partition.ids != ids:
            raise RuntimeError('Tokenizer changed token window content')
        prepared = processor.process(partition, add_special_tokens=True)
        content = [token for token, special in zip(prepared.ids, prepared.special_tokens_mask) if not special]
        if content != ids or len(prepared.ids) != len(ids) + special_count:
            raise RuntimeError('Tokenizer changed content while adding special tokens')
        features.append({'input_ids': prepared.ids})
    return features


def validate_policy(policy, metadata):
    for key in ('weights_sha256', 'config_sha256', 'tokenizer_sha256', 'aggregation', 'max_length', 'stride', 'preprocessing'):
        if key not in metadata or key not in policy or policy[key] != metadata[key]:
            raise RuntimeError(f'Calibration policy does not match model: {key}')
    expected_runtime = validate_inference_runtime(metadata.get('inference_runtime'))
    policy_runtime = validate_inference_runtime(policy.get('inference_runtime'))
    if policy_runtime != expected_runtime:
        raise RuntimeError('Calibration policy does not match model: inference_runtime')
    if policy.get('schema_version') != 1 or not isinstance(policy.get('release_approved'), bool):
        raise RuntimeError('Invalid decision policy schema')
    for key in ('temperature', 'min_confidence', 'min_margin'):
        if not isinstance(policy.get(key), (int,float)) or not math.isfinite(policy[key]):
            raise RuntimeError(f'Invalid policy value: {key}')
    if policy['temperature'] <= 0 or not 0 <= policy['min_confidence'] <= 1 or not 0 <= policy['min_margin'] <= 1:
        raise RuntimeError('Invalid decision thresholds')
    if not isinstance(policy.get('min_tokens'), int) or policy['min_tokens'] < 1:
        raise RuntimeError('Invalid context requirement')
    if not isinstance(policy.get('validated_modes'), list) or not set(policy['validated_modes']) <= {'article','sentence','paragraph'}:
        raise RuntimeError('Invalid validated modes')
    if policy['release_approved'] and not policy.get('evaluation_report_sha256'):
        raise RuntimeError('Released policy must reference an evaluation report')
    return policy


@lru_cache(maxsize=1)
def get_policy():
    path = get_model_dir() / 'decision_policy.json'
    return validate_policy(json.loads(path.read_text()), model_metadata()) if path.exists() else None


def classify_scores(logits, token_count, mode, policy):
    values=np.asarray(logits)
    if values.shape!=(3,) or values.dtype.kind not in 'iuf' or not np.isfinite(values).all():
        raise ValueError('Expected exactly three finite numeric model logits')
    temperature=policy['temperature'] if policy else 1.
    if isinstance(temperature,bool) or not isinstance(temperature,(int,float)) or not math.isfinite(temperature) or temperature<=0:
        raise ValueError('Expected a finite positive temperature')
    # Subtract before dividing so even very large finite logits/temperatures do
    # not overflow into NaN and accidentally pass every confidence comparison.
    with np.errstate(over='ignore',under='ignore'):
        centered=values.astype(float)-float(values.max())
        scores=np.exp(centered/temperature)
    scores /= scores.sum()
    if not np.isfinite(scores).all():
        raise ValueError('Model scores could not be normalized')
    ranked = np.sort(scores)
    reason = None
    demo_mode = os.getenv('BIASCHECK_DEMO_MODE', '0') == '1'
    if not policy or not policy['release_approved']:
        if demo_mode:
            margin = float(ranked[-1] - ranked[-2])
            if token_count < 12:
                reason = 'insufficient_context'
            elif ranked[-1] < 0.55 or margin < 0.15:
                reason = 'uncertain'
            else:
                reason = 'demo_estimate'
        else:
            reason = 'model_not_validated'
    elif mode not in policy['validated_modes']:
        reason = 'mode_not_validated'
    elif token_count < policy['min_tokens']:
        reason = 'insufficient_context'
    elif ranked[-1] < policy['min_confidence'] or ranked[-1] - ranked[-2] < policy['min_margin']:
        reason = 'uncertain'
    return scores, reason


def predict_text(text, mode='article'):
    tokenizer, model = get_tokenizer(), get_model()
    encoded_text = tokenizer(text, add_special_tokens=False, truncation=False, verbose=False)
    ids = encoded_text['input_ids']
    if not ids:
        raise ValueError('No analyzable tokens')
    capacity = int(min(MAX_LENGTH, tokenizer.model_max_length)) - tokenizer.num_special_tokens_to_add(pair=False)
    windows = list(token_windows(ids, capacity))
    if len(windows) > get_settings().max_windows:
        raise ValueError('Article exceeds the processing limit. Please use shorter text.')
    features = prepare_window_features(tokenizer, encoded_text, windows, capacity)
    weighted = np.zeros(3, dtype=np.float64)
    batch_size = get_settings().batch_size
    with torch.inference_mode():
        for offset in range(0, len(windows), batch_size):
            batch = windows[offset:offset + batch_size]
            encoded = tokenizer.pad(features[offset:offset + batch_size], padding=True, return_tensors='pt', verbose=False)
            logits = model(**encoded).logits.cpu().numpy()
            for (_,_,_,weight), row in zip(batch, logits):
                weighted += row.astype(np.float64) * weight
    logits = weighted / len(ids)
    policy = get_policy()
    scores, reason = classify_scores(logits, len(ids), mode, policy)
    labels = {int(k): str(v).upper() for k,v in model.config.id2label.items()}
    label_id = int(scores.argmax())
    return {
        'label': labels[label_id] if reason in (None, 'demo_estimate') else None,
        'label_id': label_id if reason in (None, 'demo_estimate') else None,
        'raw_label': labels[label_id],
        'probabilities': {labels[i]: round(float(scores[i]), 6) for i in range(3)},
        'decision': 'classified' if reason in (None, 'demo_estimate') else 'abstained', 'reason': reason,
        'token_count': len(ids), 'tokens_processed': len(ids), 'chunk_count': len(windows),
        'truncated': False, 'calibrated': bool(policy and policy.get('calibration_data_sha256')),
        'logits': logits.tolist(),
    }
