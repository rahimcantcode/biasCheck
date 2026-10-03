#!/usr/bin/env node
// Optional local browser smoke. API responses are synthetic fixtures, never model accuracy data.
// Run a built frontend on 127.0.0.1:3015 first. Requires Playwright and Chromium.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(require.resolve('playwright', {
  paths: [process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES || process.cwd()],
}));

const destination = path.resolve(process.argv[2] || '/tmp/biascheck-browser-smoke');
fs.mkdirSync(destination, { recursive: true });
const source = 'Café 𝟙: my cat is pretty and taxing the rich is good.\n\nThis is a synthetic interface fixture.';
const phrase = 'taxing the rich is good';
const phraseStart = Array.from(source.slice(0, source.indexOf(phrase))).length;
const evidence = { start: phraseStart, end: phraseStart + phrase.length, text: phrase,
  label: 'LEFT', attribution: 'author', status: 'experimental', rationale: 'Synthetic fixture for interface testing.' };
const modelResult = { label: 'LEFT', label_id: 0, raw_label: 'LEFT', decision: 'classified', reason: 'demo_estimate',
  token_count: 24, tokens_processed: 24, chunk_count: 1, truncated: false, calibrated: false,
  score_type: 'class_probability', probabilities: { LEFT: 0.8, CENTER: 0.1, RIGHT: 0.1 } };

(async () => {
  const browser = await chromium.launch({ headless: true,
    executablePath: process.env.BIASCHECK_BROWSER_EXECUTABLE || undefined });
  const report = { purpose: 'Local browser UI contracts with mocked predictions; no accuracy or live deployment test',
    generated_at_utc: new Date().toISOString(), browser: browser.version(), viewports: [] };
  try {
    for (const [name, viewport] of [['desktop', { width: 1440, height: 1000 }], ['mobile', { width: 390, height: 844 }]]) {
      const context = await browser.newContext({ viewport, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const errors = [];
      const requests = [];
      page.on('pageerror', error => errors.push(String(error)));
      await page.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (url.hostname !== '127.0.0.1' || url.port !== '3015') return route.abort();
        if (url.pathname !== '/api/predict') return route.continue();
        const request = route.request().postDataJSON();
        assert.equal(request.input, source);
        requests.push(request.mode);
        const data = { source_type: 'text', resolved_text: request.input, mode: request.mode,
          overall: modelResult, results: [{ ...modelResult, text: source, start: 0, end: Array.from(source).length, segment_index: 0 }],
          warnings: ['Synthetic interface test. Not model accuracy evidence.'], model: { weights_sha256: 'synthetic-ui-fixture', aggregation: 'synthetic' },
          evidence_status: 'available', evidence_spans: [evidence], evidence_metadata: { offset_unit: 'unicode_code_point' } };
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
      });
      await page.goto('http://127.0.0.1:3015', { waitUntil: 'networkidle' });
      await page.getByRole('heading', { name: 'See how your article leans' }).waitFor();
      const layout = await page.evaluate(() => {
        const input = document.querySelector('#article-input');
        const about = document.querySelector('a[href="#model-details"]');
        return { horizontalOverflow: document.documentElement.scrollWidth > innerWidth,
          inputWidth: input.getBoundingClientRect().width,
          background: getComputedStyle(document.body).backgroundColor,
          aboutColor: getComputedStyle(about).color,
          aboutDisplay: getComputedStyle(about).display };
      });
      assert.equal(layout.horizontalOverflow, false, `${name}: horizontal overflow`);
      assert.ok(layout.inputWidth >= 200);
      await page.screenshot({ path: path.join(destination, `${name}-home.png`), fullPage: true, animations: 'disabled' });
      await page.getByLabel('Article text or URL').fill(source);
      for (const mode of ['article', 'sentence', 'paragraph']) {
        const label = mode.charAt(0).toUpperCase() + mode.slice(1);
        await page.getByRole('button', { name: label, exact: true }).click();
        await page.getByRole('button', { name: 'Analyze', exact: true }).click();
        const article = page.getByRole('article', { name: 'Analyzed article' });
        await article.waitFor();
        assert.equal(await article.textContent(), source);
        assert.equal(await article.locator('mark').count(), 1);
        const mark = article.getByRole('button');
        assert.equal(await mark.textContent(), phrase);
        await mark.focus();
        await page.keyboard.press('Enter');
        assert.equal(await mark.getAttribute('aria-pressed'), 'true');
        await page.keyboard.press('Escape');
        assert.equal(await mark.getAttribute('aria-pressed'), 'false');
        const inspector = page.getByText('Inspect experimental passage estimates', { exact: true });
        if (mode === 'article') {
          assert.equal(await inspector.count(), 0);
        } else {
          await inspector.click();
          await page.getByText('Experimental Left estimate', { exact: true }).waitFor();
        }
      }
      await page.getByRole('article', { name: 'Analyzed article' }).scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(destination, `${name}-results.png`), fullPage: true, animations: 'disabled' });
      const highlightStyle = await page.locator('mark').evaluate(node => {
        const css = getComputedStyle(node);
        return { radius: css.borderRadius, textDecoration: css.textDecorationLine, background: css.backgroundColor,
          color: css.color, cursor: css.cursor };
      });
      assert.equal(highlightStyle.radius, '2px');
      assert.ok(highlightStyle.textDecoration.includes('underline'));
      assert.equal(highlightStyle.cursor, 'pointer');
      await page.getByRole('button', { name: 'Highlight expressions', exact: true }).click();
      assert.equal(await page.locator('mark').count(), 0);
      assert.equal(await page.getByRole('article', { name: 'Analyzed article' }).textContent(), source);
      await page.getByRole('button', { name: 'Clear', exact: true }).click();
      assert.equal(await page.getByRole('article', { name: 'Analyzed article' }).count(), 0);
      assert.equal(await page.getByLabel('Article text or URL').inputValue(), '');
      assert.deepEqual(requests, ['article', 'sentence', 'paragraph']);
      assert.deepEqual(errors, [], `${name}: browser page errors`);
      report.viewports.push({ name, viewport, layout, highlightStyle, api_fixture_modes: requests,
        exact_source: true, keyboard_highlight_selection: true, passage_inspector: true, clear: true, page_errors: errors });
      await context.close();
    }
    fs.writeFileSync(path.join(destination, 'report.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
