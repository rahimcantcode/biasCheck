import type { EvidenceSpan } from "./api";

export interface ArticlePart {
  text: string;
  evidence?: EvidenceSpan;
}

function validEvidence(value: unknown, characters: string[]): value is EvidenceSpan {
  if (!value || typeof value !== "object") return false;
  const span = value as Partial<EvidenceSpan>;
  return (
    Number.isSafeInteger(span.start) &&
    Number.isSafeInteger(span.end) &&
    span.start! >= 0 &&
    span.end! > span.start! &&
    span.end! <= characters.length &&
    typeof span.text === "string" &&
    span.text.trim().length > 0 &&
    characters.slice(span.start, span.end).join("") === span.text &&
    (span.label === "LEFT" || span.label === "RIGHT") &&
    (span.attribution === "author" || span.attribution === "quoted" || span.attribution === "unknown") &&
    span.status === "experimental" &&
    (span.rationale === undefined || typeof span.rationale === "string")
  );
}

/**
 * Preserve every character, including paragraph breaks, while annotating only
 * exact, non-overlapping author evidence supplied by the server. Never derive a
 * phrase from a keyword, a segment prediction, or the document's overall label.
 *
 * API offsets count Unicode code points (as Python does), not JS UTF-16 units.
 * Invalid entries fail closed. Every member of an overlapping group is dropped,
 * including an author span that conflicts with quoted/unknown attribution.
 */
export function buildArticleParts(text: string, evidence: unknown): ArticlePart[] {
  const characters = Array.from(text);
  const candidates = (Array.isArray(evidence) ? evidence : [])
    .filter((span): span is EvidenceSpan => validEvidence(span, characters))
    .sort((a, b) => a.start - b.start || a.end - b.end);
  const accepted: EvidenceSpan[] = [];

  for (let index = 0; index < candidates.length;) {
    const first = candidates[index];
    let next = index + 1;
    let groupEnd = first.end;
    while (next < candidates.length && candidates[next].start < groupEnd) {
      groupEnd = Math.max(groupEnd, candidates[next].end);
      next += 1;
    }
    if (next === index + 1 && first.attribution === "author") accepted.push(first);
    index = next;
  }

  const parts: ArticlePart[] = [];
  let cursor = 0;
  for (const span of accepted) {
    if (span.start > cursor) parts.push({ text: characters.slice(cursor, span.start).join("") });
    parts.push({ text: characters.slice(span.start, span.end).join(""), evidence: span });
    cursor = span.end;
  }
  if (cursor < characters.length) parts.push({ text: characters.slice(cursor).join("") });
  return parts;
}
