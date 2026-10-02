"""Bounded, training-only PoliticalBiasCorpus word/bigram comparison.

Run register, recover, then run. The immutable protocol is written before data
recovery or model fitting. Only the frozen 115 training IDs are materialized.
Combined upstream CSVs necessarily contain other rows: those bytes are downloaded
and CSV-framed, but non-allowlisted fields are not inspected, retained, printed,
or used. No validation/test dataset is constructed. All models remain research
artifacts under the corpus's CC-BY-NC-SA-4.0 terms, with release_approved false.

NB-SVM is inspired by Wang & Manning (2012), https://aclanthology.org/P12-2018/.
It uses binary word/bigram counts, alpha=1 normalized positive/negative feature
counts, and one binary LinearSVC per class. It is NOT a paper replication: it
uses OVR multiclass argmax, balanced class weights, sklearn tokenization and
vocabulary limits, and beta=1 (no NB/SVM coefficient interpolation).
"""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import urllib.request
import warnings

import joblib
import numpy as np
import scipy
from scipy import sparse
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.svm import LinearSVC

from boilerplate_ablation import FOOTERS, strip_footers
from corpus_experiment import LABELS, digest, metrics


REVISION = "b193ee173936b281183ca1dc101ae4de215a0e5c"
TRAIN_SHA256 = "5ebefc86e5da25784649b895753219207913cbcb042b85e7e90fdf4b84f2d1b9"
SEED = 20261001
SOURCE_FILES = (
    "gold/HIT_inputs/mturk_input_300.csv",
    "gold/gold_docs_workers_agreed_and_matched_outlet.csv",
    "gold/gold_docs_workers_agreed_conflicted_with_outlet.csv",
    "gold/gold_docs_workers_agreed_labeled_center_conflicted_with_outlet_lr.csv",
)
ROOT = Path(__file__).resolve().parents[2]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    # Exclusive create protects protocols and completed run artifacts.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def normalize_event(event):
    value = " ".join(event.lower().split())
    if not value:
        raise ValueError("Empty event string")
    return value


def event_family_groups(rows, known_families):
    """Union normalized events and reviewed ID families, including transitivity."""
    ids = [row["id"] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate training IDs")
    parent = {key: key for key in ids}

    def find(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    def union(left, right):
        left, right = find(left), find(right)
        parent[max(left, right)] = min(left, right)

    by_event = {}
    for row in rows:
        event = normalize_event(row["event"])
        if event in by_event:
            union(row["id"], by_event[event])
        else:
            by_event[event] = row["id"]
    for family in known_families:
        if not family or len(set(family)) != len(family):
            raise ValueError("Known families must have distinct, nonempty IDs")
        if not set(family).issubset(parent):
            raise ValueError("Known family includes nontraining IDs")
        for key in family[1:]:
            union(family[0], key)
    return [find(key) for key in ids]


def make_folds(rows, known_families, n_splits=5):
    groups = event_family_groups(rows, known_families)
    folds = list(GroupKFold(n_splits=n_splits).split(rows, groups=groups))
    validate_folds(rows, groups, folds)
    return groups, folds


def validate_folds(rows, groups, folds):
    held_occurrences = Counter()
    all_indices = set(range(len(rows)))
    for train, held in folds:
        if len(set(train)) != len(train) or len(set(held)) != len(held):
            raise ValueError("Repeated index within a fold")
        train, held = set(map(int, train)), set(map(int, held))
        if train & held or train | held != all_indices:
            raise ValueError("Fold must partition the full training dataset")
        if {groups[i] for i in train} & {groups[i] for i in held}:
            raise ValueError("Event family crosses a fold")
        held_occurrences.update(held)
    if held_occurrences != Counter({i: 1 for i in all_indices}):
        raise ValueError("Each training ID must appear exactly once out of fold")


def validate_oof(rows, predictions):
    expected = Counter(row["id"] for row in rows)
    if any(n != 1 for n in expected.values()):
        raise ValueError("Duplicate reference IDs")
    if Counter(row["id"] for row in predictions) != expected:
        raise ValueError("Each training ID must appear exactly once out of fold")


def binary_features(matrix):
    matrix = sparse.csr_matrix(matrix, dtype=np.float64).copy()
    if not np.all(np.isfinite(matrix.data)) or np.any(matrix.data < 0):
        raise ValueError("NB features must be finite and nonnegative")
    matrix.eliminate_zeros()
    matrix.data[:] = 1.0
    return matrix


def nb_log_count_ratio(matrix, positive, alpha=1.0):
    """Only supplied fit rows contribute: log((p/sum(p))/(q/sum(q)))."""
    matrix = binary_features(matrix)
    positive = np.asarray(positive, dtype=bool)
    if len(positive) != matrix.shape[0] or not positive.any() or positive.all():
        raise ValueError("NB ratio requires both classes in the training fold")
    if alpha <= 0 or not np.isfinite(alpha):
        raise ValueError("Smoothing must be positive and finite")
    p = alpha + np.asarray(matrix[positive].sum(axis=0)).ravel()
    q = alpha + np.asarray(matrix[~positive].sum(axis=0)).ravel()
    return np.log(p / p.sum()) - np.log(q / q.sum())


class OVRNBSVM:
    """Three independent training-fold NB transforms and balanced linear SVMs."""

    def __init__(self, C=1.0):
        self.C = C

    def fit(self, matrix, labels):
        matrix = binary_features(matrix)
        labels = np.asarray(labels)
        self.classes_ = np.asarray(LABELS)
        if set(labels) != set(LABELS):
            raise ValueError("Each fit fold must contain LEFT, CENTER and RIGHT")
        self.ratios_, self.models_ = [], []
        self.fit_n_ = matrix.shape[0]
        self.class_counts_ = {label: int(sum(labels == label)) for label in LABELS}
        for label in self.classes_:
            target = labels == label
            ratio = nb_log_count_ratio(matrix, target)
            model = svm(self.C)
            model.fit(matrix.multiply(ratio).tocsr(), target.astype(int))
            self.ratios_.append(ratio)
            self.models_.append(model)
        return self

    def decision_function(self, matrix):
        matrix = binary_features(matrix)
        return np.column_stack([
            model.decision_function(matrix.multiply(ratio).tocsr())
            for ratio, model in zip(self.ratios_, self.models_)
        ])

    def predict(self, matrix):
        return self.classes_[self.decision_function(matrix).argmax(axis=1)]


def svm(C):
    return LinearSVC(C=C, class_weight="balanced", loss="squared_hinge",
                     penalty="l2", dual="auto", tol=1e-5, max_iter=10000,
                     random_state=SEED)


def candidate_grid():
    return [{"name": f"{view}_{kind}_C{C:g}", "view": view, "kind": kind, "C": C}
            for view in ("raw", "clean")
            for kind in ("lr", "linearsvc", "nbsvm")
            for C in ((1.0,) if kind == "lr" else (0.1, 1.0, 10.0))]


def vectorizer(kind):
    options = {"ngram_range": (1, 2), "min_df": 2, "max_features": 20000}
    if kind == "nbsvm":
        return CountVectorizer(binary=True, dtype=np.float64, **options)
    return TfidfVectorizer(sublinear_tf=True, **options)


def register(output, manifest_path, review_path):
    manifest = json.loads(manifest_path.read_text())["manifest"]
    # Only frozen train metadata and previously reviewed train-ID aliases are used.
    train = manifest["splits"]["train"]
    review = json.loads(review_path.read_text())
    family = review["train_ids"]
    if (manifest["revision"] != REVISION or train["sha256"] != TRAIN_SHA256
            or train["n"] != 115 or len(train["ids"]) != 115
            or len(set(train["ids"])) != 115 or not set(family).issubset(train["ids"])):
        raise ValueError("Unexpected frozen corpus metadata")
    output.mkdir(parents=True, exist_ok=False)
    protocol = {
        "schema_version": 1, "registered_at_utc": timestamp(),
        "purpose": "Bounded training-only model comparison; not independent accuracy",
        "license": manifest["license"], "release_approved": False,
        "source_revision": REVISION, "source_repository": manifest["dataset"],
        "source_paths": list(SOURCE_FILES), "expected_train": train,
        "manifest_path": str(manifest_path.relative_to(ROOT)),
        "manifest_file_sha256": sha256(manifest_path.read_bytes()),
        "known_event_family_train_ids": [family],
        "family_review_path": str(review_path.relative_to(ROOT)),
        "family_review_sha256": sha256(review_path.read_bytes()),
        "script_sha256": sha256(Path(__file__).read_bytes()),
        "dependency_hashes": {name: sha256((Path(__file__).parent / name).read_bytes())
                              for name in ("boilerplate_ablation.py", "corpus_experiment.py")},
        "extraction": [
            "Download four combined source CSVs at the immutable revision, in memory only",
            "CSV-frame records, read docid first, discard non-allowlisted rows before accessing text/label fields",
            "Never print or save source CSV bodies or construct validation/test datasets",
            "Join stripped title, snippet1, snippet2, snippet3 with two newlines",
            "Uppercase human_label; normalize event lower-case whitespace; compare original worker labels for strict_agreement",
            "Preserve worker labels and normalized lower-case whitespace text SHA-256",
            "Serialize fields in original order using json.dumps defaults plus newline, in frozen train-ID order",
            "Require byte-identical train SHA-256 before writing train.jsonl",
        ],
        "folds": {"method": "GroupKFold", "n_splits": 5, "shuffle": False,
                  "groups": "Transitive union of normalized event strings and known reviewed training-ID episode family",
                  "full_event_family_independence_established": False},
        "candidates": candidate_grid(), "seed": SEED,
        "features": {"analyzer": "word", "ngram_range": [1, 2], "min_df": 2,
                     "max_features": 20000, "lowercase": True,
                     "token_pattern": r"(?u)\b\w\w+\b", "stop_words": None,
                     "lr_linearsvc": "sublinear TF-IDF, smoothed training-fold IDF, row L2 norm",
                     "nbsvm": "binary counts, no IDF, no row normalization",
                     "fitting": "Fit each candidate vocabulary, IDF, class weights and NB ratios inside fit fold only",
                     "external_scaler": None},
        "lr": {"solver": "lbfgs", "penalty": "l2", "class_weight": "balanced",
               "C": 1.0, "max_iter": 1000, "tol": 1e-4, "random_state": SEED},
        "svm": {"loss": "squared_hinge", "penalty": "l2", "class_weight": "balanced",
                "dual": "auto", "tol": 1e-5, "max_iter": 10000, "random_state": SEED},
        "nbsvm": {"reference": "https://aclanthology.org/P12-2018/", "alpha": 1.0,
                  "formula": "B_ij=1[count_ij>0]; p_cj=1+sum_{i:y_i=c} B_ij; q_cj=1+sum_{i:y_i!=c} B_ij; r_cj=log(p_cj/sum_j p_cj)-log(q_cj/sum_j q_cj); z_icj=B_ij*r_cj",
                  "fit": "For each class fit a balanced binary LinearSVC on z_c; predict argmax raw signed margins",
                  "decision_order": LABELS, "ties": "first class in LEFT,CENTER,RIGHT order",
                  "beta": 1.0, "coefficient_interpolation": False,
                  "paper_replication": False, "probabilities_calibrated": False,
                  "limitations": "OVR raw margins are not calibrated/comparable probabilities; feature representation differs from TF-IDF comparators"},
        "preprocessing": {"views": ["raw", "clean"], "footer_hashes": sorted(FOOTERS),
                          "clean": "Remove only whole paragraphs matching two known normalized hashes; train/evaluate same view",
                          "provenance": "Development-informed hashes from earlier train/validation audit; human references apply to original text"},
        "primary_metrics": ["pooled macro F1", "LEFT/CENTER/RIGHT recall", "released-label agreement", "confusion matrix"],
        "secondary_metrics": ["unanimous-annotator subset", "each held-fold result"],
        "uncertainty": {"method": "paired event-family-cluster percentile bootstrap of fixed OOF predictions",
                        "draws": 5000, "seed": SEED, "percentiles": [2.5, 97.5],
                        "comparators": ["raw_lr_C1", "same-view LR C1"],
                        "metrics": ["agreement", "macro F1", "class recall"],
                        "interpretation": "Exploratory only; no refitting, no model-selection adjustment, shared training folds, incomplete family audit, and reused development knowledge prevent independent generalization claims"},
        "bounds": {"candidate_n": 14, "fold_model_n": 70,
                   "heldout_validation_model_evaluations": 0, "reserved_test_model_evaluations": 0,
                   "character_models": 0, "full_training_refits": 0,
                   "paid_compute_purchases": 0, "winner_selection": False,
                   "threshold_tuning": False, "deployment": False},
        "required_sklearn": "1.6.1",
        "stop_rule": "Finish and report all 14 candidates over five fixed folds, including negative results; no further search based on outcomes",
    }
    save_json(output / "protocol.json", protocol)
    print(json.dumps({"protocol": str(output / "protocol.json"),
                      "sha256": sha256((output / "protocol.json").read_bytes())}))


def read_protocol(path):
    protocol = json.loads(path.read_text())
    if protocol["script_sha256"] != sha256(Path(__file__).read_bytes()):
        raise ValueError("Script changed after protocol registration")
    for name, expected in protocol["dependency_hashes"].items():
        if sha256((Path(__file__).parent / name).read_bytes()) != expected:
            raise ValueError("Dependency changed after protocol registration")
    if protocol["expected_train"]["sha256"] != TRAIN_SHA256:
        raise ValueError("Unexpected training hash")
    return protocol


def allowlisted_csv_records(content, allowed):
    """Nontraining row fields are framed by CSV, never interpreted as examples."""
    reader = csv.reader(io.StringIO(content.decode("utf-8"), newline=""))
    header = next(reader)
    docid_index = header.index("docid")
    for values in reader:
        if values[docid_index] not in allowed:
            continue
        if len(values) != len(header):
            raise ValueError("Malformed allowlisted source record")
        yield dict(zip(header, values))


def recover(protocol_path, output):
    protocol = read_protocol(protocol_path)
    if output.exists():
        raise ValueError("Use a new training-data directory")
    allowed = set(protocol["expected_train"]["ids"])
    inputs, labels, provenance = {}, {}, []
    for path in protocol["source_paths"]:
        url = f"https://raw.githubusercontent.com/ksolaiman/PoliticalBiasCorpus/{REVISION}/{path}"
        with urllib.request.urlopen(url, timeout=60) as response:
            content = response.read()
        selected = list(allowlisted_csv_records(content, allowed))
        provenance.append({"path": path, "url": url, "sha256": sha256(content),
                           "bytes": len(content), "selected_train_rows": len(selected)})
        target = inputs if path == SOURCE_FILES[0] else labels
        for row in selected:
            key = row["docid"]
            if key in target:
                raise ValueError("Duplicate allowlisted source ID")
            target[key] = row
        del content, selected
    if set(inputs) != allowed or set(labels) != allowed:
        raise ValueError("Frozen training IDs missing from pinned source")
    rows = []
    for key in protocol["expected_train"]["ids"]:
        shown, row = inputs[key], labels[key]
        text = "\n\n".join(shown[k].strip() for k in ("title", "snippet1", "snippet2", "snippet3"))
        rows.append({"id": key, "text": text, "label": row["human_label"].upper(),
                     "event": normalize_event(row["event"]),
                     "strict_agreement": row["worker_1_label"] == row["worker_2_label"],
                     "worker_labels": [row["worker_1_label"], row["worker_2_label"]],
                     "text_sha256": digest(text)})
    content = "".join(json.dumps(row) + "\n" for row in rows).encode()
    if sha256(content) != TRAIN_SHA256:
        raise ValueError("Recovered training serialization differs from frozen hash")
    output.mkdir(parents=True)
    (output / "train.jsonl").write_bytes(content)
    record = {"recovered_at_utc": timestamp(), "source_revision": REVISION,
              "protocol_sha256": sha256(protocol_path.read_bytes()),
              "train_sha256": sha256(content), "train_n": len(rows),
              "source_files": provenance,
              "combined_source_bytes_include_nontraining_records": True,
              "nontraining_fields_inspected_or_used": False,
              "nontraining_rows_retained": 0,
              "validation_or_test_datasets_constructed": False,
              "files_created": ["train.jsonl", "recovery_provenance.json"]}
    save_json(output / "recovery_provenance.json", record)
    print(json.dumps({"train_n": len(rows), "train_sha256": sha256(content)}))


def confusion_statistics(confusions):
    confusions = np.asarray(confusions, dtype=float)
    true_positive = np.diagonal(confusions, axis1=-2, axis2=-1)
    true_counts, pred_counts = confusions.sum(axis=-1), confusions.sum(axis=-2)
    denom = true_counts + pred_counts
    f1 = np.divide(2 * true_positive, denom, out=np.zeros_like(denom), where=denom > 0)
    recalls = np.divide(true_positive, true_counts, out=np.zeros_like(denom), where=true_counts > 0)
    return {"agreement": true_positive.sum(axis=-1) / confusions.sum(axis=(-2, -1)),
            "macro_f1": f1.mean(axis=-1),
            **{f"recall_{label}": recalls[..., i] for i, label in enumerate(LABELS)}}


def uncertainty(rows, groups, oof, draws=5000):
    unique_groups = sorted(set(groups))
    group_index = {value: i for i, value in enumerate(unique_groups)}
    labels = {label: i for i, label in enumerate(LABELS)}
    rng = np.random.default_rng(SEED)
    sampled = rng.integers(0, len(unique_groups), size=(draws, len(unique_groups)))
    samples = {}
    for name, predictions in oof.items():
        by_id = {entry["id"]: entry["prediction"] for entry in predictions}
        counts = np.zeros((len(unique_groups), len(LABELS), len(LABELS)))
        for row, group in zip(rows, groups):
            counts[group_index[group], labels[row["label"]], labels[by_id[row["id"]]]] += 1
        samples[name] = confusion_statistics(counts[sampled].sum(axis=1))
    results = {}
    for name, measures in samples.items():
        view_control = f"{name.split('_', 1)[0]}_lr_C1"
        results[name] = {"pointwise_95_percentile_intervals": {
            key: np.percentile(value, [2.5, 97.5]).tolist() for key, value in measures.items()},
            "paired_difference_intervals": {control: {
                key: np.percentile(value - samples[control][key], [2.5, 97.5]).tolist()
                for key, value in measures.items()}
                for control in dict.fromkeys(("raw_lr_C1", view_control))}}
    return {"unit": "known-episode-unioned normalized event group", "group_n": len(unique_groups),
            "draws": draws, "seed": SEED, "zero_support_class_convention": "recall and F1 = 0",
            "selection_adjusted": False, "independent_accuracy_interval": False,
            "model_refitting_in_bootstrap": False, "candidates": results}


def runtime_versions():
    return {"python": sys.version, "platform": platform.platform(),
            "numpy": np.__version__, "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__, "joblib": joblib.__version__}


def run(protocol_path, data, result_path):
    protocol = read_protocol(protocol_path)
    output = protocol_path.parent
    if result_path.exists() or (output / "run_started.json").exists():
        raise ValueError("Do not repeat a preregistered run or overwrite results")
    if sklearn.__version__ != protocol["required_sklearn"]:
        raise ValueError("Use the preregistered scikit-learn version")
    if sha256(data.read_bytes()) != TRAIN_SHA256:
        raise ValueError("Only the exact frozen training file may be evaluated")
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    if [row["id"] for row in rows] != protocol["expected_train"]["ids"]:
        raise ValueError("Training ID/order mismatch")
    if (dict(Counter(row["label"] for row in rows)) != protocol["expected_train"]["labels"]
            or sum(row["strict_agreement"] for row in rows) != protocol["expected_train"]["strict_agreement_n"]):
        raise ValueError("Unexpected training reference labels")
    if any(digest(row["text"]) != row["text_sha256"] for row in rows):
        raise ValueError("Training text checksum mismatch")
    recovery_path = data.parent / "recovery_provenance.json"
    recovery = json.loads(recovery_path.read_text())
    protocol_hash = sha256(protocol_path.read_bytes())
    if recovery["protocol_sha256"] != protocol_hash or recovery["train_sha256"] != TRAIN_SHA256:
        raise ValueError("Recovery provenance does not match this protocol")
    groups, folds = make_folds(rows, protocol["known_event_family_train_ids"])
    views = {"raw": [row["text"] for row in rows], "clean": []}
    transformations = []
    for row in rows:
        clean, removed = strip_footers(row["text"])
        views["clean"].append(clean)
        transformations.append({"id": row["id"], "raw_text_sha256": row["text_sha256"],
                                "clean_text_sha256": digest(clean), "removed_footer_hashes": removed})
    for view, texts in views.items():
        if len({digest(text) for text in texts}) != len(texts):
            raise ValueError(f"Duplicate normalized text in {view} view")
    fold_manifest = []
    for fold, (fit, held) in enumerate(folds):
        fit_rows, held_rows = [rows[i] for i in fit], [rows[i] for i in held]
        if set(row["label"] for row in fit_rows) != set(LABELS):
            raise ValueError("Fit fold does not contain all classes")
        fold_manifest.append({"fold": fold, "fit_ids": [row["id"] for row in fit_rows],
                              "held_ids": [row["id"] for row in held_rows],
                              "fit_group_ids": sorted({groups[i] for i in fit}),
                              "held_group_ids": sorted({groups[i] for i in held}),
                              "fit_label_counts": dict(Counter(row["label"] for row in fit_rows)),
                              "held_label_counts": dict(Counter(row["label"] for row in held_rows))})
    # Freeze actual membership before the first estimator or vectorizer is fitted.
    save_json(output / "fold_manifest.json", fold_manifest)
    started = {"started_at_utc": timestamp(), "protocol_sha256": protocol_hash,
               "fold_manifest_sha256": sha256((output / "fold_manifest.json").read_bytes())}
    save_json(output / "run_started.json", started)
    report = {"purpose": protocol["purpose"], "release_approved": False,
              "winner_selected": False, "validation_dataset_read": False,
              "reserved_test_dataset_read": False, "protocol": protocol,
              "protocol_sha256": protocol_hash, **started,
              "recovery": recovery, "recovery_provenance_sha256": sha256(recovery_path.read_bytes()),
              "runtime": runtime_versions(), "train_n": len(rows),
              "normalized_event_string_n": len({normalize_event(row["event"]) for row in rows}),
              "known_episode_unioned_group_n": len(set(groups)),
              "groups": [{"group_id": group, "train_ids": [row["id"] for row, g in zip(rows, groups) if g == group]}
                         for group in sorted(set(groups))],
              "folds": fold_manifest, "transformations": transformations,
              "leakage_checks": {"frozen_train_hash_reproduced": True,
                                 "all_candidate_folds_identical": True,
                                 "normalized_events_and_known_aliases_do_not_cross_folds": True,
                                 "no_raw_or_clean_exact_duplicates": True,
                                 "all_fit_state_training_fold_only": True,
                                 "full_event_family_independence_established": False},
              "references": [{"id": row["id"], "label": row["label"],
                              "strict_agreement": row["strict_agreement"],
                              "worker_labels": row["worker_labels"], "group_id": group}
                             for row, group in zip(rows, groups)],
              "oof": {candidate["name"]: [] for candidate in protocol["candidates"]},
              "summary": {}, "model_artifacts": [],
              "limitations": [
                  "Training-only reused-development exploration; not independent product accuracy",
                  "Known family union fixes one reviewed alias; other event-family and publisher dependence remain unaudited",
                  "Footer hashes came from prior train/validation review; clean text was not separately human-annotated",
                  "Only 115 historical US-politics excerpts; the 54 unanimous cases are a selected secondary subset",
                  "Prior original labels resolve some Center/partisan disagreements toward partisan",
                  "Fourteen candidates and shared fitted folds make apparent winners and bootstrap intervals exploratory",
                  "SVM decision margins and logistic probabilities are uncalibrated; no selective release policy is derived",
                  "No final model, production change, threshold tuning or full-training refit is authorized by these scores",
              ]}
    for fold, (fit, held) in enumerate(folds):
        fit_labels = [rows[i]["label"] for i in fit]
        held_rows = [rows[i] for i in held]
        fold_manifest[fold]["candidates"] = {}
        for candidate in protocol["candidates"]:
            name, kind, view = candidate["name"], candidate["kind"], candidate["view"]
            features = vectorizer(kind)
            fit_matrix = features.fit_transform([views[view][i] for i in fit])
            held_matrix = features.transform([views[view][i] for i in held])
            if kind == "lr":
                model = LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000, random_state=SEED)
            elif kind == "linearsvc":
                model = svm(candidate["C"])
            else:
                model = OVRNBSVM(C=candidate["C"])
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                model.fit(fit_matrix, fit_labels)
            # Retain any failure rather than silently report an unconverged score.
            convergence = [str(w.message) for w in caught if issubclass(w.category, ConvergenceWarning)]
            predicted = model.predict(held_matrix).tolist()
            margins = model.decision_function(held_matrix).tolist()
            probabilities = model.predict_proba(held_matrix).tolist() if kind == "lr" else None
            artifact = output / f"fold-{fold}-{name}.joblib"
            # Standard sklearn objects/arrays make NB artifacts reloadable without
            # a custom class pickled as __main__.OVRNBSVM from CLI execution.
            stored_model = ({"type": "ovr_nbsvm", "classes": model.classes_,
                             "ratios": model.ratios_, "estimators": model.models_}
                            if kind == "nbsvm" else model)
            joblib.dump({"vectorizer": features, "classifier": stored_model,
                         "fit_ids": fold_manifest[fold]["fit_ids"], "protocol_sha256": protocol_hash}, artifact)
            model_record = {"fold": fold, "candidate": name, "file": artifact.name,
                            "sha256": sha256(artifact.read_bytes()), "feature_n": len(features.vocabulary_),
                            "fit_n": len(fit), "score_class_order": model.classes_.tolist(),
                            "convergence_warnings": convergence,
                            "fitted_class_weights": "Computed from fit-label frequencies only"}
            if kind == "nbsvm":
                model_record["nb_ratio_sha256"] = [sha256(ratio.astype("<f8").tobytes()) for ratio in model.ratios_]
                model_record["nb_ratio_fit_n"] = model.fit_n_
                model_record["nb_ratio_fit_class_counts"] = model.class_counts_
            report["model_artifacts"].append(model_record)
            for j, i in enumerate(held):
                entry = {"id": rows[i]["id"], "fold": fold, "prediction": predicted[j],
                         "decision_scores": margins[j], "score_class_order": model.classes_.tolist()}
                if probabilities is not None:
                    entry["uncalibrated_probabilities"] = probabilities[j]
                report["oof"][name].append(entry)
            fold_manifest[fold]["candidates"][name] = metrics(held_rows, predicted)
        print(f"Completed fold {fold + 1}/5; held training articles={len(held)}", flush=True)
    for candidate in protocol["candidates"]:
        name = candidate["name"]
        validate_oof(rows, report["oof"][name])
        by_id = {entry["id"]: entry for entry in report["oof"][name]}
        report["oof"][name] = [by_id[row["id"]] for row in rows]
        predictions = [by_id[row["id"]]["prediction"] for row in rows]
        summary = metrics(rows, predictions)
        summary["matches"] = sum(row["label"] == predicted for row, predicted in zip(rows, predictions))
        strict_pairs = [(row, predicted) for row, predicted in zip(rows, predictions) if row["strict_agreement"]]
        summary["unanimous_secondary_full_metrics"] = metrics([row for row, _ in strict_pairs], [p for _, p in strict_pairs])
        report["summary"][name] = summary
    report["uncertainty"] = uncertainty(rows, groups, report["oof"], protocol["uncertainty"]["draws"])
    report["leakage_checks"]["each_id_exactly_once_oof_per_candidate"] = True
    report["completed_at_utc"] = timestamp()
    report["convergence_warning_count"] = sum(len(model["convergence_warnings"]) for model in report["model_artifacts"])
    result_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(result_path, report)
    save_json(output / "result_provenance.json", {"result_path": str(result_path),
                                                "result_sha256": sha256(result_path.read_bytes())})
    for name, value in report["summary"].items():
        print(json.dumps({"candidate": name, "matches": value["matches"], "n": value["n"],
                          "macro_f1": value["macro_f1"],
                          "recall": {label: value["per_class"][label]["recall"] for label in LABELS}}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    register_parser = commands.add_parser("register")
    register_parser.add_argument("--output", type=Path, required=True)
    register_parser.add_argument("--manifest", type=Path, default=ROOT / "research/results/corpus_comparison_20261001.json")
    register_parser.add_argument("--review", type=Path, default=ROOT / "research/results/development_overlap_review_20261002.json")
    recover_parser = commands.add_parser("recover")
    recover_parser.add_argument("--protocol", type=Path, required=True)
    recover_parser.add_argument("--output", type=Path, required=True)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--protocol", type=Path, required=True)
    run_parser.add_argument("--data", type=Path, required=True)
    run_parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "register":
        register(args.output, args.manifest.resolve(), args.review.resolve())
    elif args.command == "recover":
        recover(args.protocol, args.output)
    else:
        run(args.protocol, args.data, args.result)


if __name__ == "__main__":
    main()
