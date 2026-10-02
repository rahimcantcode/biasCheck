"""Training-only grouped CV of a fixed footer-invariance augmentation."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from boilerplate_ablation import FOOTERS, paragraph_hash, strip_footers
from corpus_experiment import metrics


def variants(text, footers):
    clean, _ = strip_footers(text)
    return [clean] + [clean + "\n\n" + footer for footer in footers]


def augment(rows, footers):
    texts, labels, weights = [], [], []
    for row in rows:
        copies = variants(row["text"], footers)
        texts.extend(copies)
        labels.extend([row["label"]] * len(copies))
        weights.extend([1 / len(copies)] * len(copies))
    return texts, labels, weights


def run(data, output):
    if output.exists():
        raise ValueError("Use a new output directory")
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    if not rows or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Expected unique training IDs")
    paragraphs = {paragraph_hash(p): p for r in rows for p in re.split(r"\n\s*\n", r["text"])
                  if paragraph_hash(p) in FOOTERS}
    if set(paragraphs) != FOOTERS:
        raise ValueError("Both fixed footer templates must exist in training input")
    footers = [paragraphs[h] for h in sorted(FOOTERS)]
    output.mkdir(parents=True)
    record = {"purpose": "Training-only grouped development CV; not independent accuracy",
              "validation_read": False, "reserved_test_read": False, "release_approved": False,
              "input_sha256": hashlib.sha256(data.read_bytes()).hexdigest(), "footer_hashes": sorted(FOOTERS),
              "footer_provenance": "Known hashes selected during previous development audit; templates extracted from training input",
              "fold_method": "GroupKFold(5), no shuffle, normalized source event strings; family independence unproven",
              "settings": {"C": 1., "class_weight": "balanced", "seed": 20261001, "max_iter": 1000,
                           "vectorizer": "word (1,2), min_df=2, max_features=20000, sublinear_tf=True; fit raw training fold only",
                           "augmented_row_weight": 1/3}, "folds": [], "oof": {"baseline": [], "augmented": []}}
    (output / "protocol.json").write_text(json.dumps(record, indent=2))
    for fold, (train, held) in enumerate(GroupKFold(5).split(rows, groups=[r["event"] for r in rows])):
        train_rows, held_rows = [rows[i] for i in train], [rows[i] for i in held]
        if {r["event"] for r in train_rows} & {r["event"] for r in held_rows}:
            raise ValueError("Event strings cross folds")
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000, sublinear_tf=True)
        vectorizer.fit([r["text"] for r in train_rows])
        split_record = {"fold": fold, "train_ids": [r["id"] for r in train_rows], "held_ids": [r["id"] for r in held_rows], "models": {}}
        for name in ("baseline", "augmented"):
            texts, labels, weights = augment(train_rows, footers) if name == "augmented" else ([r["text"] for r in train_rows], [r["label"] for r in train_rows], [1.] * len(train_rows))
            if not np.isclose(sum(weights), len(train_rows)):
                raise ValueError("Loss weight must preserve original sample mass")
            model = LogisticRegression(C=1., class_weight="balanced", random_state=20261001, max_iter=1000)
            model.fit(vectorizer.transform(texts), labels, sample_weight=weights)
            original = model.predict(vectorizer.transform([r["text"] for r in held_rows])).tolist()
            views = [v for r in held_rows for v in variants(r["text"], footers)]
            counterfactual = model.predict(vectorizer.transform(views)).reshape(len(held_rows), 3).tolist()
            path = output / f"fold-{fold}-{name}.joblib"
            joblib.dump({"vectorizer": vectorizer, "classifier": model}, path)
            split_record["models"][name] = {"model_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                           "train_row_n": len(texts), "train_weight_sum": float(sum(weights)),
                                           "original_metrics": metrics(held_rows, original)}
            record["oof"][name].extend({"id": r["id"], "fold": fold, "prediction": p, "variant_predictions": v,
                                        "all_variants_agree": len(set(v)) == 1} for r, p, v in zip(held_rows, original, counterfactual))
        record["folds"].append(split_record)
        print("fold", fold, "completed", len(held_rows), flush=True)
    record["summary"] = {}
    for name, values in record["oof"].items():
        by_id = {v["id"]: v for v in values}
        if len(values) != len(rows) or set(by_id) != {r["id"] for r in rows}:
            raise ValueError("Incomplete or repeated out-of-fold coverage")
        record["summary"][name] = {"original_metrics": metrics(rows, [by_id[r["id"]]["prediction"] for r in rows]),
                                   "variant_consistent_n": sum(v["all_variants_agree"] for v in values),
                                   "variant_consistent_fraction": sum(v["all_variants_agree"] for v in values) / len(rows)}
    (output / "training_results.json").write_text(json.dumps(record, indent=2))
    browser = [{"id": rows[0]["id"] + "-original", "text": rows[0]["text"]}]
    browser += [{"id": rows[0]["id"] + f"-variant-{i}", "text": text} for i, text in enumerate(variants(rows[0]["text"], footers))]
    (output / "browser_variants.json").write_text(json.dumps(browser, indent=2))
    print(json.dumps(record["summary"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.output)
