"""Experimental political entailment engine. Scores are not calibrated confidence."""
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_ID = 'mlburnham/Political_DEBATE_large_v1.0'
REVISION = '1a3aff1ecb97ad93a6de598f7414b1707de7e7c3'
HYPOTHESES = {
    'politics': 'This text is about politics.',
    'policy': 'This text is about government policy.',
    'LEFT': 'The author of this text supports politically liberal positions.',
    'RIGHT': 'The author of this text supports politically conservative positions.',
    'CENTER': 'This text reports political information without taking a political side.',
    'mixed': 'The author endorses a combination of both liberal and conservative political positions.',
}
LABELS = ['LEFT', 'CENTER', 'RIGHT']
MAX_WINDOWS = 12

@lru_cache(maxsize=1)
def model_path():
    return Path(os.environ.get('BIASCHECK_NLI_MODEL_DIR', str(Path(__file__).resolve().parents[1] / 'research/checkpoints/political-debate-large')))

@lru_cache(maxsize=1)
def verify_checkpoint():
    manifest = json.loads(Path(__file__).with_name("nli_checkpoint.json").read_text())
    for name, expected in manifest["files"].items():
        digest = hashlib.sha256()
        with (model_path() / name).open("rb") as stream:
            for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise RuntimeError(f"Checkpoint integrity check failed: {name}")
    return manifest

@lru_cache(maxsize=1)
def get_tokenizer():
    verify_checkpoint()
    return AutoTokenizer.from_pretrained(model_path(), local_files_only=True)

@lru_cache(maxsize=1)
def get_model():
    verify_checkpoint()
    torch.set_num_threads(max(1, min(4, int(os.environ.get('BIASCHECK_TORCH_THREADS', '2')))))
    model, info = AutoModelForSequenceClassification.from_pretrained(model_path(), local_files_only=True, output_loading_info=True)
    if any(info.get(k) for k in ('missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs')):
        raise RuntimeError('Incomplete or incompatible political entailment checkpoint')
    if model.config.id2label != {0: 'entailment', 1: 'not_entailment'}:
        raise RuntimeError('Unexpected entailment label mapping')
    return model.eval()

def get_policy():
    return None

@lru_cache(maxsize=1)
def model_metadata():
    manifest = verify_checkpoint()
    return {'engine': 'political_nli', 'model_id': MODEL_ID, 'revision': REVISION,
            'weights_sha256': manifest['files']['model.safetensors'], 'artifact_sha256': manifest['files'], 'aggregation': 'overlapping_windows_mean_entailment_v1',
            'decision_rules': 'development_v2_mixed_guard', 'preprocessing': 'plain_text_exact_url_article_extraction_v2',
            'validation_status': 'development_only', 'release_approved': False,
            'hypotheses': HYPOTHESES, 'score_type': 'independent_entailment'}

def assess(scores, token_count):
    """Conservative development rules, not fitted or validated operating thresholds."""
    if token_count < 12:
        return 'insufficient_context', None
    if max(scores['politics'], scores['policy']) < 0.5:
        return 'nonpolitical', None
    ranked = sorted(LABELS, key=lambda label: scores[label], reverse=True)
    if scores[ranked[0]] < 0.8 or scores[ranked[0]] - scores[ranked[1]] < 0.4:
        return 'uncertain', None
    if ranked[0] in ('LEFT', 'RIGHT') and scores.get('mixed', 0.0) >= 0.8:
        return 'mixed_or_conflicting', None
    return 'tentative', ranked[0]

def predict_text(text, mode='article'):
    tok = get_tokenizer()
    encoded = tok(text, add_special_tokens=False, return_offsets_mapping=True)
    offsets = encoded['offset_mapping']
    count = len(offsets)
    # Reserve paired hypothesis and special-token space. Never discard the tail.
    capacity = 512 - max(len(tok(h, add_special_tokens=False)['input_ids']) for h in HYPOTHESES.values()) - tok.num_special_tokens_to_add(pair=True) - 4
    windows = []
    start = 0
    while start < count:
        end = min(start + capacity, count)
        windows.append((start, end))
        if end == count:
            break
        start = end - 64
    if len(windows) > MAX_WINDOWS:
        raise ValueError('Text exceeds the experimental engine limit of 12 windows. Please submit a shorter article.')
    scores = {key: 0.0 for key in HYPOTHESES}
    window_scores = []
    for start, end in windows:
        passage = text[offsets[start][0]:offsets[end - 1][1]]
        current = {}
        for offset in range(0, len(HYPOTHESES), 2):
            keys = list(HYPOTHESES)[offset:offset + 2]
            inputs = tok([passage] * len(keys), [HYPOTHESES[k] for k in keys], padding=True, return_tensors='pt')
            if inputs['input_ids'].shape[1] > 512:
                raise ValueError('Tokenization exceeds model capacity. Please use shorter text.')
            with torch.inference_mode():
                values = get_model()(**inputs).logits.softmax(-1)[:, 0].tolist()
            current.update(zip(keys, values))
        window_scores.append(current)
        for key in scores:
            scores[key] += current[key] / len(windows)
    assessment, tentative = assess(scores, count)
    # Opposing positions in different windows must not be averaged into a clear stance.
    window_labels = {assess(item, count)[1] for item in window_scores}
    if 'LEFT' in window_labels and 'RIGHT' in window_labels:
        assessment, tentative = 'mixed_or_conflicting', None
    return {'label': None, 'label_id': None, 'raw_label': max(LABELS, key=lambda key: scores[key]),
            'probabilities': {key: scores[key] for key in LABELS}, 'decision': 'abstained',
            'reason': 'experimental_model_not_validated', 'assessment': assessment,
            'tentative_label': tentative, 'relevance_scores': {key: scores[key] for key in ('politics', 'policy')},
            'score_type': 'independent_entailment', 'token_count': count, 'tokens_processed': count,
            'chunk_count': len(windows), 'truncated': False, 'calibrated': False}
