"""Allowlisted human party ratings and training-only grouped ridge baseline."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import Ridge

from corpus_experiment import metrics


def decode(rep, dem, threshold=.125):
    difference = rep - dem
    return "RIGHT" if difference > threshold else "LEFT" if difference < -threshold else "CENTER"


def rating(q1, q2):
    values = {"-5", "-2.5", "0", "2.5", "5"}
    if q1 not in values or q2 not in values:
        raise ValueError("Invalid source rating")
    return float(q1) / 5, -float(q2) / 5


def recover(path, rows):
    allowed = {r["id"] for r in rows}
    recovered = {id: [] for id in allowed}
    csv.field_size_limit(10_000_000)
    # Only ASCII identifiers/numeric fields from allowlisted rows are retained.
    with path.open(encoding="latin-1", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["Input.docid"] not in allowed:
                continue
            rep, dem = rating(row["Answer.q1"], row["Answer.q2"])
            recovered[row["Input.docid"]].append({"republican_valence": rep, "democratic_valence": dem,
                                                 "source_status": row["AssignmentStatus"]})
    for row in rows:
        values = recovered[row["id"]]
        if len(values) != 2:
            raise ValueError("Expected exactly two original ratings per training ID")
        derived = sorted(decode(v["republican_valence"], v["democratic_valence"], 0.) for v in values)
        if derived != sorted(y.upper() for y in row["worker_labels"]):
            raise ValueError("Recovered axes do not reproduce saved worker labels")
    return recovered


def run(data, source, folds, output):
    if output.exists():
        raise ValueError("Use a new output directory")
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate training IDs")
    human = recover(source, rows)
    prior = json.loads((folds / "training_results.json").read_text())
    source_hash = hashlib.sha256(data.read_bytes()).hexdigest()
    if source_hash != prior["input_sha256"]:
        raise ValueError("Training input changed since frozen folds")
    by_id = {r["id"]: r for r in rows}
    means = {id: np.mean([[v["republican_valence"], v["democratic_valence"]] for v in values], axis=0) for id, values in human.items()}
    record = {"purpose": "Training-only development model; not independent evaluation", "release_approved": False,
              "reserved_test_file_read": False, "validation_file_read": False,
              "raw_annotation_access": "CSV scanned and filtered to training allowlist; nontraining rating values not retained or used",
              "data_sha256": source_hash, "annotation_csv_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "fold_manifest_sha256": hashlib.sha256((folds / "training_results.json").read_bytes()).hexdigest(),
              "protocol": {"axes": ["Republican valence", "Democratic valence"], "q2_sign_inverted": True,
                           "target": "Mean of two human ratings, divided by5", "ridge_alpha": 1., "solver": "lsqr",
                           "threshold": .125, "threshold_basis": "Half smallest nonzero two-worker mean difference increment; fixed, untuned"},
              "human_training_ratings": human, "predictions": [], "folds": []}
    output.mkdir(parents=True)
    (output / "protocol.json").write_text(json.dumps(record, indent=2))
    for fold in prior["folds"]:
        train, held = fold["train_ids"], fold["held_ids"]
        if set(train) & set(held) or set(train) | set(held) != set(by_id):
            raise ValueError("Invalid fold partition")
        path = folds / f"fold-{fold['fold']}-baseline.joblib"
        if hashlib.sha256(path.read_bytes()).hexdigest() != fold["models"]["baseline"]["model_sha256"]:
            raise ValueError("Frozen feature artifact hash mismatch")
        vectorizer = joblib.load(path)["vectorizer"]
        model = Ridge(alpha=1., solver="lsqr")
        model.fit(vectorizer.transform([by_id[id]["text"] for id in train]), np.stack([means[id] for id in train]))
        predicted = model.predict(vectorizer.transform([by_id[id]["text"] for id in held]))
        destination = output / f"fold-{fold['fold']}.joblib"
        joblib.dump({"vectorizer": vectorizer, "regressor": model}, destination)
        record["folds"].append({"fold": fold["fold"], "train_ids": train, "held_ids": held,
                                "model_sha256": hashlib.sha256(destination.read_bytes()).hexdigest()})
        record["predictions"].extend({"id": id, "fold": fold["fold"], "prediction": decode(*values),
                                       "predicted_valence": values.tolist(), "reference_mean_valence": means[id].tolist()}
                                      for id, values in zip(held, predicted))
    by_prediction = {r["id"]: r for r in record["predictions"]}
    if len(record["predictions"]) != len(rows) or set(by_prediction) != set(by_id):
        raise ValueError("Incomplete out-of-fold coverage")
    record["metrics"] = metrics(rows, [by_prediction[r["id"]]["prediction"] for r in rows])
    record["valence_mae"] = np.mean(np.abs(np.array([r["predicted_valence"] for r in record["predictions"]]) - np.array([r["reference_mean_valence"] for r in record["predictions"]])), axis=0).tolist()
    record["zero_valence_mae"] = np.mean(np.abs(np.array(list(means.values()))), axis=0).tolist()
    record["previous_logistic_metrics"] = prior["summary"]["baseline"]["original_metrics"]
    (output / "training_results.json").write_text(json.dumps(record, indent=2))
    (output / "browser_three.json").write_text(json.dumps([{k:r[k] for k in ("id", "text")} for r in rows[:3]], indent=2))
    print(json.dumps({k:record[k] for k in ("metrics", "valence_mae", "zero_valence_mae")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("data", "source", "folds", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.source, args.folds, args.output)
