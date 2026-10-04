import type { SegmentResult } from "./api";

export interface ArticlePart {
  text: string;
  result?: SegmentResult;
}

// Python offsets count Unicode code points. Keep all original spacing and text.
export function buildArticleParts(text: string, results: SegmentResult[]): ArticlePart[] {
  const characters = Array.from(text);
  const parts: ArticlePart[] = [];
  let cursor = 0;
  for (const result of results) {
    if (!Number.isSafeInteger(result.start) || !Number.isSafeInteger(result.end)
      || result.start < cursor || result.end <= result.start || result.end > characters.length
      || characters.slice(result.start, result.end).join("") !== result.text
      || !["LEFT", "CENTER", "RIGHT"].includes(result.label)) {
      return [{ text }];
    }
    if (result.start > cursor) parts.push({ text: characters.slice(cursor, result.start).join("") });
    parts.push({ text: result.text, result });
    cursor = result.end;
  }
  if (cursor < characters.length) parts.push({ text: characters.slice(cursor).join("") });
  return parts;
}
