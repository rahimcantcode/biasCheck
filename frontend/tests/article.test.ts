import assert from "node:assert/strict";
import test from "node:test";
import type { EvidenceSpan } from "../lib/api";
import { buildArticleParts } from "../lib/article";

function evidence(text: string, start = 0, label: EvidenceSpan["label"] = "LEFT"): EvidenceSpan {
  return { start, end: start + Array.from(text).length, text, label, attribution: "author", status: "experimental" };
}

test("only the supported expression is highlighted in the user's mixed-clause example", () => {
  const phrase = "taxing the rich is good";
  const text = `my cat is pretty and ${phrase}`;
  const span = evidence(phrase, 21);
  assert.deepEqual(buildArticleParts(text, [span]), [{ text: "my cat is pretty and " }, { text: phrase, evidence: span }]);
});

test("code-point offsets preserve emoji, combining characters, paragraphs, and whitespace", () => {
  const before = "  🐈 My cafe\u0301 is open.\r\n\r\n";
  const phrase = "taxing the rich is good";
  const after = "\n\nEnd.  ";
  const text = before + phrase + after;
  const span = evidence(phrase, Array.from(before).length);
  const parts = buildArticleParts(text, [span]);
  assert.deepEqual(parts, [{ text: before }, { text: phrase, evidence: span }, { text: after }]);
  assert.equal(parts.map(part => part.text).join(""), text);
});

test("repeated phrases use supplied positions rather than first-match searching", () => {
  const phrase = "taxing the rich is good";
  const before = `A critic said “${phrase}”.\nThe author writes: `;
  const text = before + phrase;
  const span = evidence(phrase, Array.from(before).length);
  assert.deepEqual(buildArticleParts(text, [span]), [{ text: before }, { text: phrase, evidence: span }]);
});

test("out-of-order spans are sorted without mutating the response", () => {
  const first = evidence("Left");
  const second = evidence("Right", 9, "RIGHT");
  const input = [second, first];
  const parts = buildArticleParts("Left and Right", input);
  assert.deepEqual(parts, [{ text: "Left", evidence: first }, { text: " and " }, { text: "Right", evidence: second }]);
  assert.deepEqual(input, [second, first]);
});

test("missing, malformed, or empty evidence never manufactures a highlight", () => {
  for (const input of [undefined, null, {}, "LEFT", [], [null], [42], ["tax the rich"]]) {
    assert.deepEqual(buildArticleParts("tax the rich", input), [{ text: "tax the rich" }]);
  }
  assert.deepEqual(buildArticleParts("", []), []);
});

test("segment-like objects cannot masquerade as phrase evidence", () => {
  const span = evidence("tax the rich");
  const { attribution: _attribution, status: _status, ...segment } = span;
  assert.deepEqual(buildArticleParts(span.text, [{ ...segment, decision: "classified" }]), [{ text: span.text }]);
});

test("invalid offsets, text, labels, attribution, or status fail closed", () => {
  const span = evidence("tax the rich");
  const invalid = [
    { start: -1 }, { start: 0.5 }, { start: "0" }, { start: null },
    { end: NaN }, { end: Infinity }, { end: 0 }, { end: 100 }, { end: 3 },
    { text: "Tax the rich" }, { text: "" }, { text: null },
    { label: "CENTER" }, { label: "left" }, { attribution: "speaker" },
    { status: "validated" }, { status: undefined }, { rationale: {} },
  ];
  for (const change of invalid) {
    assert.deepEqual(buildArticleParts(span.text, [{ ...span, ...change }]), [{ text: span.text }], JSON.stringify(change));
  }
  assert.deepEqual(buildArticleParts(" \n ", [evidence(" \n ")]), [{ text: " \n " }]);
});

test("wrong UTF-16 offsets after an emoji fail closed instead of shifting the highlight", () => {
  const text = "🐈 tax the rich";
  assert.deepEqual(buildArticleParts(text, [evidence("tax the rich", 3)]), [{ text }]);
});

test("quoted and unknown attribution remain plain", () => {
  for (const attribution of ["quoted", "unknown"] as const) {
    const span = { ...evidence("tax the rich"), attribution };
    assert.deepEqual(buildArticleParts(span.text, [span]), [{ text: span.text }]);
  }
});

test("every member of a transitive overlap group is rejected; unrelated evidence survives", () => {
  const text = "abcdefghij";
  const spans = [evidence("abcd"), evidence("def", 3), evidence("fgh", 5), evidence("ij", 8, "RIGHT")];
  assert.deepEqual(buildArticleParts(text, spans), [{ text: "abcdefgh" }, { text: "ij", evidence: spans[3] }]);
});

test("duplicate spans and author/quote conflicts both fail closed", () => {
  const span = evidence("tax the rich");
  for (const second of [span, { ...span, label: "RIGHT" }, { ...span, attribution: "quoted" }, { ...span, attribution: "unknown" }]) {
    assert.deepEqual(buildArticleParts(span.text, [span, second]), [{ text: span.text }]);
  }
});

test("adjacent non-overlapping spans are preserved", () => {
  const left = evidence("Left");
  const right = evidence("Right", 4, "RIGHT");
  assert.deepEqual(buildArticleParts("LeftRight", [left, right]), [{ text: "Left", evidence: left }, { text: "Right", evidence: right }]);
});

test("a malformed entry does not suppress separate correctly matched evidence", () => {
  const span = evidence("tax the rich");
  assert.deepEqual(buildArticleParts(span.text, [{ ...span, text: "wrong" }, span]), [{ text: span.text, evidence: span }]);
});
