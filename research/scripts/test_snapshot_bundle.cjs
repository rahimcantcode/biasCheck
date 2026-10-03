const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {createHash} = require('node:crypto');
const {chromium} = require('playwright');

(async () => {
  const [bundlePath, output] = process.argv.slice(2);
  const bytes = fs.readFileSync(bundlePath);
  const rows = JSON.parse(bytes);
  fs.mkdirSync(output, {recursive: true});
  const browser = await chromium.launch({executablePath: process.env.BIASCHECK_TEST_BROWSER,
    headless: true, args: ['--disable-webgl']});
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    const errors = [], requests = [], checks = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => {if(/^https?:/.test(request.url())) requests.push(request.url())});
    await page.goto(pathToFileURL(path.resolve('research/annotation/Bias_Checker_Review_Pilot.html')).href);
    await page.locator('#reviewer').fill('automated-test-only');
    await page.locator('#start').click();
    await page.locator('#rationale').fill('Unsaved draft must survive snapshot loading.');
    const upload = async data => {
      await page.locator('#bundle').setInputFiles({name: 'snapshots.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(data))});
      await page.waitForFunction(() => !document.querySelector('#bundle').disabled);
    };
    const reject = async (name, data) => {
      await upload(data);
      assert.match(await page.locator('#status').innerText(), /Bundle rejected/);
      assert.equal(await page.evaluate(() => texts.size), 40);
      checks.push(name);
    };
    await reject('missing item rejected atomically', rows.slice(1));
    await reject('duplicate ID rejected atomically', [...rows.slice(0, -1), rows[0]]);
    await reject('unknown ID rejected atomically', rows.map((r,i) => i === 99 ? {...r,id:'unknown'} : r));
    await reject('late changed text rejected atomically', rows.map((r,i) => i === 99 ? {...r,text:r.text+' changed'} : r));
    await upload(rows);
    assert.equal(await page.evaluate(() => texts.size), 100);
    assert.equal(await page.locator('#rationale').inputValue(), 'Unsaved draft must survive snapshot loading.');
    assert.equal(await page.evaluate(() => dirty), true);
    assert.equal(await page.locator('#save').isEnabled(), true);
    assert.equal(await page.locator('#text').innerText(), rows.find(r=>r.id==='P001').text);
    checks.push('all 100 loaded', 'unsaved draft preserved', 'verified article rendered');
    // Do not create synthetic reviewer judgments or exports.
    assert.equal(await page.evaluate(() => Object.keys(answers).length), 0);
    assert.deepEqual(requests, []);
    assert.deepEqual(errors, []);
    await page.screenshot({path: path.join(output, 'desktop.png'), fullPage:true});
    await page.setViewportSize({width:390,height:844});
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    assert.equal(overflow, false);
    await page.screenshot({path: path.join(output, 'mobile.png'), fullPage:true});
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify({timestamp:new Date().toISOString(),
      browser:await browser.version(), browser_location:'local Chromium fallback', checks,
      bundle_sha256:createHash('sha256').update(bytes).digest('hex'),
      viewer_sha256:createHash('sha256').update(fs.readFileSync('research/annotation/Bias_Checker_Review_Pilot.html')).digest('hex'),
      manifest_sha256:createHash('sha256').update(fs.readFileSync('research/annotation/pilot_manifest.json')).digest('hex'), page_errors:errors,
      network_requests:requests, mobile_overflow:overflow, human_annotations_created:0}, null, 2));
    console.log(JSON.stringify({checks, output}));
  } finally {await browser.close()}
})().catch(error => {console.error(error); process.exitCode = 1});
