"""Aggregate matched validation comparisons without publishing article text."""
import argparse
import json
from pathlib import Path
import numpy as np
from corpus_experiment import metrics


def bootstrap(rows, predictions, baseline):
    groups = sorted({r["event"] for r in rows})
    indices = {g: [i for i, r in enumerate(rows) if r["event"] == g] for g in groups}
    rng = np.random.default_rng(20261001)
    estimates, differences = [], []
    for _ in range(5000):
        chosen = [i for group in rng.choice(groups, len(groups), replace=True) for i in indices[group]]
        correct = [predictions[i] == rows[i]["label"] for i in chosen]
        original = [baseline[i] == rows[i]["label"] for i in chosen]
        estimates.append(float(np.mean(correct)))
        differences.append(float(np.mean(correct) - np.mean(original)))
    return {"method": "Event-cluster percentile bootstrap, 5000 draws, seed 20261001; exploratory validation uncertainty", "accuracy_interval_95": np.quantile(estimates, [.025, .975]).tolist(), "paired_accuracy_difference_vs_live_interval_95": np.quantile(differences, [.025, .975]).tolist()}


def align(rows, predictions):
    if len(predictions) != len(rows) or {r["id"] for r in predictions} != {r["id"] for r in rows}:
        raise ValueError("Missing, duplicate or unexpected prediction ids")
    by_id = {r["id"]: r["prediction"] for r in predictions}
    if not set(by_id.values()) <= {"LEFT", "CENTER", "RIGHT"}:
        raise ValueError("Unexpected prediction label")
    return [by_id[r["id"]] for r in rows]


def run(data, output):
    rows = [json.loads(s) for s in (data / "pbc-snippets-20261001/validation.jsonl").read_text().splitlines()]
    live = json.loads((data / "live-snippets-validation-20261001.json").read_text())
    baseline = align(rows, [{"id": r["id"], "prediction": r["response"]["overall"]["raw_label"]} for r in live["results"]])
    candidates = {"live_roberta": baseline}
    astra = [{"id": r["id"], "prediction": r["label"]} for p in sorted((data / "astra-snippets-validation-20261001").glob("batch-*.json")) for r in json.loads(p.read_text())["predictions"]]
    candidates["astra_medium_frozen_prompt"] = align(rows, astra)
    for dirname in ("pbc-snippets-tfidf-20261001", "pbc-minilm-20261001"):
        record = json.loads((data.parent / "checkpoints" / dirname / "training_results.json").read_text())
        for candidate in record["candidates"]:
            candidates[candidate["name"]] = align(rows, candidate["predictions"])
    finetuned = data.parent / "checkpoints/pbc-minilm-finetuned-20261001/training_results.json"
    if finetuned.exists():
        record = json.loads(finetuned.read_text())
        for epoch in record["history"]:
            candidates[f"finetuned_minilm_epoch{epoch['epoch']}"] = align(rows, epoch["predictions"])
    report = {"purpose": "Exploratory matched-context validation; not independent product accuracy", "manifest": json.loads((data / "pbc-snippets-20261001/manifest.json").read_text()), "live_model": live["health"], "models": {}, "release_approved": False, "reserved_test_evaluated": False}
    for name, predicted in candidates.items():
        report["models"][name] = {"metrics": metrics(rows, predicted), "uncertainty": bootstrap(rows, predicted, baseline), "predictions": [{"id": r["id"], "prediction": p, "reference": r["label"], "strict_agreement": r["strict_agreement"]} for r, p in zip(rows, predicted)]}
    high = [r for r in live["results"] if max(r["response"]["overall"]["probabilities"].values()) >= .95]
    gold = {r["id"]: r["label"] for r in rows}
    report["live_high_score"] = {"threshold": .95, "n": len(high), "incorrect": sum(r["response"]["overall"]["raw_label"] != gold[r["id"]] for r in high)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps({name: {k: value["metrics"][k] for k in ("accuracy", "macro_f1", "strict_agreement")} for name, value in report["models"].items()}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.output)
