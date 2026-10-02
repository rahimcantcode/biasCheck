"""Reproducible research-only training on PoliticalBiasCorpus human annotations.

Uses event-disjoint development splits, retains disagreement provenance, and keeps
the test partition unopened by the training command. Text and models stay local.
"""
import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

LABELS = ["LEFT", "CENTER", "RIGHT"]


def digest(text):
    return hashlib.sha256(" ".join(text.lower().split()).encode()).hexdigest()


def prepare(source, output):
    from sklearn.model_selection import GroupShuffleSplit

    inputs = {r["docid"]: r for r in csv.DictReader((source / "gold/HIT_inputs/mturk_input_300.csv").open())}
    rows = []
    seen = set()
    for path in sorted((source / "gold").glob("gold_docs*.csv")):
        for row in csv.DictReader(path.open()):
            shown = inputs[row["docid"]]
            text = "\n\n".join(shown[k].strip() for k in ("title", "snippet1", "snippet2", "snippet3"))
            key = digest(text)
            if key in seen:
                raise ValueError("Duplicate text requires explicit adjudication")
            seen.add(key)
            rows.append({"id": row["docid"], "text": text,
                         "label": row["human_label"].upper(),
                         "event": " ".join(row["event"].lower().split()),
                         "strict_agreement": row["worker_1_label"] == row["worker_2_label"],
                         "worker_labels": [row["worker_1_label"], row["worker_2_label"]],
                         "text_sha256": key})
    rows.sort(key=lambda r: r["id"])
    groups = [r["event"] for r in rows]
    development, test = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=20261001).split(rows, groups=groups))
    dev_rows = [rows[i] for i in development]
    train, valid = next(GroupShuffleSplit(n_splits=1, test_size=.30, random_state=20261002).split(dev_rows, groups=[r["event"] for r in dev_rows]))
    splits = {"train": [dev_rows[i] for i in train], "validation": [dev_rows[i] for i in valid], "test": [rows[i] for i in test]}
    output.mkdir(parents=True, exist_ok=True)
    if (output / "manifest.json").exists():
        raise ValueError("Refusing to overwrite a frozen experiment")
    manifest = {"dataset": "https://github.com/ksolaiman/PoliticalBiasCorpus",
                "revision": subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip(),
                "license": "CC-BY-NC-SA-4.0; research only; not approved for commercial deployment",
                "split_method": "Exact text unique; normalized event-string-group-disjoint train/validation/test; seeds 20261001,20261002; not proof of event-family independence",
                "text_view": "Title and three excerpts shown to annotators, not full article HTML",
                "limitations": ["Different event strings can describe a shared news episode; event-family audit required", "Publisher overlap not excluded", "Pretraining overlap unknown", "Center/partisan disagreements resolved toward partisan by source", "Historical US news only", "Strict-agreement subset is selection-biased toward easier items"], "splits": {}}
    for name, items in splits.items():
        content = "".join(json.dumps(r) + "\n" for r in items)
        (output / f"{name}.jsonl").write_text(content)
        manifest["splits"][name] = {"n": len(items), "labels": {label: sum(r["label"] == label for r in items) for label in LABELS}, "strict_agreement_n": sum(r["strict_agreement"] for r in items), "sha256": hashlib.sha256(content.encode()).hexdigest(), "ids": [r["id"] for r in items]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    # These inputs deliberately omit reference labels, event names, and publisher metadata.
    blind = [{"id": r["id"], "text": r["text"]} for r in splits["validation"]]
    (output / "validation_blind.json").write_text(json.dumps(blind, indent=2))
    print(json.dumps({k: {x: v for x, v in value.items() if x != "ids"} for k, value in manifest["splits"].items()}, indent=2))


def metrics(rows, predictions):
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
    if len(rows) != len(predictions) or not rows:
        raise ValueError("Predictions must match a nonempty dataset")
    gold = [r["label"] for r in rows]
    result = {"n": len(rows), "accuracy": accuracy_score(gold, predictions), "macro_f1": f1_score(gold, predictions, labels=LABELS, average="macro", zero_division=0), "label_order": LABELS, "confusion_matrix": confusion_matrix(gold, predictions, labels=LABELS).tolist(), "per_class": classification_report(gold, predictions, labels=LABELS, output_dict=True, zero_division=0)}
    strict = [(r, p) for r, p in zip(rows, predictions) if r["strict_agreement"]]
    result["strict_agreement"] = {"n": len(strict), "accuracy": sum(r["label"] == p for r, p in strict) / len(strict) if strict else None,
                                  "macro_f1": f1_score([r["label"] for r, _ in strict], [p for _, p in strict], labels=LABELS, average="macro", zero_division=0) if strict else None,
                                  "label_counts": {label: sum(r["label"] == label for r, _ in strict) for label in LABELS}}
    return result


def train(data, output):
    import joblib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import FeatureUnion, Pipeline

    if output.exists():
        raise ValueError("Use a new output directory")
    train_rows = [json.loads(s) for s in (data / "train.jsonl").read_text().splitlines()]
    valid = [json.loads(s) for s in (data / "validation.jsonl").read_text().splitlines()]
    for field in ("event", "text_sha256", "id"):
        if {r[field] for r in train_rows} & {r[field] for r in valid}:
            raise ValueError(f"Leaking {field}")
    output.mkdir(parents=True)
    reports = []
    for feature in ("word", "word_char"):
        for regularization in (.1, 1., 10.):
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=20000)
            if feature == "word_char":
                vectorizer = FeatureUnion([("word", vectorizer), ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, sublinear_tf=True, max_features=20000))])
            model = Pipeline([("features", vectorizer), ("classifier", LogisticRegression(C=regularization, class_weight="balanced", max_iter=1000, random_state=20261001))])
            model.fit([r["text"] for r in train_rows], [r["label"] for r in train_rows])
            pred = model.predict([r["text"] for r in valid]).tolist()
            name = f"{feature}_C{regularization}"
            report = {"name": name, "metrics": metrics(valid, pred), "predictions": [{"id": r["id"], "prediction": p} for r, p in zip(valid, pred)]}
            reports.append(report)
            joblib.dump(model, output / f"{name}.joblib")
            print(name, json.dumps(report["metrics"]), flush=True)
    best = max(reports, key=lambda r: r["metrics"]["macro_f1"])
    record = {"purpose": "Human-annotation event-disjoint validation; test not evaluated", "train_n": len(train_rows), "best": best["name"], "candidates": reports, "data_manifest": json.loads((data / "manifest.json").read_text()), "release_approved": False}
    (output / "training_results.json").write_text(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "train"])
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    (prepare if args.mode == "prepare" else train)(args.input, args.output)
