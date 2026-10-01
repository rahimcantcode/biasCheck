"""Diagnose annotation disagreement without changing gold or fitting a model."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from corpus_experiment import LABELS, metrics
from summarize_corpus_experiment import align


def diagnose(rows, predictions):
    if not rows or len(rows) != len(predictions):
        raise ValueError("Nonempty aligned inputs required")
    records = []
    for row, prediction in zip(rows, predictions):
        workers = [label.upper() for label in row["worker_labels"]]
        if len(workers) != 2 or any(y not in LABELS for y in workers + [prediction, row["label"]]):
            raise ValueError("Invalid labels")
        if row["strict_agreement"] != (workers[0] == workers[1]):
            raise ValueError("Inconsistent agreement provenance")
        records.append({"id": row["id"], "released_label": row["label"], "worker_labels": workers,
                        "prediction": prediction, "unanimous": row["strict_agreement"],
                        "released_match": prediction == row["label"],
                        "worker_match_fraction": sum(prediction == y for y in workers) / 2,
                        "matches_neither_worker": prediction not in workers})
    groups = {}
    for name, selected in (("all", records), ("unanimous", [r for r in records if r["unanimous"]]),
                           ("disputed", [r for r in records if not r["unanimous"]])):
        n = len(selected)
        groups[name] = {"n": n, "released_matches": sum(r["released_match"] for r in selected),
                        "released_agreement": sum(r["released_match"] for r in selected) / n if n else None,
                        "mean_worker_agreement": sum(r["worker_match_fraction"] for r in selected) / n if n else None,
                        "matches_neither_worker": sum(r["matches_neither_worker"] for r in selected),
                        "released_errors_matching_one_worker": sum(not r["released_match"] and r["worker_match_fraction"] > 0 for r in selected)}
    return {"groups": groups, "released_metrics": metrics(rows, predictions), "records": records}


def run(data, comparison, weighting, output):
    if output.exists():
        raise ValueError("Use a new output path")
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate reference IDs")
    prior = json.loads(comparison.read_text())
    ablation = json.loads(weighting.read_text())
    selected = ("live_roberta", "astra_medium_frozen_prompt", "word_C1.0", "minilm_C0.1")
    candidates = {name: prior["models"][name]["predictions"] for name in selected}
    candidates[ablation["best"]] = next(c["predictions"] for c in ablation["candidates"] if c["name"] == ablation["best"])
    records = {name: diagnose(rows, align(rows, predictions)) for name, predictions in candidates.items()}
    report = {"purpose": "Post hoc annotation error analysis, not independent accuracy or relabeling",
              "reserved_test_read": False, "release_approved": False,
              "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (data, comparison, weighting)},
              "validation_n": len(rows), "event_n": len({r["event"] for r in rows}),
              "worker_pair_counts": dict(Counter("/".join(sorted(y.upper() for y in r["worker_labels"])) for r in rows)),
              "released_label_outside_worker_pair_n": sum(r["label"] not in [y.upper() for y in r["worker_labels"]] for r in rows),
              "models": records,
              "cautions": ["Worker agreement is not an alternative product-accuracy claim",
                           "Two annotators are not independent gold; unanimity is a selected subset",
                           "Prior candidates selected on this validation set; no new model selection",
                           "Do not relabel toward model predictions or tune on the reserved test"]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps({"worker_pair_counts": report["worker_pair_counts"], "event_n": report["event_n"],
                      "models": {name: result["groups"] for name, result in records.items()}}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("data", "comparison", "weighting", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.comparison, args.weighting, args.output)
