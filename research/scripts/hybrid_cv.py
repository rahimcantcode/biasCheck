"""Fixed training-only comparison of lexical, semantic and combined features."""
import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import scipy
from scipy.sparse import csr_matrix, hstack
import sklearn
from sklearn.linear_model import LogisticRegression

from corpus_experiment import metrics


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hybrid(word, semantic):
    if word.shape[0] != semantic.shape[0] or not np.isfinite(semantic).all():
        raise ValueError("Invalid aligned feature blocks")
    return hstack([word, csr_matrix(semantic)], format="csr") / np.sqrt(2)


def validate_split(rows, train, held):
    ids = {r["id"] for r in rows}
    if len(ids) != len(rows) or len(set(train)) != len(train) or len(set(held)) != len(held):
        raise ValueError("Duplicate IDs")
    if not train or not held or set(train) & set(held) or set(train) | set(held) != ids:
        raise ValueError("Invalid partition")
    lookup = {r["id"]: r for r in rows}
    if {lookup[i]["event"] for i in train} & {lookup[i]["event"] for i in held}:
        raise ValueError("Event strings cross folds")


def run(data, features, folds, output):
    if output.exists():
        raise ValueError("Use a new output directory")
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    ids = [r["id"] for r in rows]
    provenance = json.loads(features.with_suffix(".json").read_text())
    prior = json.loads((folds / "training_results.json").read_text())
    if provenance["records"]["train"]["ids"] != ids or provenance["records"]["train"]["data_sha256"] != digest(data) or prior["input_sha256"] != digest(data):
        raise ValueError("Training data/features/folds provenance mismatch")
    # NPZ members are loaded lazily: never index the validation member.
    with np.load(features, allow_pickle=False) as arrays:
        semantic = arrays["train"]
    if semantic.shape != (len(rows), 384) or not np.isfinite(semantic).all() or not np.allclose(np.linalg.norm(semantic, axis=1), 1, atol=1e-5):
        raise ValueError("Expected finite normalized MiniLM training features")
    record = {"purpose": "Training-only exploratory grouped CV; not independent accuracy",
              "validation_array_loaded": False, "reserved_test_read": False, "release_approved": False,
              "data_sha256": digest(data), "features_container_sha256": digest(features),
              "feature_metadata_sha256": digest(features.with_suffix(".json")),
              "fold_manifest_sha256": digest(folds / "training_results.json"),
              "encoder": {k: provenance[k] for k in ("model", "revision", "pooling", "capacity", "stride")},
              "settings": {"C": 1, "class_weight": "balanced", "seed": 20261001, "max_iter": 1000,
                           "solver": "lbfgs", "hybrid": "Concatenate both blocks scaled by 1/sqrt(2); no tuning"},
              "runtime": {"numpy": np.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__, "joblib": joblib.__version__},
              "folds": [], "oof": {name: [] for name in ("word", "semantic", "hybrid")}}
    output.mkdir(parents=True)
    (output / "protocol.json").write_text(json.dumps(record, indent=2))
    index = {id: i for i, id in enumerate(ids)}
    for split in prior["folds"]:
        train, held = split["train_ids"], split["held_ids"]
        validate_split(rows, train, held)
        ti, hi = [index[i] for i in train], [index[i] for i in held]
        path = folds / f"fold-{split['fold']}-baseline.joblib"
        if digest(path) != split["models"]["baseline"]["model_sha256"]:
            raise ValueError("Frozen vocabulary/model artifact mismatch")
        saved = joblib.load(path)
        vectorizer = saved["vectorizer"]
        wt = vectorizer.transform([rows[i]["text"] for i in ti])
        wh = vectorizer.transform([rows[i]["text"] for i in hi])
        fold = {"fold": split["fold"], "train_ids": train, "held_ids": held, "models": {}}
        for name, fit_x, pred_x in (("word", wt, wh), ("semantic", semantic[ti], semantic[hi]),
                                    ("hybrid", hybrid(wt, semantic[ti]), hybrid(wh, semantic[hi]))):
            if name == "word":
                model = saved["classifier"]
                model_hash = digest(path)
            else:
                model = LogisticRegression(C=1, class_weight="balanced", max_iter=1000, random_state=20261001)
                model.fit(fit_x, [rows[i]["label"] for i in ti])
                destination = output / f"fold-{split['fold']}-{name}.joblib"
                joblib.dump({"classifier": model, "vectorizer": vectorizer if name == "hybrid" else None,
                             "encoder": record["encoder"], "settings": record["settings"]}, destination)
                model_hash = digest(destination)
            probabilities = model.predict_proba(pred_x)
            predictions = model.classes_[probabilities.argmax(axis=1)]
            fold["models"][name] = {"model_sha256": model_hash, "iterations": model.n_iter_.tolist()}
            record["oof"][name].extend({"id": id, "fold": split["fold"], "prediction": str(label),
                "probabilities": dict(zip(model.classes_.tolist(), scores.tolist()))}
                for id, label, scores in zip(held, predictions, probabilities))
        record["folds"].append(fold)
    record["metrics"] = {}
    for name, predictions in record["oof"].items():
        aligned = {r["id"]: r["prediction"] for r in predictions}
        if len(predictions) != len(rows) or set(aligned) != set(ids):
            raise ValueError("Incomplete or repeated OOF coverage")
        record["metrics"][name] = metrics(rows, [aligned[id] for id in ids])
    (output / "training_results.json").write_text(json.dumps(record, indent=2))
    (output / "browser_three.json").write_text(json.dumps([{k: r[k] for k in ("id", "text")} for r in rows[3:6]], indent=2))
    print(json.dumps(record["metrics"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("data", "features", "folds", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.features, args.folds, args.output)
