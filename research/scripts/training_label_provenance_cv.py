"""One preregistered, training-only unanimous-reference inclusion sensitivity.

Use the exact frozen folds and saved raw LR C=1 control from training_linear_cv.
Fit five raw TF-IDF/LR heads on unanimous training-fold examples and evaluate ALL
115 out-of-fold examples. This changes sample size and class composition as well
as disagreement inclusion; it cannot identify label noise or establish gold truth.
No heldout corpus split is opened and no production candidate is selected.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import warnings

import joblib
import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

from corpus_experiment import LABELS, metrics
from training_linear_cv import (SEED, TRAIN_SHA256, runtime_versions, save_json,
                                sha256, timestamp, uncertainty, validate_oof, vectorizer)


DEPENDENCIES = ("training_linear_cv.py", "corpus_experiment.py", "boilerplate_ablation.py")
NEW_NAME = "raw_unanimous_lr_C1"
CONTROL = "raw_lr_C1"


def select_unanimous_fit(rows, fit_ids, held_ids):
    by_id = {row["id"]: row for row in rows}
    if len(by_id) != len(rows) or len(set(fit_ids)) != len(fit_ids) or len(set(held_ids)) != len(held_ids):
        raise ValueError("Duplicate IDs in dataset or fold")
    if set(fit_ids) & set(held_ids) or set(fit_ids) | set(held_ids) != set(by_id):
        raise ValueError("Frozen fit and held IDs must partition training dataset")
    retained = [by_id[key] for key in fit_ids if by_id[key]["strict_agreement"]]
    if {row["label"] for row in retained} != set(LABELS):
        raise ValueError("Unanimous fit fold lacks at least one class; do not fit or oversample")
    return retained


def input_rows(data):
    if sha256(data.read_bytes()) != TRAIN_SHA256:
        raise ValueError("Expected exactly the frozen 115 training rows")
    return [json.loads(line) for line in data.read_text().splitlines()]


def load_control(path):
    control = json.loads(path.read_text())
    if control["protocol"]["expected_train"]["sha256"] != TRAIN_SHA256:
        raise ValueError("Unexpected parent corpus")
    if control["winner_selected"] or control["release_approved"]:
        raise ValueError("Expected research-only control")
    return control


def register(data, control_path, output):
    if output.exists():
        raise ValueError("Use a new protocol directory")
    rows, control = input_rows(data), load_control(control_path)
    fold_records, blocked = [], []
    for original in control["folds"]:
        fold = {key: original[key] for key in ("fold", "fit_ids", "held_ids", "fit_group_ids", "held_group_ids", "fit_label_counts", "held_label_counts")}
        try:
            retained = select_unanimous_fit(rows, fold["fit_ids"], fold["held_ids"])
            fold["unanimous_fit_ids"] = [row["id"] for row in retained]
            fold["unanimous_fit_counts"] = dict(Counter(row["label"] for row in retained))
            fold["unanimous_fit_n"] = len(retained)
            fold["all_three_fit_classes_present"] = True
        except ValueError as exc:
            blocked.append({"fold": fold["fold"], "reason": str(exc)})
        fold_records.append(fold)
    protocol = {
        "registered_at_utc": timestamp(),
        "purpose": "Single label-provenance inclusion sensitivity; not independent accuracy or causal label-noise test",
        "source_revision": control["protocol"]["source_revision"],
        "license": control["protocol"]["license"],
        "train_sha256": TRAIN_SHA256, "train_n": len(rows),
        "control_path": str(control_path), "control_sha256": sha256(control_path.read_bytes()),
        "control_name": CONTROL, "candidate_name": NEW_NAME,
        "script_sha256": sha256(Path(__file__).read_bytes()),
        "dependency_hashes": {name: sha256((Path(__file__).parent / name).read_bytes()) for name in DEPENDENCIES},
        "folds": fold_records, "blocked_folds": blocked,
        "data_use": "Filter fit-fold IDs by original worker unanimity only; all held-fold IDs predicted regardless of agreement; no held-fold labels fit anything",
        "model": {"kind": "raw word/bigram TF-IDF logistic regression", "C": 1., "class_weight": "balanced",
                  "solver": "lbfgs", "max_iter": 1000, "random_state": SEED,
                  "features": {"ngram_range": [1, 2], "min_df": 2, "max_features": 20000,
                               "sublinear_tf": True, "smooth_idf": True, "norm": "l2"},
                  "fit_state": "Vocabulary, IDF and class weights fit on retained unanimous fit-fold rows only"},
        "full_training_label_counts": dict(Counter(row["label"] for row in rows)),
        "unanimous_training_n": sum(row["strict_agreement"] for row in rows),
        "unanimous_training_label_counts": dict(Counter(row["label"] for row in rows if row["strict_agreement"])),
        "primary_metrics": ["ALL115 denominator macro-F1", "LEFT/CENTER/RIGHT recall", "released-label agreement"],
        "secondary_metrics": ["unanimous subset", "disputed subset", "each held fold"],
        "uncertainty": control["protocol"]["uncertainty"],
        "limitations": [
            "Unanimity is not adjudicated gold truth",
            "Training population shrinks115 to54 and class composition changes38/26/51 to12/26/16",
            "All26 CENTER examples are already unanimous, so exclusion disproportionately removes LEFT/RIGHT examples",
            "Any difference confounds sample size, class composition, text selection and disputed-reference inclusion",
            "No size/class-matched removal control is included; do not attribute changes specifically to noisy labels",
            "Same frozen folds as current raw LR control; GroupKFold group-key tie ordering differs from older historical CV",
            "Prior development knowledge and incomplete event-family audit preclude independent accuracy claims",
        ],
        "bounds": {"new_candidates": 1, "new_fit_count": 5, "new_hyperparameter_grid": False,
                   "validation_or_test_evaluations": 0, "paid_compute_purchases": 0,
                   "full_training_refit": False, "winner_selection": False, "deployment": False},
        "required_sklearn": "1.6.1",
        "stop_rule": "If every unanimous fit fold contains all classes, finish five fits and report all115 predictions; otherwise record blocked and do not fit, oversample or change folds",
    }
    output.mkdir(parents=True)
    save_json(output / "protocol.json", protocol)
    # Save exact helpers: the shared working tree can change in other tasks.
    source = output / "frozen_source"
    source.mkdir()
    for name in (*DEPENDENCIES, Path(__file__).name):
        (source / name).write_bytes((Path(__file__).parent / name).read_bytes())
    print(json.dumps({"protocol_sha256": sha256((output / "protocol.json").read_bytes()),
                      "all_fit_folds_have_three_classes": not blocked,
                      "unanimous_fit_counts": [fold.get("unanimous_fit_counts") for fold in fold_records]}))


def run(data, control_path, protocol_path, result_path):
    protocol = json.loads(protocol_path.read_text())
    if result_path.exists() or (protocol_path.parent / "run_started.json").exists():
        raise ValueError("Do not overwrite or repeat this registered run")
    expected = {**protocol["dependency_hashes"], Path(__file__).name: protocol["script_sha256"]}
    for name, expected_sha in expected.items():
        if sha256((Path(__file__).parent / name).read_bytes()) != expected_sha:
            raise ValueError("Source changed after registration; use the exact frozen source")
    if sklearn.__version__ != protocol["required_sklearn"]:
        raise ValueError("Use preregistered sklearn version")
    if sha256(control_path.read_bytes()) != protocol["control_sha256"]:
        raise ValueError("Saved control changed after registration")
    rows, control = input_rows(data), load_control(control_path)
    by_id = {row["id"]: row for row in rows}
    started = {"started_at_utc": timestamp(), "protocol_sha256": sha256(protocol_path.read_bytes())}
    save_json(protocol_path.parent / "run_started.json", started)
    report = {"purpose": protocol["purpose"], "protocol": protocol, **started,
              "runtime": runtime_versions(), "release_approved": False, "winner_selected": False,
              "validation_or_test_dataset_read": False, "original_control_retrained": False,
              "original_control_file_unchanged": True, "blocked": bool(protocol["blocked_folds"]),
              "references": control["references"], "groups": control["groups"],
              "oof": {CONTROL: control["oof"][CONTROL], NEW_NAME: []},
              "folds": [], "model_artifacts": [], "summary": {}}
    if report["blocked"]:
        save_json(result_path, report)
        return
    for frozen in protocol["folds"]:
        fit_rows = select_unanimous_fit(rows, frozen["fit_ids"], frozen["held_ids"])
        if [row["id"] for row in fit_rows] != frozen["unanimous_fit_ids"]:
            raise ValueError("Retained fit IDs differ from protocol")
        held_rows = [by_id[key] for key in frozen["held_ids"]]
        features = vectorizer("lr")
        fit_matrix = features.fit_transform([row["text"] for row in fit_rows])
        held_matrix = features.transform([row["text"] for row in held_rows])
        model = LogisticRegression(C=1., class_weight="balanced", max_iter=1000, random_state=SEED)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            model.fit(fit_matrix, [row["label"] for row in fit_rows])
        convergence = [str(w.message) for w in caught if issubclass(w.category, ConvergenceWarning)]
        predicted, scores, probabilities = model.predict(held_matrix), model.decision_function(held_matrix), model.predict_proba(held_matrix)
        artifact = protocol_path.parent / f"fold-{frozen['fold']}-unanimous-lr.joblib"
        joblib.dump({"vectorizer": features, "classifier": model,
                     "fit_ids": frozen["unanimous_fit_ids"], "protocol_sha256": started["protocol_sha256"]}, artifact)
        report["model_artifacts"].append({"fold": frozen["fold"], "file": artifact.name,
                                          "sha256": sha256(artifact.read_bytes()), "feature_n": len(features.vocabulary_),
                                          "convergence_warnings": convergence})
        report["oof"][NEW_NAME].extend({"id": row["id"], "fold": frozen["fold"], "prediction": p,
                                        "score_class_order": model.classes_.tolist(), "decision_scores": s.tolist(),
                                        "uncalibrated_probabilities": probability.tolist()}
                                       for row, p, s, probability in zip(held_rows, predicted.tolist(), scores, probabilities))
        report["folds"].append({**frozen, "all_held_metrics": metrics(held_rows, predicted.tolist())})
        print(f"Completed fold {frozen['fold']+1}/5 with {len(fit_rows)} unanimous fit articles", flush=True)
    for name, predictions in report["oof"].items():
        validate_oof(rows, predictions)
        aligned = {entry["id"]: entry for entry in predictions}
        report["oof"][name] = [aligned[row["id"]] for row in rows]
        predictions = [aligned[row["id"]]["prediction"] for row in rows]
        summary = {"all_115": metrics(rows, predictions)}
        for strict, key in ((True, "unanimous_secondary"), (False, "disputed_secondary")):
            selected = [(row, prediction) for row, prediction in zip(rows, predictions) if row["strict_agreement"] == strict]
            summary[key] = metrics([row for row, _ in selected], [p for _, p in selected])
        report["summary"][name] = summary
    groups = [entry["group_id"] for entry in control["references"]]
    report["uncertainty"] = uncertainty(rows, groups, report["oof"], protocol["uncertainty"]["draws"])
    report["checks"] = {"all_115_exactly_once_per_candidate": True,
                        "all_folds_unchanged_from_control": True,
                        "all_unanimous_fit_folds_contain_three_classes": True,
                        "no_held_example_dropped_from_primary_metrics": True,
                        "all_fit_state_uses_retained_fit_rows_only": True,
                        "comparison_does_not_isolate_disputed_label_effect": True}
    report["convergence_warning_count"] = sum(len(a["convergence_warnings"]) for a in report["model_artifacts"])
    report["completed_at_utc"] = timestamp()
    save_json(result_path, report)
    save_json(protocol_path.parent / "result_provenance.json", {"result_sha256": sha256(result_path.read_bytes())})
    for name, summary in report["summary"].items():
        metric = summary["all_115"]
        print(json.dumps({"name": name, "agreement": metric["accuracy"], "macro_f1": metric["macro_f1"],
                          "recall": {label: metric["per_class"][label]["recall"] for label in LABELS}}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("register", "run"))
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Protocol/checkpoint directory")
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    if args.mode == "register":
        register(args.data, args.control, args.output)
    else:
        if args.result is None:
            parser.error("--result is required for run")
        run(args.data, args.control, args.output / "protocol.json", args.result)


if __name__ == "__main__":
    main()
