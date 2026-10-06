const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../research/scripts/live_browser_audit.cjs'), 'utf8');

async function simulate(failure, mode = 'article', input = {}) {
  const writes = [];
  const buttons = [];
  let waits = 0, closed = false;
  const status = failure === 'json' ? 502 : failure === 'http503' ? 503 : failure === 'http422' ? 422 : 200;
  const result = status === 503 || status === 422 ? { detail: 'request failed' } :
    { mode: failure === 'mode' ? 'article' : mode, resolved_text: failure === 'text' ? 'changed example' : 'example', overall: { label: 'LEFT' } };
  const locator = { fill: async () => {}, click: async () => {}, waitFor: async () => {} };
  const page = {
    setDefaultTimeout() {}, on() {},
    goto: async () => ({ status: () => 200 }), url: () => 'https://bias.r4him.tech/',
    getByLabel: () => locator, getByRole: (role, options) => { buttons.push(options.name); return locator; },
    waitForFunction: async () => {
      if (++waits === 2 && failure === 'ui') throw new Error('render timeout');
    },
    waitForResponse: async () => ({ text: async () => {
      if (failure === 'body') throw new Error('body unavailable');
      return failure === 'json' ? '<html>Bad gateway</html>' : JSON.stringify(result);
    }, status: () => status, ok: () => status === 200 }),
    screenshot: async () => { if (failure === 'screenshot') throw new Error('capture timeout'); },
    locator: () => ({ innerText: async () => 'visible' }),
    setViewportSize: async () => {}, evaluate: async () => false
  };
  const process = { argv: ['node', 'script', 'input', 'output'], env: {} };
  await vm.runInNewContext(source, {
    require(name) {
      if (name === 'fs') return { mkdirSync() {}, readFileSync: () => JSON.stringify([{id:'one',text:'example',mode,...input}]),
        writeFileSync: (file, value) => writes.push(JSON.parse(value)) };
      if (name === 'path') return path;
      if (name === 'playwright') return { chromium: { launch: async () => ({
        version: () => 'mock', newPage: async () => page, close: async () => { closed = true; }
      }) } };
      throw new Error('Unexpected dependency');
    }, process, console: { log() {} }, Date
  });
  assert(closed);
  assert(buttons.includes({article:'Article',sentence:'Sentence',paragraph:'Paragraph'}[mode]));
  assert.equal(writes[0].cases[0].requested_mode, mode);
  assert.equal(writes[0].cases[0].status, status);
  assert.equal(writes[0].cases[0].body_read, 'pending');
  assert.equal(writes[0].cases[0].ui_verification, 'pending');
  assert.equal(writes[0].cases[0].screenshot, 'pending');
  const final = writes.at(-1);
  assert.equal(final.cases.length, 1);
  assert(final.finished_at);
  if (failure === 'json') {
    assert.equal(final.cases[0].response_text, '<html>Bad gateway</html>');
    assert.equal(final.cases[0].body_read, 'complete');
    assert.equal(final.cases[0].json_decode, 'pending');
    assert.equal(final.cases[0].result, undefined);
  } else if (failure === 'body') {
    assert.equal(final.cases[0].body_read, 'pending');
    assert.equal(final.cases[0].result, undefined);
  } else if (failure === 'http503' || failure === 'http422') {
    assert.deepEqual(JSON.parse(final.cases[0].response_text), result);
    assert.equal(final.cases[0].result.detail, 'request failed');
    assert.equal(final.cases[0].json_decode, 'complete');
    assert.equal(final.error, 'Prediction HTTP error: ' + status);
  } else {
    assert.equal(final.cases[0].result.overall.label, 'LEFT');
    assert.equal(final.cases[0].json_decode, 'complete');
  }
  if (failure) {
    assert.equal(process.exitCode, 1);
    assert.equal(final.cases[0].error, final.error);
    assert.equal(final.cases[0].screenshot, 'pending');
    assert.equal(final.cases[0].ui_verification, failure === 'screenshot' ? 'complete' : 'pending');
    if (failure === 'text') {
      assert.equal(final.error, 'Resolved text differs from expected input');
      assert.equal(final.cases[0].input_verification, 'pending');
      assert.equal(final.cases[0].result.resolved_text, 'changed example');
    }
  } else {
    assert.equal(final.cases[0].input_verification, input.text && !input.expected_resolved_text ? 'not_checked_url' : 'complete');
    assert.equal(final.cases[0].screenshot, 'complete');
    assert.equal(final.cases[0].visible_text, 'visible');
    assert.equal(final.mobile_overflow, false);
    assert.equal(process.exitCode, undefined);
  }
}

(async () => {
  for (const failure of [null, 'ui', 'screenshot', 'json', 'body']) await simulate(failure);
  await simulate(null, 'paragraph');
  await simulate('mode', 'sentence');
  await simulate('http503');
  await simulate('http422');
  await simulate('text');
  await simulate(null, 'article', {text:'https://example.com/article'});
  await simulate(null, 'article', {text:'https://example.com/article',expected_resolved_text:'example'});
  await simulate('text', 'article', {text:'https://example.com/article',expected_resolved_text:'example'});
  console.log('13 response-persistence/mode/input scenarios passed (mock browser)');
})().catch(error => { console.error(error); process.exitCode = 1; });
