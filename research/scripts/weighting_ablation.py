"""Training-only annotation-weight ablations on frozen, aligned embeddings."""
import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

from corpus_experiment import LABELS, metrics

REGIMES = ("hard", "downweight_disputes", "worker_distribution", "unanimous_only")


def weighted_targets(rows, regime):
    if regime not in REGIMES or not rows:
        raise ValueError("Unknown regime or empty training set")
    indices, labels, base = [], [], []
    for i, row in enumerate(rows):
        workers = [label.upper() for label in row["worker_labels"]]
        if len(workers) != 2 or any(label not in LABELS for label in workers):
            raise ValueError("Expected two valid worker labels")
        if row["label"] not in LABELS or row["strict_agreement"] != (workers[0] == workers[1]):
            raise ValueError("Invalid annotation provenance")
        if regime == "unanimous_only" and not row["strict_agreement"]:
            continue
        targets = workers if regime == "worker_distribution" else [row["label"]]
        weight = .25 if regime == "downweight_disputes" and not row["strict_agreement"] else 1.
        for label in targets:
            indices.append(i)
            labels.append(label)
            base.append(weight / len(targets))
    masses = {label: sum(w for y, w in zip(labels, base) if y == label) for label in LABELS}
    if any(mass <= 0 for mass in masses.values()):
        raise ValueError("All classes must have positive training mass")
    # Equal class mass and fixed total loss weight keep C comparable across regimes.
    weights = np.array([w / masses[y] * len(rows) / len(LABELS) for y, w in zip(labels, base)])
    return np.array(indices), labels, weights, masses


def run(data, features, output):
    if output.exists():
        raise ValueError("Refusing to overwrite an experiment")
    rows = {s: [json.loads(line) for line in (data / f"{s}.jsonl").read_text().splitlines()]
            for s in ("train", "validation")}
    provenance = json.loads(features.with_suffix(".json").read_text())
    arrays = np.load(features)
    for split, items in rows.items():
        ids = [r["id"] for r in items]
        if len(set(ids)) != len(ids) or provenance["records"][split]["ids"] != ids:
            raise ValueError("Duplicate or misaligned IDs")
        if provenance["records"][split]["data_sha256"] != hashlib.sha256((data / f"{split}.jsonl").read_bytes()).hexdigest():
            raise ValueError("Input hash mismatch")
        if arrays[split].shape[0] != len(items) or not np.isfinite(arrays[split]).all():
            raise ValueError("Invalid feature array")
    for field in ("event", "text_sha256", "id"):
        if {r[field] for r in rows["train"]} & {r[field] for r in rows["validation"]}:
            raise ValueError(f"Leaking {field}")
    output.mkdir(parents=True)
    record = {"purpose": "Exploratory validation ablation; research-only; test never opened",
              "selection_rule": "Highest all-validation macro-F1; ties favor earlier listed regime/C",
              "regimes": list(REGIMES), "C": [.1, 1., 10.], "seed": 20261001,
              "class_weight": None, "weight_sum": len(rows["train"]), "max_iter": 1000,
              "encoder": provenance, "features_sha256": hashlib.sha256(features.read_bytes()).hexdigest(),
              "release_approved": False, "candidates": []}
    (output / "protocol.json").write_text(json.dumps(record, indent=2))
    for regime in REGIMES:
        indices, labels, weights, masses = weighted_targets(rows["train"], regime)
        for strength in record["C"]:
            model = LogisticRegression(C=strength, class_weight=None, max_iter=1000, random_state=20261001)
            model.fit(arrays["train"][indices], labels, sample_weight=weights)
            pred = model.predict(arrays["validation"]).tolist()
            strict = [(r, p) for r, p in zip(rows["validation"], pred) if r["strict_agreement"]]
            name = f"{regime}_C{strength}"
            path = output / f"{name}.joblib"
            joblib.dump(model, path)
            result = {"name": name, "C": strength, "regime": regime,
                      "unique_training_n": len(set(indices.tolist())), "expanded_training_n": len(labels),
                      "base_class_mass": masses, "weight_sum": float(weights.sum()),
                      "balanced_class_mass": {y: float(weights[np.array(labels) == y].sum()) for y in LABELS},
                      "n_iter": model.n_iter_.tolist(), "model_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "metrics": metrics(rows["validation"], pred),
                      "strict_metrics": metrics([r for r, _ in strict], [p for _, p in strict]),
                      "predictions": [{"id": r["id"], "prediction": p} for r, p in zip(rows["validation"], pred)]}
            record["candidates"].append(result)
            print(name, result["metrics"]["accuracy"], result["metrics"]["macro_f1"], result["strict_metrics"]["accuracy"], flush=True)
    record["best"] = max(record["candidates"], key=lambda r: r["metrics"]["macro_f1"])["name"]
    (output / "training_results.json").write_text(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("data", "features", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.features, args.output)
