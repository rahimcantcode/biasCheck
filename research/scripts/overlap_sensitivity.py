"""Report a reviewed development-only exclusion alongside unchanged full scores."""
import argparse
import hashlib
import json
from pathlib import Path

from corpus_experiment import metrics
from summarize_corpus_experiment import align


def run(data, comparison, review, output):
    if output.exists():
        raise ValueError("Use a new output path")
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    decision = json.loads(review.read_text())
    excluded = set(decision["validation_ids"])
    if not excluded or not excluded < {r["id"] for r in rows}:
        raise ValueError("Exclusion must be a nonempty proper subset")
    previous = json.loads(comparison.read_text())
    retained = [i for i, r in enumerate(rows) if r["id"] not in excluded]
    result = {"purpose": "Post hoc sensitivity only; no split change or independent accuracy claim",
              "excluded_ids": sorted(excluded), "release_approved": False, "reserved_test_read": False,
              "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (data, comparison, review)}, "models": {}}
    for name in ("live_roberta", "astra_medium_frozen_prompt", "word_C1.0", "minilm_C0.1"):
        predictions = align(rows, previous["models"][name]["predictions"])
        full = metrics(rows, predictions)
        subset = metrics([rows[i] for i in retained], [predictions[i] for i in retained])
        result["models"][name] = {"all_validation": full, "excluding_reviewed_family": subset}
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps({name: {group: {"n": value["n"], "agreement": value["accuracy"], "macro_f1": value["macro_f1"]}
                             for group, value in model.items()} for name, model in result["models"].items()}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("data", "comparison", "review", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.comparison, args.review, args.output)
