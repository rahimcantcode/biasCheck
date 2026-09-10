import type { Label, PredictionProbabilities, SegmentResult } from "./api";

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
    const start = text.indexOf(result.text, cursor);
    if (start < 0) continue;
    if (start > cursor) parts.push({ text: text.slice(cursor, start) });
    parts.push({ text: result.text, result });
    cursor = start + result.text.length;
  }

  if (cursor < text.length) parts.push({ text: text.slice(cursor) });
  return parts;
}

export function summarizeArticle(results: SegmentResult[]) {
  const probabilities: PredictionProbabilities = { LEFT: 0, CENTER: 0, RIGHT: 0 };
  const labels: Label[] = ["LEFT", "CENTER", "RIGHT"];
  let totalWords = 0;

  for (const result of results) {
    const words = result.text.trim().split(/\s+/).filter(Boolean).length;
    totalWords += words;
    for (const label of labels) probabilities[label] += result.probabilities[label] * words;
  }

  if (!totalWords) return null;
  for (const label of labels) probabilities[label] /= totalWords;
  const ranked = [...labels].sort((a, b) => probabilities[b] - probabilities[a]);
  const label = Math.abs(probabilities[ranked[0]] - probabilities[ranked[1]]) < 0.000001
    ? null
    : ranked[0];
  return { label, probabilities, totalWords };
}
