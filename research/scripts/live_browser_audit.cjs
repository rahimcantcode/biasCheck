// Real public-site interactions; responses and screenshots retained per case.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const output = path.resolve(process.argv[3]);
fs.mkdirSync(output, { recursive: true });
(async () => {
  const args = process.env.BIASCHECK_DISABLE_WEBGL === '1' ? ['--disable-webgl'] : [];
  const browser = await chromium.launch({ headless: true, args, executablePath: process.env.BIASCHECK_TEST_BROWSER, timeout: 120000 });
  const report = { started_at: new Date().toISOString(), environment: 'local Chromium driving public deployed site; not cloud browser', browser_args: args, url: 'https://bias.r4him.tech/', browser: browser.version(), cases: [], page_errors: [], failed_requests: [] };
  let page, activeCase;
  try {
    page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    page.setDefaultTimeout(90000);
    page.on('pageerror', error => report.page_errors.push(error.message));
    page.on('requestfailed', request => report.failed_requests.push({ url: request.url(), error: request.failure() }));
    const response = await page.goto(report.url, { waitUntil: 'domcontentloaded', timeout: 90000 });
    console.log('page', response.status(), page.url());
    await page.getByLabel('Article text or URL').waitFor({ timeout: 60000 });
    await page.waitForFunction(() => Object.keys(document.querySelector('#article-input')).some(key => key.startsWith('__reactProps')), undefined, { timeout: 90000 });
    for (const row of input) {
      const mode = row.mode || 'article';
      const modeButtons = { article: 'Article', sentence: 'Sentence', paragraph: 'Paragraph' };
      if (!Object.hasOwn(modeButtons, mode)) throw new Error('Invalid requested mode: ' + mode);
      await page.getByRole('button', { name: modeButtons[mode], exact: true }).click();
      await page.getByLabel('Article text or URL').fill(row.text);
      const started = Date.now();
      const [prediction] = await Promise.all([
        page.waitForResponse(r => r.url().endsWith('/predict') && r.request().method() === 'POST', { timeout: 180000 }),
        page.getByRole('button', { name: 'Analyze', exact: true }).click()
      ]);
      // Preserve HTTP evidence even when body reading or JSON decoding fails.
      activeCase = { id: row.id, requested_mode: mode, status: prediction.status(), response_seconds: (Date.now() - started) / 1000,
        body_read: 'pending', json_decode: 'pending', ui_verification: 'pending', screenshot: 'pending' };
      report.cases.push(activeCase);
      fs.writeFileSync(path.join(output, 'audit.json'), JSON.stringify(report, null, 2));
      activeCase.response_text = await prediction.text();
      activeCase.body_read = 'complete';
      fs.writeFileSync(path.join(output, 'audit.json'), JSON.stringify(report, null, 2));
      const result = JSON.parse(activeCase.response_text);
      activeCase.result = result;
      activeCase.json_decode = 'complete';
      fs.writeFileSync(path.join(output, 'audit.json'), JSON.stringify(report, null, 2));
      if (prediction.ok() && result.mode !== mode) throw new Error('Response mode differs from requested mode');
      await page.getByRole('button', { name: 'Analyze', exact: true }).waitFor({ state: 'visible' });
      if (prediction.ok()) {
        await page.waitForFunction(text => document.querySelector('article[aria-label="Analyzed article"]')?.textContent === text, result.resolved_text);
      }
      activeCase.ui_verification = prediction.ok() ? 'complete' : 'not_applicable';
      await page.screenshot({ path: path.join(output, row.id + '.png'), fullPage: true });
      activeCase.screenshot = 'complete';
      activeCase.seconds = (Date.now() - started) / 1000;
      activeCase.visible_text = await page.locator('body').innerText();
      fs.writeFileSync(path.join(output, 'audit.json'), JSON.stringify(report, null, 2));
      console.log(row.id, prediction.status(), JSON.stringify(result.overall || result));
      activeCase = null;
    }
    await page.setViewportSize({ width: 390, height: 844 });
    report.mobile_overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    await page.screenshot({ path: path.join(output, 'mobile.png'), fullPage: true });
  } catch (error) {
    report.error = error.message;
    if (activeCase) activeCase.error = error.message;
    fs.writeFileSync(path.join(output, 'audit.json'), JSON.stringify(report, null, 2));
    if (page) await page.screenshot({ path: path.join(output, 'failure.png'), fullPage: true }).catch(() => {});
    process.exitCode = 1;
  } finally {
    report.finished_at = new Date().toISOString();
    fs.writeFileSync(path.join(output, 'audit.json'), JSON.stringify(report, null, 2));
    await browser.close();
  }
})();
