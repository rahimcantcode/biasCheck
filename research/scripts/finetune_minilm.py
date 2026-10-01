"""CPU-sized partial transformer fine-tuning on development data only.

Train the upper two encoder blocks and a masked-mean classification head.
Ambiguous source labels receive 0.25 weight; this is a development hypothesis.
"""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import torch
from safetensors.torch import save_file
from transformers import AutoModel, AutoTokenizer

LABELS = ["LEFT", "CENTER", "RIGHT"]


def macro_f1(gold, predicted):
    values = []
    for label in range(3):
        tp = sum(g == label and p == label for g, p in zip(gold, predicted))
        fp = sum(g != label and p == label for g, p in zip(gold, predicted))
        fn = sum(g == label and p != label for g, p in zip(gold, predicted))
        values.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.)
    return sum(values) / 3


def run(data, checkpoint, output):
    if output.exists():
        raise ValueError("Use an empty new experiment directory")
    torch.set_num_threads(2)
    torch.manual_seed(20261001)
    random.seed(20261001)
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
    encoder = AutoModel.from_pretrained(checkpoint, local_files_only=True)
    for parameter in encoder.parameters():
        parameter.requires_grad = False
    for layer in encoder.encoder.layer[-2:]:
        for parameter in layer.parameters():
            parameter.requires_grad = True
    head = torch.nn.Linear(encoder.config.hidden_size, 3)
    optimizer = torch.optim.AdamW([
        {"params": [p for p in encoder.parameters() if p.requires_grad], "lr": 2e-5},
        {"params": head.parameters(), "lr": 1e-3},
    ], weight_decay=.01)
    rows = {split: [json.loads(s) for s in (data / f"{split}.jsonl").read_text().splitlines()] for split in ("train", "validation")}
    for field in ("event", "text_sha256", "id"):
        if {r[field] for r in rows["train"]} & {r[field] for r in rows["validation"]}:
            raise ValueError(f"Leaking {field}")
    windows = {}
    for split, items in rows.items():
        windows[split] = []
        for row in items:
            ids = tokenizer(row["text"], add_special_tokens=False, truncation=False)["input_ids"]
            parts, previous_end = [], 0
            for start in range(0, len(ids), 222):
                end = min(start + 254, len(ids))
                parts.append((tokenizer.prepare_for_model(ids[start:end]), (end - previous_end) / len(ids)))
                previous_end = end
                if end == len(ids):
                    break
            windows[split].append(parts)
    output.mkdir(parents=True)
    record = {"seed": 20261001, "base": json.loads((checkpoint / "download_manifest.json").read_text()), "training": "Upper two encoder blocks + masked-mean linear head; 3 epochs; article-window weighted loss; disputed-label weight .25; label smoothing .1", "data_sha256": {s: hashlib.sha256((data / f"{s}.jsonl").read_bytes()).hexdigest() for s in rows}, "history": [], "release_approved": False}
    class_counts = [sum(r["label"] == label for r in rows["train"]) for label in LABELS]
    class_weights = torch.tensor([len(rows["train"]) / (3 * n) for n in class_counts])

    def forward(parts):
        encoded = tokenizer.pad([p[0] for p in parts], padding=True, return_tensors="pt")
        hidden = encoder(**encoded).last_hidden_state
        mask = encoded["attention_mask"].unsqueeze(-1)
        pooled = (hidden * mask).sum(1) / mask.sum(1)
        return head(pooled)

    started, best = time.monotonic(), -1.
    for epoch in range(3):
        encoder.train()
        head.train()
        indices = list(range(len(rows["train"])))
        random.Random(20261001 + epoch).shuffle(indices)
        loss_total = 0.
        for offset in range(0, len(indices), 4):
            indices_batch = indices[offset:offset + 4]
            optimizer.zero_grad(set_to_none=True)
            for index in indices_batch:
                row, parts = rows["train"][index], windows["train"][index]
                for part_offset in range(0, len(parts), 4):
                    subset = parts[part_offset:part_offset + 4]
                    logits = forward(subset)
                    target = torch.full((len(subset),), LABELS.index(row["label"]), dtype=torch.long)
                    losses = torch.nn.functional.cross_entropy(logits, target, weight=class_weights, label_smoothing=.1, reduction="none")
                    weights = torch.tensor([p[1] for p in subset])
                    loss = (losses * weights).sum() * (1. if row["strict_agreement"] else .25) / len(indices_batch)
                    loss.backward()
                    loss_total += loss.item()
            torch.nn.utils.clip_grad_norm_([p for p in list(encoder.parameters()) + list(head.parameters()) if p.requires_grad], 1.)
            optimizer.step()
            if offset % 20 == 0:
                print("epoch", epoch + 1, "documents", offset, "/", len(indices), flush=True)
        encoder.eval()
        head.eval()
        predictions = []
        with torch.inference_mode():
            for row, parts in zip(rows["validation"], windows["validation"]):
                aggregate = torch.zeros(3)
                for offset in range(0, len(parts), 4):
                    subset = parts[offset:offset + 4]
                    aggregate += (forward(subset) * torch.tensor([p[1] for p in subset]).unsqueeze(-1)).sum(0)
                predictions.append({"id": row["id"], "prediction": LABELS[int(aggregate.argmax())], "logits": aggregate.tolist()})
        gold = [LABELS.index(r["label"]) for r in rows["validation"]]
        pred = [LABELS.index(r["prediction"]) for r in predictions]
        f1 = macro_f1(gold, pred)
        history = {"epoch": epoch + 1, "macro_f1": f1, "accuracy": sum(g == p for g, p in zip(gold, pred)) / len(gold), "weighted_train_loss_sum": loss_total, "elapsed_seconds": time.monotonic() - started, "predictions": predictions}
        record["history"].append(history)
        if f1 > best:
            best = f1
            encoder.save_pretrained(output / "best-encoder", safe_serialization=True)
            tokenizer.save_pretrained(output / "best-encoder")
            save_file(head.state_dict(), str(output / "best-head.safetensors"))
            record["best_epoch"] = epoch + 1
        (output / "training_results.json").write_text(json.dumps(record, indent=2))
        print(json.dumps({k: v for k, v in history.items() if k != "predictions"}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.checkpoint, args.output)
