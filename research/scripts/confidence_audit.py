"""Fixed-score development audit; never fits calibration or selects a threshold."""
import argparse
import hashlib
import json
import math
from pathlib import Path

LABELS = ("LEFT", "CENTER", "RIGHT")
THRESHOLDS = (.5, .8, .9, .95, .99, .999)


def align(rows, live):
    references = {r["id"]: r for r in rows}
    responses = {r["id"]: r for r in live}
    if not rows or len(references) != len(rows) or len(responses) != len(live) or references.keys() != responses.keys():
        raise ValueError("Unique, complete, aligned IDs required")
    records = []
    for row in rows:
        overall = responses[row["id"]]["response"]["overall"]
        probabilities = overall["probabilities"]
        if set(probabilities) != set(LABELS):
            raise ValueError("Unexpected probability labels")
        values = list(probabilities.values())
        if any(not math.isfinite(v) or not 0 <= v <= 1 for v in values) or abs(sum(values) - 1) > 1e-5:
            raise ValueError("Invalid probability simplex")
        prediction = overall["raw_label"]
        if row["label"] not in LABELS or prediction not in LABELS or probabilities[prediction] != max(values):
            raise ValueError("Invalid label or argmax mismatch")
        records.append({"id": row["id"], "reference": row["label"], "prediction": prediction,
                        "displayed_label": overall.get("label"), "decision": overall.get("decision"),
                        "unanimous": row["strict_agreement"], "probabilities": probabilities,
                        "confidence": max(values), "correct": prediction == row["label"]})
    return records


def summarize(records):
    n = len(records)
    if not n:
        return {"n": 0}
    correct = sum(r["correct"] for r in records)
    bins = []
    for index in range(10):
        selected = [r for r in records if min(int(r["confidence"] * 10), 9) == index]
        bins.append({"lower": index / 10, "upper": (index + 1) / 10, "n": len(selected),
                     "matches": sum(r["correct"] for r in selected),
                     "mean_confidence": sum(r["confidence"] for r in selected) / len(selected) if selected else None})
    ece = sum(abs(b["mean_confidence"] * b["n"] - b["matches"]) for b in bins if b["n"]) / n
    positive = [r["confidence"] for r in records if r["correct"]]
    negative = [r["confidence"] for r in records if not r["correct"]]
    auc = (sum((a > b) + .5 * (a == b) for a in positive for b in negative) / (len(positive) * len(negative))) if positive and negative else None
    thresholds = []
    for threshold in THRESHOLDS:
        selected = [r for r in records if r["confidence"] >= threshold]
        matches = sum(r["correct"] for r in selected)
        thresholds.append({"threshold": threshold, "n": len(selected), "matches": matches,
                           "coverage": len(selected) / n, "agreement": matches / len(selected) if selected else None})
    minimum = math.ceil(.8 * n)
    displayed = [r for r in records if r["decision"] == "classified" and r["displayed_label"] in LABELS]
    displayed_matches = sum(r["displayed_label"] == r["reference"] for r in displayed)
    return {"n": n, "matches": correct, "agreement": correct / n,
            "displayed_decisions": {"n": len(displayed), "matches": displayed_matches,
                "coverage": len(displayed) / n,
                "agreement": displayed_matches / len(displayed) if displayed else None},
            "mean_confidence": sum(r["confidence"] for r in records) / n,
            "top_label_ece_10_bins": ece, "bins": bins, "confidence_correctness_auc": auc,
            "brier_multiclass_sum": sum(sum((r["probabilities"][label] - (r["reference"] == label)) ** 2 for label in LABELS) for r in records) / n,
            "nll_epsilon_1e_12": -sum(math.log(max(r["probabilities"][r["reference"]], 1e-12)) for r in records) / n,
            "thresholds": thresholds, "oracle_at_minimum_coverage": {"requested_coverage": .8,
                "minimum_retained": minimum, "actual_coverage": minimum / n,
                "agreement_upper_bound": min(correct, minimum) / minimum}}


def run(data, responses, output):
    if output.exists():
        raise ValueError("Refusing to overwrite report")
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    live = json.loads(responses.read_text())
    data_hash = hashlib.sha256(data.read_bytes()).hexdigest()
    if data_hash != live["input_sha256"]:
        raise ValueError("Reference dataset differs from prediction input")
    records = align(rows, live["results"])
    report = {"purpose": "Post hoc development confidence audit, not independent product accuracy",
              "release_approved": False, "reserved_test_read": False, "calibration_fitted": False,
              "data_sha256": data_hash, "responses_sha256": hashlib.sha256(responses.read_bytes()).hexdigest(),
              "model": live["health"], "records": records,
              "groups": {"all": summarize(records),
                         "unanimous": summarize([r for r in records if r["unanimous"]]),
                         "disputed": summarize([r for r in records if not r["unanimous"]])},
              "cautions": ["Reference labels are disputed and task-mismatched; unanimity is a selected subset",
                           "Rounded API scores used as stored; NLL clips zeros at 1e-12",
                           "NLL uses natural logarithms; threshold coverage denominator is the named subgroup",
                           "Thresholds describe raw argmax predictions, not an adopted UI policy; displayed decisions reported separately",
                           "Brier is the sum across three classes, range 0 to 2",
                           "Fixed ECE bins are left-inclusive, right-exclusive except final bin includes 1",
                           "AUC ranks correct over incorrect with half credit for ties; undefined if one group absent",
                           "Oracle bound assumes unchanged predictions and perfect selection on this finite sample only",
                           "No threshold selected, no calibration fitted, no abstention policy approved"]}
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["groups"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("data", "responses", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.responses, args.output)
