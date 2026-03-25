from functools import lru_cache
from pathlib import Path
from typing import Dict, TypedDict

import torch
from tokenizers import Tokenizer
from transformers import RobertaForSequenceClassification
try:
    from .config import get_settings
except ImportError:  # pragma: no cover - supports `uvicorn main:app` from backend/
    from config import get_settings


LABEL_MAP = {
    0: "LEFT",
    1: "RIGHT",
    2: "CENTER",
}
MAX_LENGTH = 512


class PredictionOutput(TypedDict):
    label: str
    label_id: int
    probabilities: Dict[str, float]


@lru_cache(maxsize=1)
def get_tokenizer():
    model_dir = get_model_dir()
    tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    tokenizer.enable_truncation(max_length=MAX_LENGTH)
    tokenizer.enable_padding(length=MAX_LENGTH, pad_id=1, pad_token="<pad>")
    return tokenizer


@lru_cache(maxsize=1)
def get_model():
    model = RobertaForSequenceClassification.from_pretrained(get_model_dir())
    model.eval()
    return model


def get_model_dir() -> Path:
    model_dir = get_settings().model_dir
    required_files = ("config.json", "model.safetensors", "tokenizer.json")
    missing_files = [filename for filename in required_files if not (model_dir / filename).exists()]
    if missing_files:
        raise FileNotFoundError(
            f"Model directory not ready at '{model_dir}'. Missing: {', '.join(missing_files)}."
        )
    return model_dir


def predict_text(text: str) -> PredictionOutput:
    tokenizer = get_tokenizer()
    model = get_model()

    encoding = tokenizer.encode(text)
    encoded = {
        "input_ids": torch.tensor([encoding.ids], dtype=torch.long),
        "attention_mask": torch.tensor([encoding.attention_mask], dtype=torch.long),
    }

    with torch.no_grad():
        logits = model(**encoded).logits
        scores = torch.softmax(logits, dim=-1)[0]

    probabilities = {
        LABEL_MAP[index]: round(float(scores[index]), 6)
        for index in sorted(LABEL_MAP.keys())
    }
    label_id = int(torch.argmax(scores).item())

    return {
        "label": LABEL_MAP[label_id],
        "label_id": label_id,
        "probabilities": probabilities,
    }
