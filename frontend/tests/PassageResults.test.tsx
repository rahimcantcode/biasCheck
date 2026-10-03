import assert from "node:assert/strict";
import test from "node:test";
import { renderToStaticMarkup } from "react-dom/server";
import { ResultsPanel } from "../components/ResultsPanel";
import type { Mode, PredictResponse, PredictionResult } from "../lib/api";

function response(mode: Mode, overrides: Partial<PredictionResult> = {}): PredictResponse {
  const text = "A synthetic passage with an experimental estimate.";
  const result: PredictionResult = {
    label: "LEFT", label_id: 0, raw_label: "LEFT", decision: "classified", reason: "demo_estimate",
    score_type: "class_probability", probabilities: { LEFT: 0.9, CENTER: 0.06, RIGHT: 0.04 },
    token_count: 12, tokens_processed: 12, chunk_count: 1, truncated: false, calibrated: false,
    ...overrides,
  };
  return { source_type: "text", resolved_text: text, mode, overall: result,
    results: [{ ...result, segment_index: 0, text, start: 0, end: text.length }],
    warnings: ["Experimental estimate"], model: { weights_sha256: "synthetic", aggregation: "synthetic" },
    evidence_status: "unavailable", evidence_spans: [], evidence_metadata: {},
  };
}

function render(data: PredictResponse) {
  return renderToStaticMarkup(<ResultsPanel data={data} loading={false} error={null} />);
}

test("RoBERTa sentence and paragraph modes expose computed estimates without creating phrase highlights", () => {
  for (const mode of ["sentence", "paragraph"] as const) {
    const html = render(response(mode));
    assert.match(html, /Inspect experimental passage estimates/);
    assert.match(html, /Experimental Left estimate/);
    assert.match(html, /Uncalibrated model support/);
    assert.match(html, /not probabilities of correctness/);
    assert.doesNotMatch(html, /<mark\b/);
  }
});

test("abstained passage does not present raw class as an assigned label", () => {
  const html = render(response("sentence", { decision: "abstained", label: null, label_id: null,
    raw_label: "RIGHT", reason: "model_not_validated" }));
  assert.match(html, /No reliable label/);
  assert.match(html, /Final label withheld/);
  assert.match(html, /has not passed independent validation/);
  assert.doesNotMatch(html, /Experimental Right estimate|Experimental Left estimate/);
});

test("short and uncertain passages explain the abstention", () => {
  for (const [reason, title] of [["insufficient_context", "More context needed"], ["uncertain", "Uncertain"]]) {
    const html = render(response("paragraph", { decision: "abstained", label: null, label_id: null, reason }));
    assert.ok(html.includes(title));
    assert.match(html, /Final label withheld/);
  }
});

test("independent entailment remains tentative and is distinguished from class scores", () => {
  const html = render(response("paragraph", { decision: "abstained", label: null, label_id: null,
    tentative_label: "RIGHT", reason: "experimental_model_not_validated", score_type: "independent_entailment",
    probabilities: { LEFT: 0.8, CENTER: 0.2, RIGHT: 0.9 } }));
  assert.match(html, /Tentative Right/);
  assert.match(html, /Independent model support/);
  assert.match(html, /Final label withheld/);
  assert.doesNotMatch(html, /Uncalibrated model support/);
});

test("article mode does not duplicate its overall result as a passage panel", () => {
  const html = render(response("article"));
  assert.doesNotMatch(html, /Inspect experimental passage estimates/);
});
