"""Offline audit of published DEVELOPMENT predictions. No inference or sealed reads.

Uses only the explicitly enumerated publication records below. Article and phrase
scores are recomputed from example-level references and predictions, independently
of the original scoring implementation. Stance gold is not published per example,
so that section only checks aggregate arithmetic and raw prediction counts.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = "research/experiments/phrase_stages_20261002"
LABELS = ("LEFT", "CENTER", "RIGHT")
PHRASE_FILES = {
    "qwen3_4b_v2": "research/results/phrase_contract_v2_20261002_publication.json",
    "instruct2507_v2": "research/results/phrase_instruct2507_comparison_20261002.json",
    "v3": f"{SNAPSHOT}/research/checkpoints/phrase-pipeline-v3-20261002/results.json",
    "v4": f"{SNAPSHOT}/research/checkpoints/phrase-recall-v4-20261002/results.json",
    "v5_paired": f"{SNAPSHOT}/results_v5.json",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(rows):
    ids = [r["id"] for r in rows]
    require(len(ids) == len(set(ids)), "Duplicate example IDs")
    return set(ids)


def agree(actual, recorded, context):
    for key, value in actual.items():
        require(key in recorded, f"{context}: missing recorded metric {key}")
        expected = recorded[key]
        if isinstance(value, float):
            require(isinstance(expected, (int, float)) and math.isfinite(expected)
                    and math.isclose(value, expected, abs_tol=1e-12), f"{context}: {key}")
        else:
            require(value == expected, f"{context}: {key}")


def classification(rows):
    """Fixed three-label scores; rejected/absent predictions remain in denominator."""
    unique(rows)
    require(bool(rows), "No reference rows")
    matrix = [[0 for _ in LABELS] for _ in LABELS]
    misses = Counter()
    for row in rows:
        require(row["reference"] in LABELS, "Unknown reference label")
        if row["prediction"] not in LABELS:
            require(row["prediction"] in (None, "ABSTAIN", "INVALID"), "Unknown prediction label")
            misses[row["reference"]] += 1
        else:
            matrix[LABELS.index(row["reference"])][LABELS.index(row["prediction"])] += 1
    per_class = {}
    for i, label in enumerate(LABELS):
        tp, support = matrix[i][i], sum(matrix[i]) + misses[label]
        emitted = sum(row[i] for row in matrix)
        per_class[label] = {"support": support, "recall": tp / support if support else 0,
                            "precision": tp / emitted if emitted else 0,
                            "f1": 2 * tp / (support + emitted) if support + emitted else 0}
    correct = sum(matrix[i][i] for i in range(3))
    return {"n": len(rows), "correct": correct, "accuracy": correct / len(rows),
            "macro_f1": sum(c["f1"] for c in per_class.values()) / 3,
            "label_order": list(LABELS), "confusion_matrix": matrix,
            "abstentions_or_invalid": sum(misses.values()), "per_class": per_class}


def signatures(text, spans):
    """Resolve literal Unicode source positions without importing application code."""
    values = []
    for span in spans:
        phrase, occurrence = span["text"], span["occurrence"]
        require(isinstance(phrase, str) and bool(phrase), "Empty or invalid phrase")
        require(type(occurrence) is int and occurrence >= 0, "Invalid occurrence")
        require(span["label"] in ("LEFT", "RIGHT"), "Invalid phrase direction")
        require(span["attribution"] in ("author", "quoted", "unknown"), "Invalid attribution")
        start = -1
        for _ in range(occurrence + 1):
            start = text.find(phrase, start + 1)
            require(start >= 0, "Phrase occurrence not in source")
        values.append((start, start + len(phrase), span["label"], span["attribution"]))
    require(len(set(values)) == len(values), "Duplicate source spans")
    return set(values)


def phrase_metrics(rows, predictions):
    ids = unique(rows)
    require(bool(rows) and set(predictions) <= ids, "Empty fixture or unexpected prediction IDs")
    totals = Counter(cases=len(rows), covered_cases=0, exact_cases=0, expected_spans=0,
                     predicted_spans=0, exact_recovered_spans=0, false_highlights=0,
                     missed_spans=0, no_expected_span_cases=0,
                     no_expected_span_cases_with_false_highlights=0,
                     no_expected_span_covered_cases=0)
    author = Counter(expected_spans=0, predicted_spans=0, exact_recovered_spans=0,
                     false_highlights=0, missed_spans=0)
    errors = []
    for row in rows:
        want = signatures(row["text"], row["expected"])
        covered = row["id"] in predictions
        got = signatures(row["text"], predictions[row["id"]]["spans"]) if covered else set()
        exact = covered and want == got
        totals.update(covered_cases=int(covered), exact_cases=int(exact), expected_spans=len(want),
                      predicted_spans=len(got), exact_recovered_spans=len(want & got),
                      false_highlights=len(got - want), missed_spans=len(want - got),
                      no_expected_span_cases=int(not want),
                      no_expected_span_cases_with_false_highlights=int(not want and bool(got)),
                      no_expected_span_covered_cases=int(not want and covered))
        aw, ag = {s for s in want if s[3] == "author"}, {s for s in got if s[3] == "author"}
        author.update(expected_spans=len(aw), predicted_spans=len(ag),
                      exact_recovered_spans=len(aw & ag), false_highlights=len(ag - aw),
                      missed_spans=len(aw - ag))
        if not exact:
            errors.append({"id": row["id"], "category": row["category"], "covered": covered,
                           "false_highlights": len(got - want), "missed_spans": len(want - got)})
    def rates(values):
        values = dict(values)
        values["exact_span_recall"] = (values["exact_recovered_spans"] / values["expected_spans"]
                                        if values["expected_spans"] else None)
        values["exact_span_precision"] = (values["exact_recovered_spans"] / values["predicted_spans"]
                                           if values["predicted_spans"] else None)
        return values
    return {"totals": rates(totals), "author": rates(author), "error_cases": errors}


def build_summary(root=ROOT):
    sources = {}

    def read(relative):
        # Deliberately no discovery/globbing of data or checkpoint directories.
        path = root / relative
        data = path.read_bytes()
        sources[relative] = hashlib.sha256(data).hexdigest()
        return json.loads(data)

    corpus = read("research/results/corpus_comparison_20261001.json")
    corpus_models, reference_signature = {}, None
    for name, model in corpus["models"].items():
        rows = model["predictions"]
        signature = sorted((r["id"], r["reference"], r["strict_agreement"]) for r in rows)
        require(reference_signature is None or signature == reference_signature, "Model reference mismatch")
        reference_signature = signature
        computed = classification(rows)
        agree({k: computed[k] for k in ("n", "accuracy", "macro_f1", "label_order", "confusion_matrix")},
              model["metrics"], name)
        strict = classification([r for r in rows if r["strict_agreement"]])
        agree({k: strict[k] for k in ("n", "accuracy", "macro_f1")}, model["metrics"]["strict_agreement"], name)
        computed["unanimous_reference_subset"] = strict
        corpus_models[name] = computed

    provenance = read("research/results/training_label_provenance_20261002.json")
    references = {r["id"]: r["label"] for r in provenance["references"]}
    unique(provenance["references"])
    training = {}
    for name, predictions in provenance["oof"].items():
        require(unique(predictions) == set(references), "Incomplete out-of-fold predictions")
        rows = [{"id": p["id"], "reference": references[p["id"]], "prediction": p["prediction"]}
                for p in predictions]
        computed = classification(rows)
        agree({k: computed[k] for k in ("n", "accuracy", "macro_f1", "confusion_matrix")},
              provenance["summary"][name]["all_115"], name)
        training[name] = computed

    transfer = read(f"{SNAPSHOT}/transfer32_fixture.json")
    phrases = {}
    for experiment, relative in PHRASE_FILES.items():
        record = read(relative)
        require(record["release_approved"] is False, "Unexpected release status")
        protocol, suites = record["protocol"], {}
        for name, suite in record["suites"].items():
            if "fixture_snapshots" in protocol:
                rows = protocol["fixture_snapshots"][name]["rows"]
            elif name.startswith("v5_development_"):
                rows = protocol["development_fixture_snapshots"][name.removeprefix("v5_development_")]["rows"]
            else:
                require(sources[f"{SNAPSHOT}/transfer32_fixture.json"] == protocol["sealed_fixture_sha256"],
                        "Previously exposed transfer fixture hash mismatch")
                rows = transfer["rows"]
            require(unique(suite["attempts"]) == unique(rows), "Attempt denominator mismatch")
            require(all(a["status"] in ("validated", "failed") for a in suite["attempts"]),
                    "Unexpected phrase attempt status")
            require({a["id"] for a in suite["attempts"] if a["status"] == "validated"}
                    == set(suite["predictions"]), "Predictions differ from successful attempts")
            for attempt in suite["attempts"]:
                if "source_text_sha256" in attempt:
                    text = next(r["text"] for r in rows if r["id"] == attempt["id"])
                    require(hashlib.sha256(text.encode()).hexdigest() == attempt["source_text_sha256"],
                            "Attempt source text mismatch")
            computed = phrase_metrics(rows, suite["predictions"])
            recorded = suite.get("evaluation", suite.get("metrics", {}).get("primary_exact"))
            published_totals = dict(recorded["totals"])
            for old, new in (("neutral_cases", "no_expected_span_cases"),
                             ("neutral_cases_with_false_highlights", "no_expected_span_cases_with_false_highlights")):
                if old in published_totals:
                    published_totals[new] = published_totals[old]
            compared_totals = dict(computed["totals"])
            if "no_expected_span_covered_cases" not in published_totals:
                # This newly recomputed count was absent from the older v2 tables.
                require(experiment in ("qwen3_4b_v2", "instruct2507_v2"), "Missing coverage metric")
                compared_totals.pop("no_expected_span_covered_cases")
            agree(compared_totals, published_totals, experiment + "/" + name)
            agree(computed["author"], recorded["author_renderable_totals"], experiment + "/" + name)
            computed["data_status"] = "AI-authored exposed development, not independent human gold"
            suites[name] = computed
        phrases[experiment] = suites

    stance = {}
    for model in ("qwen3_4b", "instruct2507"):
        record = read(f"research/results/argument_stance_{model}_dev_20261002.json")
        attempts = record["attempts"]
        unique(attempts)
        labels = Counter()
        for attempt in attempts:
            require(attempt["status"] == "valid", "Unexpected invalid saved stance attempt")
            choice = attempt["raw_response"]["choices"]
            require(len(choice) == 1 and choice[0]["finish_reason"] == "stop", "Incomplete stance response")
            parsed = json.loads(choice[0]["message"]["content"])
            require(set(parsed) == {"id", "label"} and parsed["id"] == "article"
                    and type(parsed["label"]) is int and parsed["label"] in (0, 1), "Invalid stance response")
            labels[str(parsed["label"])] += 1
        metrics = record["evaluation"]["metrics"]["all"]
        confusion = metrics["confusion"]
        n = sum(sum(row.values()) for row in confusion.values())
        correct = confusion["0"]["0"] + confusion["1"]["1"]
        require(n == len(attempts) == metrics["n_all_inputs"], "Stance denominator mismatch")
        require(dict(labels) == {label: sum(row[label] for row in confusion.values()) for label in ("0", "1")},
                "Raw labels differ from reported confusion totals")
        agree({"accuracy_all_inputs": correct / n}, metrics, model)
        stance[model] = {"n": n, "correct_reported_aggregate": correct, "reference_agreement": correct / n,
                         "no_stance_false_calls_reported": confusion["0"]["1"],
                         "no_stance_reference_n_reported": sum(confusion["0"].values()),
                         "raw_prediction_counts_replayed": dict(labels),
                         "verification": "Raw response contract and prediction totals plus aggregate arithmetic only; per-ID gold unavailable in publication",
                         "task": "UK human stance-presence, not U.S. article ideology"}

    return {"schema_version": 1, "release_approved": False, "new_inference_performed": False,
            "sealed_data_read": False, "software_test_counts_are_accuracy": False,
            "scope": "Replay of previously published development records only; not new accuracy evidence",
            "corpus_development_66": corpus_models, "training_oof_115": training,
            "phrase_synthetic_development": phrases, "stance_development_274": stance,
            "limitations": ["No independent human adjudication or new test evaluation",
                            "No bootstrap uncertainty or source label correctness revalidated",
                            "No runtime inference, browser behavior or deployment verified",
                            "Historic high-score incorrect count lacks individual scores here and is not independently replayed",
                            "Historic sealed_transfer suite names denote the already published 32 cases, not the sealed 89 or 726 corpus examples"],
            "source_sha256": sources}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_summary()
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        require(args.output.resolve() not in {(ROOT / p).resolve() for p in result["source_sha256"]},
                "Refusing to overwrite historic input records")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Verified {len(result['source_sha256'])} publication files; wrote {args.output}")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
