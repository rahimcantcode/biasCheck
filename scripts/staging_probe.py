#!/usr/bin/env python3
"""Opt-in, bounded HTTP contract smoke probe. This does not measure accuracy.

Default: GET /health only. --run-predictions adds at most four sequential POSTs
(article, sentence, paragraph, empty-input rejection) with synthetic plain text.
No URLs are submitted for extraction, no retries/concurrency, no credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_RESPONSE_BYTES = 2_000_000
LABELS = {"LEFT", "RIGHT", "CENTER"}
SOURCE = (
    "  Café log 𝟙:\tThe library opens at nine and closes at six on weekdays.\r\n\r\n"
    "The recipe asks the cook to stir the vegetables before adding water.  "
)
LONG_SOURCE = "  Café catalog 𝟙:\t\r\n" + "\r\n".join(
    f"Entry {i}: The library catalog lists opening times and shelf locations. "
    "Readers may return borrowed books at the desk and find the next volume "
    "using the index printed inside the cover."
    for i in range(1, 25)
) + "  "


class ProbeError(ValueError):
    pass


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if (any(char.isspace() for char in value)
            or parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment):
        raise ProbeError("Use an explicit HTTP(S) API base URL without credentials, query, or fragment")
    try:
        parsed.port
    except ValueError as exc:
        raise ProbeError("Invalid port") from exc
    return value.rstrip("/")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProbeError("Response contains duplicate JSON keys")
        result[key] = value
    return result


def _invalid_number(value):
    raise ProbeError("Response contains a non-finite JSON number")


def _finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        _invalid_number(value)
    return result


def http_json(url: str, payload: dict | None, timeout: float) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=body, headers={
        "Accept": "application/json", "Content-Type": "application/json",
        "User-Agent": "BiasCheckStagingContractProbe/1",
    })
    try:
        response = build_opener(NoRedirects()).open(request, timeout=timeout)
    except HTTPError as exc:
        response = exc
    with response:
        status = response.status
        if 300 <= status < 400:
            raise ProbeError("Redirect refused; use the final API base URL explicitly")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ProbeError("Response exceeds the 2 MB probe limit")
        if "application/json" not in response.headers.get("Content-Type", "").lower():
            raise ProbeError("Expected an application/json response")
    result = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                        parse_constant=_invalid_number, parse_float=_finite_float)
    if not isinstance(result, dict):
        raise ProbeError("Expected a JSON object")
    return status, result


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProbeError(message)


def check_health(status: int, data: dict, expected_release: str) -> None:
    _require(status == 200 and data.get("status") == "ok", "Health is not HTTP 200 / ok")
    _require(type(data.get("release_approved")) is bool, "Health lacks a boolean release state")
    _require(isinstance(data.get("model"), dict), "Health lacks model metadata")
    if expected_release != "any":
        _require(data["release_approved"] == (expected_release == "approved"),
                 "Unexpected release approval state")


def check_result(item: dict) -> None:
    _require(isinstance(item, dict), "Prediction must be an object")
    for key in ("token_count", "tokens_processed", "chunk_count"):
        _require(type(item.get(key)) is int and item[key] > 0, f"Invalid {key}")
    _require(item["tokens_processed"] == item["token_count"], "Token coverage is incomplete")
    _require(item.get("truncated") is False, "Prediction is truncated or lacks coverage metadata")
    _require(type(item.get("calibrated")) is bool, "Missing calibration flag")
    _require(item.get("decision") in {"classified", "abstained"}, "Invalid decision")
    if item["decision"] == "abstained":
        _require(item.get("label") is None and item.get("label_id") is None,
                 "Abstained result exposes a final label")
    else:
        _require(item.get("label") in LABELS and type(item.get("label_id")) is int,
                 "Classified result lacks a label")
    scores = item.get("probabilities")
    _require(item.get("score_type") in {"class_probability", "independent_entailment"}, "Unknown score type")
    _require(isinstance(scores, dict) and set(scores) == LABELS, "Invalid score classes")
    _require(all(type(x) in {float, int} and math.isfinite(x) and 0 <= x <= 1
                 for x in scores.values()), "Scores must be finite numbers from zero to one")
    if item.get("score_type") == "class_probability":
        _require(abs(sum(scores.values()) - 1) <= 0.00001, "Class probabilities do not sum to one")


def check_prediction(status: int, data: dict, source: str, mode: str, health: dict,
                     expected_evidence: str = "unavailable") -> None:
    _require(status == 200, f"Prediction returned HTTP {status}")
    _require(data.get("source_type") == "text" and data.get("mode") == mode,
             "Source type or mode changed")
    _require(data.get("resolved_text") == source, "Pasted source text was rewritten")
    check_result(data.get("overall"))
    _require(isinstance(data.get("model"), dict), "Missing prediction model metadata")
    for key in ("weights_sha256", "config_sha256", "tokenizer_sha256", "aggregation", "engine", "demo_mode"):
        if key in health["model"]:
            _require(data["model"].get(key) == health["model"][key], f"Model identity changed: {key}")
    segments = data.get("results")
    _require(isinstance(segments, list) and bool(segments), "Missing segments")
    cursor = 0
    for index, item in enumerate(segments):
        check_result(item)
        start, end = item.get("start"), item.get("end")
        _require(type(start) is int and type(end) is int and cursor <= start < end <= len(source),
                 "Invalid or overlapping segment offsets")
        _require(not source[cursor:start].strip(), "Non-whitespace source text omitted between segments")
        _require(item.get("text") == source[start:end], "Segment text differs from source slice")
        _require(item.get("segment_index") == index, "Segment indices are not sequential")
        cursor = end
    _require(not source[cursor:].strip(), "Non-whitespace source tail omitted")
    if mode == "article":
        _require(len(segments) == 1 and segments[0]["start"] == 0 and segments[0]["end"] == len(source),
                 "Article mode does not cover the entire source")
    _require(isinstance(data.get("warnings"), list), "Missing warnings")
    if health["release_approved"] is False:
        _require(bool(data["warnings"]), "Unapproved release lacks experimental warning")
    evidence_status = data.get("evidence_status")
    _require(evidence_status in {"available", "unavailable", "invalid"}, "Missing phrase evidence contract")
    if expected_evidence != "any":
        _require(evidence_status == expected_evidence, "Unexpected phrase evidence status")
    spans = data.get("evidence_spans")
    _require(isinstance(spans, list), "Missing evidence span list")
    _require(evidence_status == "available" or not spans, "Unavailable/invalid evidence returned highlights")
    cursor = 0
    for span in spans:
        _require(isinstance(span, dict), "Evidence span must be an object")
        start, end = span.get("start"), span.get("end")
        _require(type(start) is int and type(end) is int and cursor <= start < end <= len(source),
                 "Invalid or overlapping evidence offsets")
        _require(span.get("text") == source[start:end], "Evidence text differs from source slice")
        _require(span.get("label") in {"LEFT", "RIGHT"}, "Invalid evidence direction")
        _require(span.get("attribution") in {"author", "quoted", "unknown"}, "Invalid evidence attribution")
        _require(span.get("status") == "experimental", "Missing experimental evidence status")
        cursor = end
    if evidence_status == "available":
        metadata = data.get("evidence_metadata", {})
        _require(metadata.get("source_text_sha256") == hashlib.sha256(source.encode("utf-8")).hexdigest(),
                 "Evidence source hash does not match the exact source")
        _require(metadata.get("offset_unit") == "unicode_code_point", "Unknown evidence coordinate system")


def run_probe(base_url: str, *, run_predictions: bool = False, timeout: float = 30,
              total_timeout: float = 120, expected_release: str = "unapproved",
              expected_evidence: str = "unavailable", transport=http_json) -> dict[str, Any]:
    base_url = validate_base_url(base_url)
    _require(0 < timeout <= 60 and 0 < total_timeout <= 300, "Timeout exceeds probe limits")
    _require(expected_release in {"approved", "unapproved", "any"}, "Invalid expected release state")
    _require(expected_evidence in {"available", "unavailable", "invalid", "any"}, "Invalid evidence expectation")
    started = time.monotonic()
    checks = []
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "api_base_url": base_url,
              "purpose": "synthetic HTTP contract smoke, not accuracy or load evaluation",
              "prediction_requests_enabled": run_predictions, "checks": checks}

    def request(path, payload=None):
        remaining = total_timeout - (time.monotonic() - started)
        _require(remaining > 0, "Total probe deadline reached")
        return transport(base_url + path, payload, min(timeout, remaining))

    try:
        status, health = request("/health")
        check_health(status, health, expected_release)
        checks.append({"name": "health", "passed": True, "release_approved": health["release_approved"],
                       "model": {k: v for k, v in health["model"].items() if k in
                                 {"weights_sha256", "aggregation", "engine", "demo_mode", "torch", "transformers"}}})
    except Exception as exc:
        checks.append({"name": "health", "passed": False, "error": str(exc)})
        report["passed"] = False
        return report
    if run_predictions:
        for mode in ("article", "sentence", "paragraph", "invalid_empty"):
            before = time.monotonic()
            source = LONG_SOURCE if mode == "article" else SOURCE
            payload = {"input": "   " if mode == "invalid_empty" else source,
                       "mode": "article" if mode == "invalid_empty" else mode}
            check = {"name": mode}
            try:
                status, data = request("/predict", payload)
                check["http_status"] = status
                if mode == "invalid_empty":
                    _require(status in {400, 422} and isinstance(data.get("detail"), (str, list)),
                             "Empty input did not return a controlled validation error")
                else:
                    # Preserve diagnostic facts even when a later contract check fails.
                    check["source_preserved"] = data.get("resolved_text") == source
                    check["evidence_contract_present"] = "evidence_status" in data and "evidence_spans" in data
                    check_prediction(status, data, source, mode, health, expected_evidence)
                    if mode == "article":
                        _require(data["overall"]["chunk_count"] >= 2, "Long control did not exercise multiple windows")
                    check.update({"tokens": data["overall"]["token_count"],
                                  "chunks": data["overall"]["chunk_count"],
                                  "decision": data["overall"]["decision"],
                                  "evidence_status": data["evidence_status"]})
                check["passed"] = True
            except Exception as exc:
                check.update({"passed": False, "error": str(exc)})
            check["elapsed_seconds"] = round(time.monotonic() - before, 3)
            checks.append(check)
    report["passed"] = all(x["passed"] for x in checks)
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="API base, e.g. http://127.0.0.1:8000 or https://staging.example/api")
    parser.add_argument("--run-predictions", action="store_true", help="Opt in to four bounded sequential synthetic POST requests")
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--total-timeout", type=float, default=120,
                        help="Budget checked before each request; socket timeout is an idle limit, not a hard wall-clock kill")
    parser.add_argument("--expect-release", choices=("unapproved", "approved", "any"), default="unapproved")
    parser.add_argument("--expect-evidence", choices=("available", "unavailable", "invalid", "any"), default="unavailable")
    parser.add_argument("--output", type=Path, help="Optional local JSON report path")
    args = parser.parse_args()
    try:
        report = run_probe(args.base_url, run_predictions=args.run_predictions, timeout=args.timeout,
                           total_timeout=args.total_timeout, expected_release=args.expect_release,
                           expected_evidence=args.expect_evidence)
    except ProbeError as exc:
        parser.error(str(exc))
    result = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    print(result, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
