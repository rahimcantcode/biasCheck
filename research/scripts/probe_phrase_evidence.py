"""Explicitly opt-in, offline synthetic phrase extractor and complete diagnostics.

Uses the already-authenticated supported Codex CLI. NEVER import this provider in
HTTP serving code. No keys, token extraction, account setup, or public proxy.
Freeze the fixtures first; the model receives only IDs and FULL ORIGINAL TEXTS.
All batches and failures are retained. This is synthetic development evaluation,
not independent human validation or evidence of calibrated accuracy.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.evidence import (CACHE_VERSION, EVIDENCE_SOURCE, EXTRACTION_CONTRACT, EVIDENCE_SYSTEM_PROMPT,
                              EvidenceValidationError, model_output_schema,
                              text_sha256, validate_batch, validate_prediction)

MODEL = "gpt-6-astra"
PROMPT = EVIDENCE_SYSTEM_PROMPT


def _signature(span: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(span[key] for key in ("start", "end", "label", "attribution"))


def evaluate(rows: list[dict[str, Any]], predictions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Score ALL frozen rows; missing/rejected cases count as uncovered failures."""
    cases = []
    totals = {"cases": len(rows), "covered_cases": 0, "exact_cases": 0,
              "expected_spans": 0, "predicted_spans": 0, "exact_recovered_spans": 0,
              "false_highlights": 0, "missed_spans": 0, "neutral_cases": 0,
              "neutral_cases_with_false_highlights": 0}
    author_totals = {"cases": len(rows), "covered_cases": 0, "exact_cases": 0,
                     "expected_spans": 0, "predicted_spans": 0, "exact_recovered_spans": 0,
                     "false_highlights": 0, "missed_spans": 0,
                     "expected_author_cases": 0, "rendered_author_cases": 0,
                     "cases_without_expected_author_spans_with_false_highlights": 0}
    for row in rows:
        expected = validate_prediction(row["text"], {
            "spans": [{**span, "reason": "Developer-authored synthetic expectation"} for span in row["expected"]],
            "reason": "Developer-authored diagnostic, not human gold"})
        prediction = predictions.get(row["id"])
        covered = prediction is not None
        actual = validate_prediction(row["text"], prediction) if covered else []
        want, got = {_signature(s) for s in expected}, {_signature(s) for s in actual}
        matched, false, missed = len(want & got), len(got - want), len(want - got)
        exact = covered and want == got
        totals["covered_cases"] += int(covered)
        totals["exact_cases"] += int(exact)
        totals["expected_spans"] += len(want)
        totals["predicted_spans"] += len(got)
        totals["exact_recovered_spans"] += matched
        totals["false_highlights"] += false
        totals["missed_spans"] += missed
        totals["neutral_cases"] += int(not want)
        totals["neutral_cases_with_false_highlights"] += int(not want and bool(got))
        expected_chars = {n for span in expected for n in range(span["start"], span["end"])}
        actual_chars = {n for span in actual for n in range(span["start"], span["end"])}
        author_want = {_signature(span) for span in expected if span["attribution"] == "author"}
        author_got = {_signature(span) for span in actual if span["attribution"] == "author"}
        author_case = {"exact_match": covered and author_want == author_got,
                       "expected_spans": len(author_want), "predicted_spans": len(author_got),
                       "exact_recovered_spans": len(author_want & author_got),
                       "false_highlights": len(author_got - author_want), "missed_spans": len(author_want - author_got)}
        author_totals["covered_cases"] += int(covered)
        author_totals["exact_cases"] += int(author_case["exact_match"])
        for key in ("expected_spans", "predicted_spans", "exact_recovered_spans", "false_highlights", "missed_spans"):
            author_totals[key] += author_case[key]
        author_totals["expected_author_cases"] += int(bool(author_want))
        author_totals["rendered_author_cases"] += int(bool(author_got))
        author_totals["cases_without_expected_author_spans_with_false_highlights"] += int(not author_want and bool(author_got))
        cases.append({"id": row["id"], "category": row["category"], "text": row["text"],
                      "covered": covered, "exact_match": exact, "author_renderable": author_case, "expected_spans": expected,
                      "predicted_spans": actual, "exact_recovered_spans": matched,
                      "false_highlights": false, "missed_spans": missed,
                      "extra_highlighted_code_points": len(actual_chars - expected_chars),
                      "missed_highlighted_code_points": len(expected_chars - actual_chars),
                      "reason": prediction["reason"] if covered else "No valid model response"})
    totals["coverage"] = totals["covered_cases"] / len(rows) if rows else 0
    totals["exact_case_recovery"] = totals["exact_cases"] / len(rows) if rows else 0
    totals["exact_span_recall"] = totals["exact_recovered_spans"] / totals["expected_spans"] if totals["expected_spans"] else None
    totals["exact_span_precision"] = totals["exact_recovered_spans"] / totals["predicted_spans"] if totals["predicted_spans"] else None
    author_totals["coverage"] = author_totals["covered_cases"] / len(rows) if rows else 0
    author_totals["exact_case_recovery"] = author_totals["exact_cases"] / len(rows) if rows else 0
    author_totals["exact_span_recall"] = author_totals["exact_recovered_spans"] / author_totals["expected_spans"] if author_totals["expected_spans"] else None
    author_totals["exact_span_precision"] = author_totals["exact_recovered_spans"] / author_totals["predicted_spans"] if author_totals["predicted_spans"] else None
    return {"interpretation": "Narrow construction-aware synthetic exact-boundary diagnostics only; NOT human gold, independent accuracy, or diverse-topic generalization. Boundary/attribution differences count as false and missed spans.",
            "totals": totals, "author_renderable_totals": author_totals, "cases": cases}


def run(fixture_path: Path, output_path: Path, *, allow_authenticated_codex: bool,
        batch_size: int = 5) -> dict[str, Any]:
    if not allow_authenticated_codex:
        raise ValueError("Offline authenticated model use requires --allow-authenticated-codex")
    if output_path.exists():
        raise ValueError("Refusing to overwrite previous results; preserve failures and iterations")
    executable = shutil.which("codex")
    if not executable:
        raise RuntimeError("Supported Codex CLI unavailable; no model request was made")
    fixture_bytes = fixture_path.read_bytes()
    fixture = json.loads(fixture_bytes)
    rows = fixture["rows"]
    if fixture.get("frozen_before_first_model_call") is not True or not rows:
        raise ValueError("Freeze nonempty synthetic fixtures before running")
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate fixture IDs")
    # Check synthetic expectations before any model invocation, never feed them to it.
    evaluate(rows, {})
    if not 1 <= batch_size <= 10:
        raise ValueError("Batch size must be 1 to 10")
    prompt_sha = hashlib.sha256(PROMPT.encode()).hexdigest()
    record: dict[str, Any] = {
        "cache_version": CACHE_VERSION, "evidence_source": EVIDENCE_SOURCE,
        "release_approved": False, "calibrated": False, "production_provider": False,
        "scope": "Local opt-in authenticated Codex CLI research on synthetic text only; cached exact-text demonstration, not arbitrary uploaded-article serving",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "fixture_path": str(fixture_path.relative_to(ROOT)) if fixture_path.is_relative_to(ROOT) else fixture_path.name,
        "frozen_fixture": fixture, "prompt": PROMPT, "prompt_sha256": prompt_sha,
        "model": MODEL, "reasoning_effort": "medium", "batch_size": batch_size,
        "batches": [], "entries": {}, "complete": False,
        "valid_model_outputs": 0, "infrastructure_failed": False,
        "semantic_evaluation_status": "pending",
    }
    predictions: dict[str, dict[str, Any]] = {}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    def save() -> None:
        record["evaluation"] = evaluate(rows, predictions)
        record["valid_model_outputs"] = len(predictions)
        if record.get("semantic_evaluation_status") == "not_run_provider_initialization_failed":
            record["evaluation"]["interpretation"] = "No semantic evaluation ran: the CLI runtime failed before any model inference. Coverage counts are infrastructure accounting only; no model-quality conclusion is possible."
            record["evaluation"]["quality_metrics_applicable"] = False
            for section in ("totals", "author_renderable_totals"):
                for metric in ("exact_case_recovery", "exact_span_recall", "exact_span_precision"):
                    record["evaluation"][section][metric] = None
        output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save()  # Freeze prompt + fixture hash + every expected output before the first call.
    for start in range(0, len(rows), batch_size):
        if hashlib.sha256(fixture_path.read_bytes()).hexdigest() != record["fixture_sha256"]:
            raise RuntimeError("Frozen fixture changed while running")
        batch = [{"id": row["id"], "text": row["text"]} for row in rows[start:start + batch_size]]
        attempt: dict[str, Any] = {"ids": [row["id"] for row in batch], "status": "failed", "raw_output": None}
        started = time.monotonic()
        try:
            with tempfile.TemporaryDirectory(prefix="phrase-evidence-") as tmp:
                directory = Path(tmp)
                schema_path, result_path = directory / "schema.json", directory / "result.json"
                schema_path.write_text(json.dumps(model_output_schema()))
                command = [executable, "exec", "--ephemeral", "--skip-git-repo-check", "-C", tmp,
                           "-m", MODEL, "-c", 'model_reasoning_effort="medium"', "-s", "read-only",
                           "--output-schema", str(schema_path), "-o", str(result_path), "-"]
                completed = subprocess.run(command, input=PROMPT + "\nINPUT:\n" + json.dumps(batch, ensure_ascii=False),
                                           text=True, capture_output=True, timeout=600)
                attempt["returncode"] = completed.returncode
                attempt["raw_output"] = result_path.read_text() if result_path.exists() else None
                if completed.returncode or not result_path.exists():
                    attempt["error_log"] = completed.stderr[-10000:]
                    raise RuntimeError("Codex process did not produce a successful response")
                parsed = json.loads(attempt["raw_output"])
                validated = validate_batch(batch, parsed)
                predictions.update(validated)
                for row in batch:
                    digest = text_sha256(row["text"])
                    record["entries"][digest] = {
                        "source_text": row["text"], "source_text_sha256": digest,
                        "provider": "codex_cli_local_research", "model": MODEL,
                        "prompt_sha256": prompt_sha, "extraction_contract": EXTRACTION_CONTRACT,
                        "full_original_context": True, "prediction": validated[row["id"]],
                    }
                attempt["status"] = "validated"
        except (OSError, subprocess.TimeoutExpired, RuntimeError, ValueError, EvidenceValidationError) as exc:
            attempt["error"] = f"{type(exc).__name__}: {exc}"
        attempt["elapsed_seconds"] = round(time.monotonic() - started, 3)
        record["batches"].append(attempt)
        save()
        print(f"Batch {start // batch_size + 1}: {attempt['status']}; {attempt['ids']}", flush=True)
    record["complete"] = True
    initial_failure = all(batch.get("raw_output") is None and
                          "failed to initialize in-process app-server client" in batch.get("error_log", "")
                          for batch in record["batches"])
    record["infrastructure_failed"] = initial_failure
    record["semantic_evaluation_status"] = ("not_run_provider_initialization_failed" if initial_failure
                                            else "completed_synthetic_development_diagnostic" if len(predictions) == len(rows)
                                            else "partial_or_invalid_model_responses")
    record["completed_utc"] = datetime.now(timezone.utc).isoformat()
    save()
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "research/fixtures/phrase_evidence_20261002.json")
    parser.add_argument("--output", type=Path, default=ROOT / "research/results/phrase_evidence_20261002.json")
    parser.add_argument("--allow-authenticated-codex", action="store_true")
    parser.add_argument("--batch-size", type=int, default=5)
    args = parser.parse_args()
    result = run(args.fixtures.resolve(), args.output.resolve(), allow_authenticated_codex=args.allow_authenticated_codex, batch_size=args.batch_size)
    print(json.dumps(result["evaluation"]["totals"], indent=2))
