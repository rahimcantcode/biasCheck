"""Frozen MiniLM features plus a trained classifier; development splits only."""
import argparse
import hashlib
import json
from pathlib import Path

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
FILES = ["config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "vocab.txt", "model.safetensors"]


def download(destination):
    import requests
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {"model": MODEL, "revision": REVISION, "files": {}}
    for name in FILES:
        path = destination / name
        if not path.exists():
            with requests.get(f"https://huggingface.co/{MODEL}/resolve/{REVISION}/{name}", stream=True, timeout=120) as response:
                response.raise_for_status()
                partial = path.with_suffix(path.suffix + ".partial")
                with partial.open("wb") as stream:
                    for chunk in response.iter_content(1024 * 1024):
                        stream.write(chunk)
                partial.rename(path)
        manifest["files"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
        print("downloaded", name, flush=True)
    (destination / "download_manifest.json").write_text(json.dumps(manifest, indent=2))


def encode(data, checkpoint, output):
    import numpy as np
    import torch
    from transformers import AutoModel, AutoTokenizer

    if output.exists():
        raise ValueError("Refusing to overwrite embeddings")
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
    model = AutoModel.from_pretrained(checkpoint, local_files_only=True).eval()
    arrays, records = {}, {}
    for split in ("train", "validation"):
        rows = [json.loads(s) for s in (data / f"{split}.jsonl").read_text().splitlines()]
        vectors = []
        for index, row in enumerate(rows):
            ids = tokenizer(row["text"], add_special_tokens=False, truncation=False)["input_ids"]
            aggregate = torch.zeros(model.config.hidden_size)
            covered = 0
            for start in range(0, len(ids), 222):
                end = min(start + 254, len(ids))
                inputs = tokenizer.prepare_for_model(ids[start:end], return_tensors="pt")
                inputs = {k: v.unsqueeze(0) for k, v in inputs.items()}
                with torch.inference_mode():
                    hidden = model(**inputs).last_hidden_state
                    mask = inputs["attention_mask"].unsqueeze(-1)
                    vector = (hidden * mask).sum(1) / mask.sum(1)
                    vector = torch.nn.functional.normalize(vector, dim=1)[0]
                weight = end - covered
                aggregate += vector * weight
                covered = end
                if end == len(ids):
                    break
            vectors.append(torch.nn.functional.normalize(aggregate, dim=0).numpy())
            if (index + 1) % 20 == 0:
                print(split, index + 1, "/", len(rows), flush=True)
        arrays[split] = np.stack(vectors)
        records[split] = {"ids": [r["id"] for r in rows], "data_sha256": hashlib.sha256((data / f"{split}.jsonl").read_bytes()).hexdigest()}
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez(output, **arrays)
    output.with_suffix(".json").write_text(json.dumps({"model": MODEL, "revision": REVISION, "pooling": "masked_mean_then_normalize; new-token-weighted windows then normalize", "capacity": 254, "stride": 32, "records": records}, indent=2))


def train(data, features, output):
    import joblib
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from corpus_experiment import metrics

    if output.exists():
        raise ValueError("Use a new output directory")
    rows = {split: [json.loads(s) for s in (data / f"{split}.jsonl").read_text().splitlines()] for split in ("train", "validation")}
    provenance = json.loads(features.with_suffix(".json").read_text())
    for split in rows:
        if provenance["records"][split]["ids"] != [r["id"] for r in rows[split]]:
            raise ValueError("Feature alignment mismatch")
        if provenance["records"][split]["data_sha256"] != hashlib.sha256((data / f"{split}.jsonl").read_bytes()).hexdigest():
            raise ValueError("Feature input hash mismatch")
    for field in ("event", "text_sha256", "id"):
        if {r[field] for r in rows["train"]} & {r[field] for r in rows["validation"]}:
            raise ValueError(f"Leaking {field}")
    arrays = np.load(features)
    output.mkdir(parents=True)
    reports = []
    for strength in (.1, 1., 10.):
        model = LogisticRegression(C=strength, class_weight="balanced", max_iter=1000, random_state=20261001)
        model.fit(arrays["train"], [r["label"] for r in rows["train"]])
        predictions = model.predict(arrays["validation"]).tolist()
        report = {"name": f"minilm_C{strength}", "metrics": metrics(rows["validation"], predictions), "predictions": [{"id": r["id"], "prediction": p} for r, p in zip(rows["validation"], predictions)]}
        reports.append(report)
        joblib.dump(model, output / f"{report['name']}.joblib")
        print(report["name"], report["metrics"]["accuracy"], report["metrics"]["macro_f1"], flush=True)
    (output / "training_results.json").write_text(json.dumps({"purpose": "Frozen neural encoder plus supervised trained head; test not opened", "encoder": provenance, "train_n": len(rows["train"]), "best": max(reports, key=lambda r: r["metrics"]["macro_f1"])["name"], "candidates": reports, "release_approved": False}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["download", "encode", "train"])
    parser.add_argument("--data", type=Path)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--features", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "download":
        download(args.output)
    elif args.mode == "encode":
        encode(args.data, args.checkpoint, args.output)
    else:
        train(args.data, args.features, args.output)
