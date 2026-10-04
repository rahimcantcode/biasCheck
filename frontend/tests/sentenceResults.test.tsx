import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createElement } from 'react';
import { ResultsPanel } from '../components/ResultsPanel';
import { buildArticleParts } from '../lib/article';
import type { PredictResponse, SegmentResult } from '../lib/api';
const { renderToStaticMarkup } = require('react-dom/server');

test('real model response renders sentence counts, tie and directional colors', () => {
  const data = JSON.parse(readFileSync('../docs/sentence-model-smoke.json', 'utf8')).response as PredictResponse;
  const html = renderToStaticMarkup(createElement(ResultsPanel, { data, loading: false, error: null }));
  assert.ok(html.includes('Sentence count breakdown'));
  assert.ok(html.includes('Tie'));
  assert.equal((html.match(/aria-label="Left leaning,/g) ?? []).length, data.summary.counts.LEFT);
  assert.equal((html.match(/aria-label="Right leaning,/g) ?? []).length, data.summary.counts.RIGHT);
  for (const sentence of data.results) assert.ok(html.includes(sentence.text));
});

test('Unicode offsets preserve every character and distinguish repeated sentences', () => {
  const source = '😀 Same.\n\nSame.  ';
  const base = { label: 'LEFT', label_id: 0, probabilities: { LEFT: 0.8, CENTER: 0.1, RIGHT: 0.1 } } as const;
  const results: SegmentResult[] = [
    { ...base, segment_index: 0, start: 0, end: 7, text: '😀 Same.' },
    { ...base, segment_index: 1, start: 9, end: 14, text: 'Same.' },
  ];
  const parts = buildArticleParts(source, results);
  assert.equal(parts.map(part => part.text).join(''), source);
  assert.equal(parts.filter(part => part.result).length, 2);
  assert.deepEqual(buildArticleParts(source, [{ ...results[0], end: 8 }]), [{ text: source }]);
});
