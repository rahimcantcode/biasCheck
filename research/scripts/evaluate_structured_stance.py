"""Evaluate a frozen structured comparator without hiding withheld predictions."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import statistics

from stance_contract import STANCES, validate

LABELS = ["LEFT", "CENTER", "RIGHT"]


def measures(rows, predictions):
    if not rows or len(rows) != len(predictions):
        raise ValueError("Expected a nonempty complete comparison")
    if any(r["label"] not in LABELS for r in rows) or any(p not in STANCES for p in predictions):
        raise ValueError("Unexpected label")
    matrix = [[sum(r["label"] == gold and p == pred for r, p in zip(rows, predictions))
               for pred in STANCES] for gold in LABELS]
    per_class = {}
    for label in LABELS:
        tp = sum(r["label"] == p == label for r, p in zip(rows, predictions))
        support = sum(r["label"] == label for r in rows)
        predicted = predictions.count(label)
        per_class[label] = {"support": support, "precision": tp / predicted if predicted else 0.,
                            "recall": tp / support if support else 0.,
                            "f1": 2 * tp / (support + predicted) if support + predicted else 0.}
    covered = [i for i, p in enumerate(predictions) if p in LABELS]
    return {"n": len(rows), "released_label_matches": sum(r["label"] == p for r, p in zip(rows, predictions)),
            "released_label_agreement_all": sum(r["label"] == p for r, p in zip(rows, predictions)) / len(rows),
            "macro_f1_three_reference_classes_all": sum(r["f1"] for r in per_class.values()) / 3,
            "three_way_n": len(covered), "three_way_coverage": len(covered) / len(rows),
            "conditional_three_way_agreement": sum(rows[i]["label"] == predictions[i] for i in covered) / len(covered) if covered else None,
            "predicted_counts": dict(Counter(predictions)), "per_class": per_class,
            "confusion_row_labels": LABELS, "confusion_column_labels": STANCES, "confusion": matrix}


def aligned(rows, predictions, key):
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids) or sorted(p["id"] for p in predictions) != sorted(ids):
        raise ValueError("Missing, duplicate or unexpected IDs")
    by_id = {p["id"]: p[key] for p in predictions}
    return [by_id[r["id"]] for r in rows]


def run(data, directory, previous, output):
    if output.exists():
        raise ValueError("Refusing to overwrite evaluation")
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    manifest = json.loads((directory / "run.json").read_text())
    blind = data.parent / "validation_blind.json"
    if hashlib.sha256(blind.read_bytes()).hexdigest() != manifest["input_sha256"]:
        raise ValueError("Inference input hash mismatch")
    blind_rows = json.loads(blind.read_text())
    if {r["id"]: r["text"] for r in blind_rows} != {r["id"]: r["text"] for r in rows}:
        raise ValueError("Blinded text differs from reference text")
    predictions = []
    for batch in manifest["batches"]:
        path = directory / batch["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != batch["sha256"]:
            raise ValueError("Prediction hash mismatch")
        predictions.extend(json.loads(path.read_text())["predictions"])
    validate(blind_rows, {"predictions": predictions})
    new = aligned(rows, predictions, "author_stance")
    old_record = json.loads(previous.read_text())["models"]["astra_medium_frozen_prompt"]
    old = aligned(rows, old_record["predictions"], "prediction")
    report = {"purpose": "Reused development comparison; not independent accuracy or release approval",
              "release_approved": False, "reserved_test_read": False, "run": manifest,
              "reference_sha256": hashlib.sha256(data.read_bytes()).hexdigest(),
              "previous_sha256": hashlib.sha256(previous.read_bytes()).hexdigest(),
              "schema_valid_n": len(predictions), "nonpolitical_n": sum(not p["political"] for p in predictions),
              "groups": {}}
    for name, indices in (("all", list(range(len(rows)))),
                          ("unanimous", [i for i, r in enumerate(rows) if r["strict_agreement"]]),
                          ("disputed", [i for i, r in enumerate(rows) if not r["strict_agreement"]])):
        selected = [rows[i] for i in indices]
        report["groups"][name] = {"structured": measures(selected, [new[i] for i in indices]),
                                   "previous_forced_three_way": measures(selected, [old[i] for i in indices])} if indices else {"n": 0}
    report["paired_changes"] = {"new_matches_old_not": sum(new[i] == r["label"] != old[i] for i, r in enumerate(rows)),
                                "old_matches_new_not": sum(old[i] == r["label"] != new[i] for i, r in enumerate(rows)),
                                "changed_author_label": sum(a != b for a, b in zip(new, old))}
    events = sorted({r["event"] for r in rows})
    indices_by_event = {event: [i for i, r in enumerate(rows) if r["event"] == event] for event in events}
    rng = random.Random(20261002)
    differences = []
    for _ in range(5000):
        sample = [i for event in rng.choices(events, k=len(events)) for i in indices_by_event[event]]
        differences.append(sum(int(new[i] == rows[i]["label"]) - int(old[i] == rows[i]["label"]) for i in sample) / len(sample))
    quantiles = statistics.quantiles(differences, n=40, method="inclusive")
    report["paired_uncertainty"] = {"method": "Event-cluster bootstrap; 5000 draws; seed 20261002; inclusive 2.5/97.5 percentiles",
                                    "event_n": len(events), "agreement_difference_interval_95": [quantiles[0], quantiles[-1]],
                                    "caveat": "Exploratory reused-validation uncertainty, not independent model-quality evidence"}
    by_id = {p["id"]: p for p in predictions}
    # Article text and extracted copyrighted spans remain in local raw artifacts.
    report["predictions"] = [{"id": r["id"], "reference": r["label"], "strict_agreement": r["strict_agreement"],
                              "author_stance": new[i], "previous_label": old[i],
                              "political": by_id[r["id"]]["political"],
                              "evidence_count": len(by_id[r["id"]]["evidence"]),
                              "attributed_stances": [a["stance"] for a in by_id[r["id"]]["attributed_stances"]]} for i, r in enumerate(rows)]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps({"groups": report["groups"], "paired_changes": report["paired_changes"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("data", "directory", "previous", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.directory, args.previous, args.output)
