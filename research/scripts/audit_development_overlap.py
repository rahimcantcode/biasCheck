"""Read train/validation only; surface overlap candidates without changing splits."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np


def shingles(text, width=5):
    if width < 1:
        raise ValueError("Positive shingle width required")
    tokens = re.findall(r"\w+", text.lower())
    return {tuple(tokens[i:i + width]) for i in range(len(tokens) - width + 1)}


def overlap(first, second):
    common = len(first & second)
    union = len(first | second)
    minimum = min(len(first), len(second))
    return {"shared_5grams": common, "jaccard": common / union if union else 0.,
            "shorter_containment": common / minimum if minimum else 0.}


def shared_paragraphs(rows):
    segments = {}
    for split, items in rows.items():
        for row in items:
            for paragraph in re.split(r"\n\s*\n", row["text"]):
                normalized = " ".join(paragraph.lower().split())
                if len(normalized.split()) < 8:
                    continue
                key = hashlib.sha256(normalized.encode()).hexdigest()
                group = segments.setdefault(key, {"sha256": key, "word_n": len(normalized.split()), "train": set(), "validation": set()})
                group[split].add(row["id"])
    return sorted([{**g, "train": sorted(g["train"]), "validation": sorted(g["validation"])}
                   for g in segments.values() if g["train"] and g["validation"]],
                  key=lambda g: len(g["train"]) + len(g["validation"]), reverse=True)


def verify(rows, provenance, arrays, data):
    for split, items in rows.items():
        ids = [r["id"] for r in items]
        if not ids or len(ids) != len(set(ids)) or ids != provenance["records"][split]["ids"]:
            raise ValueError("Missing, duplicate or misaligned IDs")
        if hashlib.sha256((data / f"{split}.jsonl").read_bytes()).hexdigest() != provenance["records"][split]["data_sha256"]:
            raise ValueError("Feature source hash mismatch")
        if arrays[split].ndim != 2 or arrays[split].shape[0] != len(items) or not np.isfinite(arrays[split]).all():
            raise ValueError("Invalid feature dimensions or values")
        if np.any(np.linalg.norm(arrays[split], axis=1) == 0):
            raise ValueError("Zero feature vector")
    if arrays["train"].shape[1] != arrays["validation"].shape[1]:
        raise ValueError("Feature dimensions differ")


def run(data, features, output):
    if output.exists():
        raise ValueError("Use a new output path")
    rows = {s: [json.loads(line) for line in (data / f"{s}.jsonl").read_text().splitlines()]
            for s in ("train", "validation")}
    provenance = json.loads(features.with_suffix(".json").read_text())
    with np.load(features, allow_pickle=False) as loaded:
        arrays = {s: loaded[s] for s in rows}
    verify(rows, provenance, arrays, data)
    vectors = {s: a / np.linalg.norm(a, axis=1, keepdims=True) for s, a in arrays.items()}
    cosine = vectors["validation"] @ vectors["train"].T
    grams = {s: [shingles(r["text"]) for r in items] for s, items in rows.items()}
    pairs = []
    for vi, valid in enumerate(rows["validation"]):
        for ti, train in enumerate(rows["train"]):
            score = overlap(grams["validation"][vi], grams["train"][ti])
            pairs.append({"validation_id": valid["id"], "train_id": train["id"],
                          "cosine": float(cosine[vi, ti]), **score,
                          "same_event_string": valid["event"] == train["event"],
                          "same_normalized_text_hash": valid["text_sha256"] == train["text_sha256"]})
    # Thresholds only nominate review candidates; they do not establish leakage.
    flagged = [p for p in pairs if p["cosine"] >= .85 or p["jaccard"] >= .3 or
               (p["shorter_containment"] >= .5 and p["shared_5grams"] >= 20)]
    nearest = [max((p for p in pairs if p["validation_id"] == row["id"]), key=lambda p: p["cosine"])
               for row in rows["validation"]]
    report = {"purpose": "Development overlap audit, not proof of independence or model accuracy",
              "reserved_test_read": False, "split_changes": False, "labels_used_for_selection": False,
              "encoder": provenance, "features_sha256": hashlib.sha256(features.read_bytes()).hexdigest(),
              "train_n": len(rows["train"]), "validation_n": len(rows["validation"]), "pair_n": len(pairs),
              "thresholds": {"cosine_min": .85, "jaccard_min": .3, "containment_min": .5, "containment_shared_5grams_min": 20},
              "exact_id_overlap": sorted({r["id"] for r in rows["train"]} & {r["id"] for r in rows["validation"]}),
              "same_event_pair_n": sum(p["same_event_string"] for p in pairs),
              "same_normalized_text_pair_n": sum(p["same_normalized_text_hash"] for p in pairs),
              "shared_paragraphs": shared_paragraphs(rows),
              "flagged_pairs": sorted(flagged, key=lambda p: p["cosine"], reverse=True),
              "top_cosine_pairs": sorted(pairs, key=lambda p: p["cosine"], reverse=True)[:20],
              "top_lexical_pairs": sorted(pairs, key=lambda p: p["jaccard"], reverse=True)[:20],
              "nearest_train_per_validation": nearest,
              "limitations": ["Semantic threshold is heuristic", "Shared topic or quotation is not duplicate article proof",
                              "Publisher, syndication, pretraining and test overlap are not resolved"]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("train_n", "validation_n", "pair_n", "same_event_pair_n", "same_normalized_text_pair_n", "flagged_pairs")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("data", "features", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.features, args.output)
