const {spawn}=require('child_process');
const fs=require('fs');
const assert=require('assert');
const {chromium}=require('playwright');
const path=require('path');
const root=path.resolve(__dirname,'../..');
const artifactDir=process.env.BIASCHECK_TEST_ARTIFACTS || path.join(root,'research/data/browser-smoke');
fs.mkdirSync(artifactDir,{recursive:true});
const backend=spawn(process.env.BIASCHECK_TEST_PYTHON || root+'/backend/.venv/bin/python',['-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000'],{cwd:root,env:{...process.env,BIASCHECK_ENGINE:'political_nli'},stdio:['ignore','pipe','pipe']});
const frontend=spawn(process.execPath,[root+'/frontend/node_modules/next/dist/bin/next','start','--hostname','127.0.0.1'],{cwd:root+'/frontend',stdio:['ignore','pipe','pipe']});
let logs='';for(const child of [backend,frontend])for(const stream of [child.stdout,child.stderr])stream.on('data',d=>logs+=d.toString());
async function ready(url){for(let i=0;i<120;i++){try {let r=await fetch(url);if(r.ok)return;}catch{}await new Promise(r=>setTimeout(r,500));}throw new Error('Not ready '+url+' '+logs);}
(async()=>{let browser;try{
 await ready('http://127.0.0.1:8000/health');await ready('http://127.0.0.1:3000');
 browser=await chromium.launch({executablePath:process.env.BIASCHECK_TEST_BROWSER || undefined,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 const page=await browser.newPage({viewport:{width:1280,height:900}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:3000');
 const report={purpose:'Real browser + built Next frontend + real model API integration, not accuracy',browser:await browser.version(),cases:[]};
 const left='I support higher taxes on wealthy households to fund universal healthcare and stronger social safety nets.';
 const right='I support lower corporate taxes and fewer regulations because private enterprise should drive economic growth.';
 for(const [text,expected] of [['I cooked dinner with my family yesterday and we enjoyed a quiet evening at home.','No political content detected'],['Taxes.','More context needed'],[right,'Tentative Right'],[left+'\n\n'+right,'Mixed or conflicting signals']]){
  await page.getByLabel('Article text or URL').fill(text);
  const responsePromise=page.waitForResponse(r=>r.url().endsWith('/predict'),{timeout:180000});
  await page.getByRole('button',{name:'Analyze',exact:true}).click();
  const response=await responsePromise;assert.equal(response.status(),200);const data=await response.json();
  await page.getByText(expected,{exact:true}).waitFor({state:'visible'});
  report.cases.push({input:text,response:data});console.log('Browser case passed:',expected);
 }
 await page.screenshot({path:path.join(artifactDir,'ui-desktop.png'),fullPage:true});
 await page.getByRole('button',{name:'Sentence',exact:true}).click();
 const responsePromise=page.waitForResponse(r=>r.url().endsWith('/predict'),{timeout:180000});
 await page.getByRole('button',{name:'Analyze',exact:true}).click();const data=await (await responsePromise).json();assert.equal(data.mode,'sentence');assert.equal(data.results.length,2);
 await page.getByText('Inspect experimental passage assessments',{exact:true}).click();
 await page.getByText('Tentative Left',{exact:true}).waitFor();await page.getByText('Tentative Right',{exact:true}).waitFor();
 report.cases.push({mode:'sentence',response:data});
 await page.setViewportSize({width:390,height:844});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
 await page.screenshot({path:path.join(artifactDir,'ui-mobile.png'),fullPage:true});
 await page.route('**/predict',async route=>{await new Promise(r=>setTimeout(r,750));await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});});
 await page.getByRole('button',{name:'Analyze',exact:true}).click();await page.getByRole('button',{name:'Clear',exact:true}).click();await page.waitForTimeout(1200);assert.equal(await page.getByLabel('Article text or URL').inputValue(),'');assert.equal(await page.getByText('Analysis complete',{exact:true}).count(),0);
 await page.unroute('**/predict');await page.route('**/predict',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'The model is busy. Please try again shortly.'})}));
 await page.getByLabel('Article text or URL').fill(right);await page.getByRole('button',{name:'Analyze',exact:true}).click();await page.getByRole('alert').filter({hasText:'Analysis failed'}).waitFor();
 report.checks=['Desktop real inference','Sentence passage assessments','Mobile no horizontal overflow','Clear prevents stale results','Busy error displayed'];report.page_errors=errors;assert.deepEqual(errors,[]);
 fs.writeFileSync(root+'/research/results/browser_integration.json',JSON.stringify(report,null,2));console.log('Browser integration passed');
}catch(e){console.error(e);console.error(logs.slice(-4000));process.exitCode=1;}finally{if(browser)await browser.close();backend.kill();frontend.kill();}})();
