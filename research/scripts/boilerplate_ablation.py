"""Research-only 2x2 text-view ablation; preserve frozen source inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import re

FOOTERS = frozenset({
    "9d8863723d831cbc7379f4ce548ebe95c6112f24fd467564349d57b9d07296e7",
    "49d99ae25ab648533a98e51bac27300c69d32a3079294f4d4c7fcda01e900474",
})


def paragraph_hash(text):
    return hashlib.sha256(" ".join(text.lower().split()).encode()).hexdigest()


def strip_footers(text, hashes=FOOTERS):
    pieces = re.split(r"\n\s*\n", text)
    removed = [paragraph_hash(piece) for piece in pieces if paragraph_hash(piece) in hashes]
    if not removed:
        return text, []
    retained = "\n\n".join(piece for piece in pieces if paragraph_hash(piece) not in hashes)
    if not retained.strip():
        raise ValueError("Cleaning would remove all text")
    return retained, removed


def run(data, baseline, output):
    import joblib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from corpus_experiment import digest, metrics

    if output.exists():
        raise ValueError("Use a new output directory")
    rows = {s: [json.loads(line) for line in (data / f"{s}.jsonl").read_text().splitlines()]
            for s in ("train", "validation")}
    for items in rows.values():
        if not items or len({r["id"] for r in items}) != len(items):
            raise ValueError("Empty data or duplicate IDs")
    views, transformations = {}, {}
    for split, items in rows.items():
        views[split] = {"raw": [r["text"] for r in items], "clean": []}
        transformations[split] = []
        for row in items:
            cleaned, removed = strip_footers(row["text"])
            views[split]["clean"].append(cleaned)
            transformations[split].append({"id": row["id"], "removed_paragraph_hashes": removed,
                                            "source_text_sha256": digest(row["text"]), "clean_text_sha256": digest(cleaned)})
    for view in ("raw", "clean"):
        if {digest(t) for t in views["train"][view]} & {digest(t) for t in views["validation"][view]}:
            raise ValueError("Cross-split exact duplicate after transformation")
    if {r["id"] for r in rows["train"]} & {r["id"] for r in rows["validation"]}:
        raise ValueError("Cross-split ID overlap")
    output.mkdir(parents=True)
    report = {"purpose": "Development-informed nuisance ablation, not independent accuracy",
              "release_approved": False, "reserved_test_read": False, "labels_changed": False,
              "reference_context": "Humans saw raw excerpts; cleaned-view agreement is a proxy",
              "footer_hashes": sorted(FOOTERS), "C": 1., "seed": 20261001,
              "features": {"ngram_range": [1, 2], "min_df": 2, "sublinear_tf": True, "max_features": 20000},
              "classifier": {"class_weight": "balanced", "max_iter": 1000},
              "input_hashes": {s: hashlib.sha256((data / f"{s}.jsonl").read_bytes()).hexdigest() for s in rows},
              "baseline_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
              "transformations": transformations, "evaluations": {}, "model_sha256": {}}
    (output / "protocol.json").write_text(json.dumps(report, indent=2))
    for split, items in rows.items():
        (output / f"{split}_clean.jsonl").write_text("".join(json.dumps({**r, "text": t, "source_text_sha256": r["text_sha256"], "text_sha256": digest(t)}) + "\n"
                                                                    for r, t in zip(items, views[split]["clean"])))
    for training in ("raw", "clean"):
        model = Pipeline([("features", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=20000)),
                          ("classifier", LogisticRegression(C=1., class_weight="balanced", max_iter=1000, random_state=20261001))])
        model.fit(views["train"][training], [r["label"] for r in rows["train"]])
        path = output / f"{training}_model.joblib"
        joblib.dump(model, path)
        report["model_sha256"][training] = hashlib.sha256(path.read_bytes()).hexdigest()
        for evaluation in ("raw", "clean"):
            pred = model.predict(views["validation"][evaluation]).tolist()
            scores = model.predict_proba(views["validation"][evaluation]).tolist()
            key = f"{training}_to_{evaluation}"
            report["evaluations"][key] = {"metrics": metrics(rows["validation"], pred),
                "probability_class_order": model.classes_.tolist(), "calibrated": False,
                "predictions": [{"id": r["id"], "prediction": p, "probabilities": score}
                                for r, p, score in zip(rows["validation"], pred, scores)]}
            print(key, report["evaluations"][key]["metrics"]["accuracy"], report["evaluations"][key]["metrics"]["macro_f1"], flush=True)
    prior = next(c for c in json.loads(baseline.read_text())["candidates"] if c["name"] == "word_C1.0")
    control = report["evaluations"]["raw_to_raw"]["predictions"]
    report["control_reproduces_previous_predictions"] = {p["id"]: p["prediction"] for p in prior["predictions"]} == {p["id"]: p["prediction"] for p in control}
    if not report["control_reproduces_previous_predictions"]:
        raise ValueError("Raw/raw control did not reproduce baseline; artifacts retained")
    report["inference_view_changes"] = {}
    for training in ("raw", "clean"):
        raw = report["evaluations"][f"{training}_to_raw"]["predictions"]
        clean = report["evaluations"][f"{training}_to_clean"]["predictions"]
        report["inference_view_changes"][training] = [{"id": a["id"], "raw_prediction": a["prediction"], "clean_prediction": b["prediction"],
                                                     "probability_l1_change": sum(abs(x-y) for x,y in zip(a["probabilities"], b["probabilities"]))}
                                                    for a, b in zip(raw, clean) if a["probabilities"] != b["probabilities"]]
    (output / "training_results.json").write_text(json.dumps(report, indent=2))
    browser = []
    for footer in sorted(FOOTERS):
        match = next((i for i, r in enumerate(transformations["validation"]) if footer in r["removed_paragraph_hashes"]), None)
        if match is not None:
            for view in ("raw", "clean"):
                browser.append({"id": rows["validation"][match]["id"] + "-" + view, "text": views["validation"][view][match]})
    (output / "browser_pairs.json").write_text(json.dumps(browser, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("data", "baseline", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    run(args.data, args.baseline, args.output)
