"""Fake and loopback HTTP contract checks for the opt-in staging probe."""
from copy import deepcopy
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from scripts.staging_probe import (
    LONG_SOURCE, SOURCE, ProbeError, check_prediction, http_json, run_probe, validate_base_url,
)

HEALTH = {"status": "ok", "release_approved": False, "model": {"weights_sha256": "synthetic"}}


def prediction(source, mode):
    result = {"token_count": 800, "tokens_processed": 800, "chunk_count": 2,
              "truncated": False, "calibrated": False, "decision": "abstained",
              "label": None, "label_id": None, "raw_label": "CENTER",
              "score_type": "class_probability", "reason": "model_not_validated",
              "probabilities": {"LEFT": 0.2, "RIGHT": 0.2, "CENTER": 0.6}}
    return {"source_type": "text", "resolved_text": source, "mode": mode,
            "overall": result, "results": [{**result, "segment_index": 0,
                                              "start": 0, "end": len(source), "text": source}],
            "warnings": ["Experimental synthetic fixture"], "model": dict(HEALTH["model"]),
            "evidence_status": "unavailable", "evidence_spans": [], "evidence_metadata": {}}


class FakeTransport:
    def __init__(self):
        self.calls = []

    def __call__(self, url, payload, timeout):
        self.calls.append((url, payload, timeout))
        if payload is None:
            return 200, deepcopy(HEALTH)
        if not payload["input"].strip():
            return 400, {"detail": "Please provide article text"}
        return 200, prediction(payload["input"], payload["mode"])


def test_default_is_health_only_and_posts_are_explicit_and_bounded():
    transport = FakeTransport()
    report = run_probe("http://127.0.0.1:8000", transport=transport)
    assert report["passed"] and len(transport.calls) == 1
    assert transport.calls[0][1] is None
    transport = FakeTransport()
    report = run_probe("http://127.0.0.1:8000", run_predictions=True, transport=transport)
    assert report["passed"] and len(transport.calls) == 5
    assert [check["name"] for check in report["checks"]] == ["health", "article", "sentence", "paragraph", "invalid_empty"]
    assert transport.calls[1][1]["input"] == LONG_SOURCE
    assert all(0 < call[2] <= 30 for call in transport.calls)


@pytest.mark.parametrize("url", ["file:///tmp/test", "https://user:secret@example.com", "https://example.com?token=x",
                                     "https://example.com#fragment", "https://example.com:bad", "//example.com"])
def test_ambiguous_or_credential_urls_rejected(url):
    with pytest.raises(ProbeError):
        validate_base_url(url)


@pytest.mark.parametrize("field,value", [("token_count", True), ("tokens_processed", 799),
                                           ("chunk_count", 0), ("truncated", True),
                                           ("label", "LEFT"), ("calibrated", None)])
def test_coverage_and_abstention_contract_is_enforced(field, value):
    data = prediction(SOURCE, "article")
    data["overall"][field] = value
    with pytest.raises(ProbeError):
        check_prediction(200, data, SOURCE, "article", HEALTH)


def test_source_whitespace_and_unicode_are_not_normalized_away():
    data = prediction(SOURCE, "article")
    check_prediction(200, data, SOURCE, "article", HEALTH)
    data["resolved_text"] = SOURCE.strip()
    with pytest.raises(ProbeError, match="rewritten"):
        check_prediction(200, data, SOURCE, "article", HEALTH)


def test_omitted_source_and_changed_identity_fail():
    data = prediction(SOURCE, "paragraph")
    data["results"][0].update(start=10, text=SOURCE[10:])
    with pytest.raises(ProbeError, match="omitted"):
        check_prediction(200, data, SOURCE, "paragraph", HEALTH)
    data = prediction(SOURCE, "article")
    data["model"]["weights_sha256"] = "different"
    with pytest.raises(ProbeError, match="identity"):
        check_prediction(200, data, SOURCE, "article", HEALTH)


def test_highlights_require_exact_source_and_evidence_status():
    data = prediction(SOURCE, "article")
    start = SOURCE.index("library")
    data.update(evidence_status="available", evidence_spans=[{
        "start": start, "end": start + 7, "text": "library", "label": "LEFT",
        "attribution": "unknown", "status": "experimental"}], evidence_metadata={
            "source_text_sha256": hashlib.sha256(SOURCE.encode()).hexdigest(), "offset_unit": "unicode_code_point"})
    # Arbitrary direction is deliberately accepted: this is a contract fixture, not accuracy gold.
    check_prediction(200, data, SOURCE, "article", HEALTH, "available")
    with pytest.raises(ProbeError, match="status"):
        check_prediction(200, data, SOURCE, "article", HEALTH)
    data["evidence_spans"][0]["text"] = "Library"
    with pytest.raises(ProbeError, match="source slice"):
        check_prediction(200, data, SOURCE, "article", HEALTH, "available")


def test_legacy_api_and_nonfinite_scores_fail():
    data = prediction(SOURCE, "article")
    data.pop("evidence_status")
    with pytest.raises(ProbeError, match="evidence contract"):
        check_prediction(200, data, SOURCE, "article", HEALTH)
    data = prediction(SOURCE, "article")
    data["overall"]["probabilities"]["LEFT"] = float("nan")
    with pytest.raises(ProbeError, match="finite"):
        check_prediction(200, data, SOURCE, "article", HEALTH)


def test_health_failure_prevents_all_prediction_requests():
    calls = []
    def broken(url, payload, timeout):
        calls.append(url)
        return 200, {**HEALTH, "release_approved": True}
    report = run_probe("https://staging.example/api", run_predictions=True, transport=broken)
    assert not report["passed"] and len(calls) == 1
    assert "approval" in report["checks"][0]["error"]


def test_controlled_error_must_be_rejected_instead_of_classified():
    transport = FakeTransport()
    def accepting(url, payload, timeout):
        if payload is not None and not payload["input"].strip():
            return 200, {"detail": "bad fixture"}
        return transport(url, payload, timeout)
    report = run_probe("http://127.0.0.1:8000", run_predictions=True, transport=accepting)
    assert not report["passed"]
    assert report["checks"][-1]["http_status"] == 200


@pytest.mark.parametrize("settings", [{"timeout": 0}, {"timeout": 61}, {"total_timeout": 301},
                                       {"expected_release": "yes"}, {"expected_evidence": "yes"}])
def test_invalid_probe_limits_fail_before_network(settings):
    transport = FakeTransport()
    with pytest.raises(ProbeError):
        run_probe("http://127.0.0.1:8000", transport=transport, **settings)
    assert not transport.calls


@pytest.fixture
def synthetic_http():
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            status, content_type, body = {
                "/ok": (200, "application/json", b'{"status":"ok"}'),
                "/error": (400, "application/json", b'{"detail":"invalid input"}'),
                "/redirect": (302, "application/json", b'{}'),
                "/duplicate": (200, "application/json", b'{"x":1,"x":2}'),
                "/overflow": (200, "application/json", b'{"x":1e999}'),
                "/nonjson": (200, "text/html", b'<p>upstream error</p>'),
                "/large": (200, "application/json", b' ' * 2_000_001),
            }[self.path]
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            if status == 302:
                self.send_header("Location", "/ok")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_transport_keeps_controlled_error_body(synthetic_http):
    base, _ = synthetic_http
    assert http_json(base + "/ok", None, 2) == (200, {"status": "ok"})
    assert http_json(base + "/error", None, 2) == (400, {"detail": "invalid input"})


@pytest.mark.parametrize("path,message", [("redirect", "Redirect refused"), ("duplicate", "duplicate"),
                                          ("overflow", "non-finite"), ("nonjson", "application/json"),
                                          ("large", "2 MB")])
def test_transport_rejects_redirects_and_unsafe_responses(synthetic_http, path, message):
    base, requests = synthetic_http
    with pytest.raises(ProbeError, match=message):
        http_json(base + "/" + path, None, 2)
    assert requests == ["/" + path]
