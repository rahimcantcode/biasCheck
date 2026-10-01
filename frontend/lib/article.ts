import type { SegmentResult } from "./api";

export interface ArticlePart {
  text: string;
  result?: SegmentResult;
}

// Match in reading order so repeated sentences stay in their original positions.
// Keep every character of the resolved article, including unclassified whitespace.
export function buildArticleParts(text: string, results: SegmentResult[]): ArticlePart[] {
  const parts: ArticlePart[] = [];
  let cursor = 0;

  for (const result of results) {
    if (!result.text) continue;
    const start = result.start;
    if (start < cursor || result.end > text.length || text.slice(start, result.end) !== result.text) continue;
    if (start > cursor) parts.push({ text: text.slice(cursor, start) });
    parts.push({ text: result.text, result });
    cursor = start + result.text.length;
  }

  if (cursor < text.length) parts.push({ text: text.slice(cursor) });
  return parts;
}
