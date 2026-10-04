"""Direct inference with the published political-leaning DeBERTa checkpoint."""
from functools import lru_cache
import json
import os
from pathlib import Path
import torch
from tokenizers import Tokenizer
from transformers import AutoModelForSequenceClassification
try:
    from .config import get_settings
except ImportError:
    from config import get_settings

CHECKPOINT = json.loads(Path(__file__).with_name('political_checkpoint.json').read_text())
LABEL_MAP = {int(k): v for k, v in CHECKPOINT['label_map'].items()}
MAX_LENGTH = 512

def get_model_dir():
    path = get_settings().model_dir
    for name in ('config.json', 'model.safetensors', 'tokenizer.json', 'checkpoint.json'):
        if not (path / name).is_file():
            raise RuntimeError('Run python backend/download_model.py to download political-leaning DeBERTa first.')
    if json.loads((path / 'checkpoint.json').read_text()) != CHECKPOINT:
        raise RuntimeError('The model directory does not contain the selected political-leaning DeBERTa revision.')
    return path

@lru_cache(maxsize=1)
def get_tokenizer():
    tokenizer = Tokenizer.from_file(str(get_model_dir() / 'tokenizer.json'))
    tokenizer.no_truncation()
    tokenizer.enable_padding(pad_id=0, pad_token='[PAD]')
    return tokenizer

@lru_cache(maxsize=1)
def get_model():
    torch.set_num_threads(max(1, int(os.getenv('BIASCHECK_TORCH_THREADS', '2'))))
    model, info = AutoModelForSequenceClassification.from_pretrained(
        get_model_dir(), local_files_only=True, use_safetensors=True,
        trust_remote_code=False, output_loading_info=True,
    )
    if any(info.get(key) for key in ('missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs')):
        raise RuntimeError('The pretrained weights could not be loaded completely.')
    native_labels = {k: v.upper() for k, v in model.config.id2label.items()}
    generic_labels = {i: f'LABEL_{i}' for i in range(3)}
    # The pinned model card documents 0=left, 1=center, 2=right; its config uses LABEL_n.
    if model.config.model_type != CHECKPOINT['model_type'] or native_labels not in (LABEL_MAP, generic_labels):
        raise RuntimeError('Unexpected model architecture or political label mapping.')
    model.eval()
    return model

def model_metadata():
    return {key: CHECKPOINT[key] for key in ('model_id', 'revision', 'license')}

def predict_sentences(sentences):
    """Batch complete sentences. Never silently discard the end of a sentence."""
    tokenizer, model = get_tokenizer(), get_model()
    results = []
    batch_size = get_settings().batch_size
    with torch.inference_mode():
        for start in range(0, len(sentences), batch_size):
            encodings = tokenizer.encode_batch(sentences[start:start + batch_size])
            if any(len(item.ids) > MAX_LENGTH for item in encodings):
                raise ValueError('One sentence exceeds the model limit of 512 tokens. Please split that sentence and try again.')
            encoded = {
                'input_ids': torch.tensor([item.ids for item in encodings]),
                'attention_mask': torch.tensor([item.attention_mask for item in encodings]),
                'token_type_ids': torch.tensor([item.type_ids for item in encodings]),
            }
            scores = torch.softmax(model(**encoded).logits, dim=-1)
            if not torch.isfinite(scores).all():
                raise RuntimeError('The model returned non-finite scores.')
            for row in scores:
                label_id = int(row.argmax().item())
                results.append({
                    'label': LABEL_MAP[label_id], 'label_id': label_id,
                    'probabilities': {LABEL_MAP[i]: round(float(row[i]), 6) for i in LABEL_MAP},
                })
    return results

def predict_text(text):
    return predict_sentences([text])[0]
