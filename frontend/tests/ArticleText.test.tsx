import assert from "node:assert/strict";
import test from "node:test";
import type { ComponentProps, ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { ArticleText } from "../components/ArticleText";
import { ResultsPanel } from "../components/ResultsPanel";
import type { EvidenceSpan, Mode, PredictResponse, PredictionResult } from "../lib/api";
import { buildArticleParts } from "../lib/article";

const phrase = "taxing the rich is good";
const original = `my cat is pretty and ${phrase}`;
const evidence: EvidenceSpan = { start: 21, end: Array.from(original).length, text: phrase, label: "LEFT", attribution: "author", status: "experimental" };

function render(text = original, spans: unknown = [evidence], showHighlights = true) {
  return renderToStaticMarkup(<ArticleText parts={buildArticleParts(text, spans)} showHighlights={showHighlights} selected={null} onSelect={() => {}} />);
}

function marks(html: string) {
  return [...html.matchAll(/<mark\b[^>]*>([\s\S]*?)<\/mark>/g)];
}

test("mixed-clause rendering highlights only the expression in blue", () => {
  const html = render();
  assert.match(html, /<span>my cat is pretty and <\/span>/);
  assert.equal(marks(html).length, 1);
  assert.equal(marks(html)[0][1], phrase);
  assert.match(marks(html)[0][0], /bg-blue-500\/20 text-blue-200/);
  assert.match(html, /Experimental Left-leaning expression attributed to the author/);
  assert.match(html, /tabindex="0"/);
  assert.match(html, /role="button"/);
  assert.match(html, /whitespace-pre-wrap/);
});

test("right evidence renders red and supplies a text label beyond color", () => {
  const html = render(original, [{ ...evidence, label: "RIGHT" }]);
  assert.match(marks(html)[0][0], /bg-red-500\/20 text-red-200/);
  assert.match(html, /Experimental Right-leaning expression attributed to the author/);
  assert.match(marks(html)[0][0], /decoration-double/);
});

test("turning off highlights returns a plain reading view with identical text", () => {
  const html = render(original, [evidence], false);
  assert.equal(marks(html).length, 0);
  assert.equal(html.replace(/<[^>]+>/g, ""), original);
  assert.doesNotMatch(html, /role="button"|tabindex=/);
});

test("article content and annotation attributes are escaped rather than injected as HTML", () => {
  const malicious = '<img src=x onerror="alert(1)"> & <script>alert(2)</script>';
  const span = { ...evidence, start: 0, end: Array.from(malicious).length, text: malicious };
  const html = render(malicious, [span]);
  assert.doesNotMatch(html, /<img|<script/);
  assert.match(html, /&lt;img/);
  assert.match(html, /&amp;/);
  assert.match(html, /&lt;script&gt;/);
});

test("quoted, unknown, malformed, and missing evidence render no interactive marks", () => {
  for (const spans of [undefined, [], [{ ...evidence, attribution: "quoted" }], [{ ...evidence, attribution: "unknown" }], [{ ...evidence, text: "mismatch" }]]) {
    const html = render(original, spans ?? []);
    assert.equal(marks(html).length, 0);
    assert.equal(html.replace(/<[^>]+>/g, ""), original);
  }
});

test("phrase selection supports click, Enter, Space, Escape, and toggling off", () => {
  let selected: EvidenceSpan | null = null;
  const onSelect = (span: EvidenceSpan | null) => { selected = span; };
  const getMark = (active: EvidenceSpan | null) => {
    const view = ArticleText({ parts: buildArticleParts(original, [evidence]), showHighlights: true, selected: active, onSelect });
    return (view.props.children as ReactElement<ComponentProps<"mark">>[]).find(child => child.type === "mark")!;
  };
  const mark = getMark(null);
  mark.props.onClick!({} as never);
  assert.equal(selected, evidence);
  const activeMark = getMark(evidence);
  assert.equal(activeMark.props["aria-pressed"], true);
  activeMark.props.onClick!({} as never);
  assert.equal(selected, null);
  for (const key of ["Enter", " "]) {
    let prevented = false;
    mark.props.onKeyDown!({ key, preventDefault: () => { prevented = true; } } as never);
    assert.equal(selected, evidence);
    assert.equal(prevented, true);
    mark.props.onKeyDown!({ key: "Escape" } as never);
    assert.equal(selected, null);
  }
});

const prediction: PredictionResult = {
  label: "LEFT", label_id: 0, raw_label: "LEFT", decision: "classified", reason: "demo_estimate",
  token_count: 12, tokens_processed: 12, chunk_count: 1, truncated: false, calibrated: false,
  probabilities: { LEFT: 0.8, RIGHT: 0.1, CENTER: 0.1 },
};

function response(mode: Mode, spans?: EvidenceSpan[]): PredictResponse {
  return {
    overall: prediction, warnings: [], model: { weights_sha256: "test", aggregation: "test" },
    source_type: "text", resolved_text: original, mode, evidence_spans: spans,
    evidence_status: spans ? "available" : "unavailable", evidence_metadata: { offset_unit: "unicode_code_point" },
    results: [{ ...prediction, segment_index: 0, text: original, start: 0, end: original.length }],
  };
}

test("article, sentence, and paragraph modes all render only supplied phrase evidence", () => {
  for (const mode of ["article", "sentence", "paragraph"] as const) {
    const html = renderToStaticMarkup(<ResultsPanel data={response(mode, [evidence])} loading={false} error={null} />);
    assert.equal(marks(html).length, 1, mode);
    assert.equal(marks(html)[0][1], phrase, mode);
    assert.match(html, /Experimental phrase annotations/);
  }
});

test("an overall or sentence label alone never colors the original article", () => {
  for (const mode of ["article", "sentence", "paragraph"] as const) {
    const html = renderToStaticMarkup(<ResultsPanel data={response(mode)} loading={false} error={null} />);
    assert.equal(marks(html).length, 0, mode);
    assert.match(html, /No supported phrase-level evidence is available/);
    assert.match(html, /Unhighlighted text does not establish neutrality/);
    assert.match(html, /disabled=""/);
  }
});

test("unavailable, invalid, missing, and wrong-offset-unit envelopes fail closed", () => {
  const data = response("article", [evidence]);
  const invalidResponses: PredictResponse[] = [
    { ...data, evidence_status: "unavailable" },
    { ...data, evidence_status: "invalid" },
    { ...data, evidence_status: undefined },
    { ...data, evidence_metadata: undefined },
    { ...data, evidence_metadata: { offset_unit: "utf16" } } as unknown as PredictResponse,
  ];
  for (const invalid of invalidResponses) {
    const html = renderToStaticMarkup(<ResultsPanel data={invalid} loading={false} error={null} />);
    assert.equal(marks(html).length, 0);
    assert.match(html, /Phrase analysis is unavailable/);
  }
});

test("valid phrase analysis with no author spans distinguishes absence from unavailability", () => {
  const html = renderToStaticMarkup(<ResultsPanel data={response("article", [{ ...evidence, attribution: "quoted" }])} loading={false} error={null} />);
  assert.equal(marks(html).length, 0);
  assert.match(html, /No supported author expressions are available to highlight/);
  assert.doesNotMatch(html, /Phrase analysis is unavailable/);
});

test("the loading and error states do not expose stale article highlights", () => {
  const data = response("article", [evidence]);
  const loading = renderToStaticMarkup(<ResultsPanel data={data} loading error={null} />);
  const error = renderToStaticMarkup(<ResultsPanel data={data} loading={false} error="Failed" />);
  assert.equal(marks(loading).length, 0);
  assert.equal(marks(error).length, 0);
  assert.doesNotMatch(loading + error, /my cat is pretty/);
});
