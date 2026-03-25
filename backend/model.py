from functools import lru_cache
from pathlib import Path
from typing import Dict, TypedDict

import torch
from tokenizers import Tokenizer
from transformers import RobertaForSequenceClassification


LABEL_MAP = {
    0: "LEFT",
    1: "RIGHT",
    2: "CENTER",
}
MODEL_DIR = Path(__file__).resolve().parent.parent / "bias_model"
MAX_LENGTH = 512


class PredictionOutput(TypedDict):
    label: str
    label_id: int
    probabilities: Dict[str, float]


@lru_cache(maxsize=1)
def get_tokenizer():
    tokenizer = Tokenizer.from_file(str(MODEL_DIR / "tokenizer.json"))
    tokenizer.enable_truncation(max_length=MAX_LENGTH)
    tokenizer.enable_padding(length=MAX_LENGTH, pad_id=1, pad_token="<pad>")
    return tokenizer


@lru_cache(maxsize=1)
def get_model():
    model = RobertaForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()
    return model


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
