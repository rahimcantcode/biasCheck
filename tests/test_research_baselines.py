"""Audit tests protect denominators and catch changed historical metric claims."""
import json
from pathlib import Path

import pytest

from research.scripts.summarize_research_baselines import (
    ROOT, agree, build_summary, classification, phrase_metrics, signatures,
)


def test_classification_rejection_counts_as_miss():
    rows = [{"id": "a", "reference": "LEFT", "prediction": "LEFT"},
            {"id": "b", "reference": "LEFT", "prediction": None},
            {"id": "c", "reference": "RIGHT", "prediction": "CENTER"}]
    result = classification(rows)
    assert result["n"] == 3
    assert result["correct"] == 1
    assert result["accuracy"] == 1 / 3
    assert result["per_class"]["LEFT"]["recall"] == .5
    assert result["macro_f1"] == pytest.approx((2 / 3) / 3)
    assert result["abstentions_or_invalid"] == 1


def test_duplicate_ids_cannot_inflate_sample_size():
    with pytest.raises(ValueError, match="Duplicate"):
        classification([{"id": "a", "reference": "LEFT", "prediction": "LEFT"}] * 2)


def test_nonfinite_and_missing_metric_claims_are_rejected():
    with pytest.raises(ValueError):
        agree({"accuracy": .5}, {"accuracy": float("nan")}, "test")
    with pytest.raises(ValueError, match="missing"):
        agree({"accuracy": .5}, {}, "test")


def test_failed_negative_is_not_counted_as_correct():
    rows = [{"id": "missing", "category": "nonpolitical", "text": "hello", "expected": []},
            {"id": "empty", "category": "nonpolitical", "text": "bye", "expected": []}]
    result = phrase_metrics(rows, {"empty": {"spans": []}})["totals"]
    assert result["cases"] == 2
    assert result["exact_cases"] == 1
    assert result["covered_cases"] == 1
    assert result["no_expected_span_cases_with_false_highlights"] == 0
    assert result["no_expected_span_covered_cases"] == 1


def test_same_words_wrong_voice_or_direction_are_not_correct_spans():
    wanted = {"text": "policy", "occurrence": 0, "label": "LEFT", "attribution": "quoted"}
    rows = [{"id": "a", "text": "policy", "category": "quote", "expected": [wanted]}]
    for change in ({"attribution": "author"}, {"label": "RIGHT"}):
        result = phrase_metrics(rows, {"a": {"spans": [{**wanted, **change}]}})["totals"]
        assert result["exact_recovered_spans"] == 0
        assert result["missed_spans"] == 1
        assert result["false_highlights"] == 1


def test_literal_unicode_occurrence_and_missing_phrase():
    span = {"text": "café", "occurrence": 1, "label": "LEFT", "attribution": "author"}
    assert signatures("🙂 café café", [span]) == {(7, 11, "LEFT", "author")}
    with pytest.raises(ValueError, match="not in source"):
        signatures("🙂 café", [span])
    with pytest.raises(ValueError, match="Invalid occurrence"):
        signatures("🙂 café café", [{**span, "occurrence": True}])


def test_unknown_phrase_prediction_id_rejected():
    with pytest.raises(ValueError, match="unexpected"):
        phrase_metrics([{"id": "a", "category": "negative", "text": "hi", "expected": []}],
                       {"b": {"spans": []}})


def test_published_replay_matches_generated_summary_and_known_counts():
    computed = build_summary()
    saved = json.loads((ROOT / "research/team_20261003/baseline_summary.json").read_text())
    assert computed == saved
    assert computed["corpus_development_66"]["live_roberta"]["correct"] == 31
    assert computed["training_oof_115"]["raw_lr_C1"]["correct"] == 64
    assert computed["training_oof_115"]["raw_unanimous_lr_C1"]["correct"] == 51
    phrase = computed["phrase_synthetic_development"]["v5_paired"]["v5_sealed_transfer"]["totals"]
    assert (phrase["exact_recovered_spans"], phrase["expected_spans"], phrase["predicted_spans"]) == (16, 19, 22)
    assert computed["stance_development_274"]["qwen3_4b"]["correct_reported_aggregate"] == 181
    assert computed["new_inference_performed"] is False


def test_changed_published_accuracy_fails_replay(monkeypatch):
    original = Path.read_bytes

    def changed_read(path):
        content = original(path)
        if path.name == "corpus_comparison_20261001.json":
            record = json.loads(content)
            record["models"]["live_roberta"]["metrics"]["accuracy"] = .99
            return json.dumps(record).encode()
        return content

    monkeypatch.setattr(Path, "read_bytes", changed_read)
    with pytest.raises(ValueError, match="live_roberta: accuracy"):
        build_summary()


def test_replay_reads_only_explicit_publication_paths(monkeypatch):
    original = Path.read_bytes
    visited = []

    def tracked_read(path):
        visited.append(path.relative_to(ROOT).as_posix())
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", tracked_read)
    result = build_summary()
    assert set(visited) == set(result["source_sha256"])
    assert len(visited) == 10
    assert not any("/data/" in p or p.endswith(("test.jsonl", "holdout.jsonl")) for p in visited)


def test_failed_attempt_cannot_keep_a_prediction(monkeypatch):
    original = Path.read_bytes

    def changed_read(path):
        content = original(path)
        if path.name == "phrase_contract_v2_20261002_publication.json":
            record = json.loads(content)
            suite = record["suites"]["original"]
            successful = next(a for a in suite["attempts"] if a["id"] in suite["predictions"])
            successful["status"] = "failed"
            return json.dumps(record).encode()
        return content

    monkeypatch.setattr(Path, "read_bytes", changed_read)
    with pytest.raises(ValueError, match="Predictions differ from successful"):
        build_summary()
