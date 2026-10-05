const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../research/scripts/live_browser_audit.cjs'), 'utf8');

async function simulate(failure) {
  const writes = [];
  let waits = 0, closed = false;
  const result = { resolved_text: 'example', overall: { label: 'LEFT' } };
  const locator = { fill: async () => {}, click: async () => {}, waitFor: async () => {} };
  const page = {
    setDefaultTimeout() {}, on() {},
    goto: async () => ({ status: () => 200 }), url: () => 'https://bias.r4him.tech/',
    getByLabel: () => locator, getByRole: () => locator,
    waitForFunction: async () => {
      if (++waits === 2 && failure === 'ui') throw new Error('render timeout');
    },
    waitForResponse: async () => ({ json: async () => result, status: () => 200, ok: () => true }),
    screenshot: async () => { if (failure === 'screenshot') throw new Error('capture timeout'); },
    locator: () => ({ innerText: async () => 'visible' }),
    setViewportSize: async () => {}, evaluate: async () => false
  };
  const process = { argv: ['node', 'script', 'input', 'output'], env: {} };
  await vm.runInNewContext(source, {
    require(name) {
      if (name === 'fs') return { mkdirSync() {}, readFileSync: () => '[{"id":"one","text":"example"}]',
        writeFileSync: (file, value) => writes.push(JSON.parse(value)) };
      if (name === 'path') return path;
      if (name === 'playwright') return { chromium: { launch: async () => ({
        version: () => 'mock', newPage: async () => page, close: async () => { closed = true; }
      }) } };
      throw new Error('Unexpected dependency');
    }, process, console: { log() {} }, Date
  });
  assert(closed);
  assert.equal(writes[0].cases[0].result.overall.label, 'LEFT');
  assert.equal(writes[0].cases[0].ui_verification, 'pending');
  assert.equal(writes[0].cases[0].screenshot, 'pending');
  const final = writes.at(-1);
  assert.equal(final.cases.length, 1);
  assert(final.finished_at);
  if (failure) {
    assert.equal(process.exitCode, 1);
    assert.equal(final.cases[0].error, final.error);
    assert.equal(final.cases[0].screenshot, 'pending');
    assert.equal(final.cases[0].ui_verification, failure === 'ui' ? 'pending' : 'complete');
  } else {
    assert.equal(final.cases[0].screenshot, 'complete');
    assert.equal(final.cases[0].visible_text, 'visible');
    assert.equal(final.mobile_overflow, false);
    assert.equal(process.exitCode, undefined);
  }
}

(async () => {
  for (const failure of [null, 'ui', 'screenshot']) await simulate(failure);
  console.log('3 response-persistence scenarios passed (mock browser)');
})().catch(error => { console.error(error); process.exitCode = 1; });
