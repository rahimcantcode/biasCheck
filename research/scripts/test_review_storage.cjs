const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');

(async () => {
  const output = process.argv[2];
  fs.mkdirSync(output, {recursive:true});
  const viewer = path.resolve('research/annotation/Bias_Checker_Review_Pilot.html');
  const browser = await chromium.launch({executablePath:process.env.BIASCHECK_TEST_BROWSER,
    headless:true, args:['--disable-webgl']});
  try {
    const page = await browser.newPage({viewport:{width:1280,height:900}});
    const errors = [], checks = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(pathToFileURL(viewer).href);
    await page.locator('#reviewer').fill('automated-storage-test');
    await page.locator('#start').click();
    const index = await page.evaluate(() => pilot.items.findIndex(item => item.kind === 'controlled_example'));
    await page.locator('#jump').selectOption(String(index));
    await page.evaluate(() => {
      window.originalSetItem = Storage.prototype.setItem;
      Storage.prototype.setItem = function () {throw new DOMException('Injected test failure','QuotaExceededError')};
    });
    // Synthetic test judgment, never retained as a human annotation or gold label.
    await page.locator('#read').check();
    await page.locator('#relevance').selectOption('UNCERTAIN');
    await page.locator('#label').selectOption('UNCERTAIN');
    await page.locator('#confidence').selectOption('low');
    await page.locator('#rationale').fill('AUTOMATED TEST ONLY: storage recovery fixture, not a human judgment.');
    await page.locator('#save').click();
    assert.match(await page.locator('#error').innerText(), /Browser storage failed/);
    assert.equal(await page.evaluate(() => storagePending), true);
    checks.push('save failure warning retained');
    const originalId = await page.evaluate(() => pilot.items[current].id);
    await page.locator('#prev').click();
    assert.match(await page.locator('#error').innerText(), /Browser storage failed/);
    assert.equal(await page.evaluate(() => {
      const event = new Event('beforeunload', {cancelable:true});
      dispatchEvent(event); return event.defaultPrevented;
    }), true);
    checks.push('navigation preserves pending warning and unload protection');
    await page.locator('#reviewer').fill('another-test-reviewer');
    await page.locator('#start').click();
    assert.equal(await page.evaluate(() => active), 'automated-storage-test');
    assert.equal(await page.evaluate(() => Object.keys(answers).length), 1);
    checks.push('workspace replacement blocked while storage pending');
    await page.locator('#skip').fill('AUTOMATED TEST ONLY');
    await page.locator('#skipButton').click();
    assert.match(await page.locator('#error').innerText(), /Browser storage failed/);
    checks.push('skip failure warning retained');
    const downloadEvent = page.waitForEvent('download');
    await page.locator('#export').click();
    const stream = await (await downloadEvent).createReadStream();
    const chunks=[];for await (const chunk of stream) chunks.push(chunk);
    const exported = JSON.parse(Buffer.concat(chunks).toString());
    assert.equal(exported.annotations.length, 2);
    assert.equal(exported.annotations.find(row=>row.id===originalId).rationale.startsWith('AUTOMATED TEST ONLY'), true);
    assert.equal(await page.evaluate(() => storagePending), true);
    checks.push('in-memory records recoverable by export without false persistence claim');
    await page.screenshot({path:path.join(output,'storage-warning.png'),fullPage:true});
    await page.evaluate(() => {Storage.prototype.setItem = window.originalSetItem});
    await page.locator('#skipButton').click();
    assert.equal(await page.evaluate(() => storagePending), false);
    assert.equal(await page.locator('#error').innerText(), 'Skip recorded.');
    assert.equal(await page.evaluate(() => Object.keys(JSON.parse(localStorage.getItem(key()))).length), 2);
    checks.push('successful retry persists all pending records and clears warning');
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({timestamp:new Date().toISOString(),
      browser:browser.version(),environment:'local Chromium fallback',checks,page_errors:errors,
      viewer_sha256:createHash('sha256').update(fs.readFileSync(viewer)).digest('hex'),
      synthetic_test_records:2,human_annotations_created:0,synthetic_exports_retained:false},null,2));
    console.log(JSON.stringify({checks,output}));
  } finally {await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
