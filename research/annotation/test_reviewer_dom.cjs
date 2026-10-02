/* Node DOM/event fixture: no network, browser launch or completed human review.
 * This checks event behavior, not visual layout or real browser compatibility. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {webcrypto,createHash}=require('node:crypto');
const folder=__dirname,html=fs.readFileSync(path.join(folder,'Bias_Checker_Review_Pilot.html'),'utf8');
const manifest=JSON.parse(fs.readFileSync(path.join(folder,'pilot_manifest_v2.json'),'utf8'));
const storage=new Map(),nodes=new Map(),confirmations=[];let exportedBlob;
function node(){return {value:'',checked:false,disabled:false,textContent:'',children:[],listeners:{},appendChild(child){this.children.push(child);},replaceChildren(){this.children=[];},addEventListener(event,fn){this.listeners[event]=fn;},click(){if(this.onclick)return this.onclick();}};}
for(const match of html.matchAll(/\bid="([^"]+)"/g))nodes.set(match[1],node());
nodes.get('pilot-data').textContent=JSON.stringify(manifest);
const context=vm.createContext({document:{getElementById(id){assert(nodes.has(id),'HTML must contain control '+id);return nodes.get(id);},createElement:()=>node()},window:{addEventListener(){}},localStorage:{getItem:key=>storage.get(key)||null,setItem:(key,value)=>storage.set(key,value)},confirm:()=>confirmations.length?confirmations.shift():true,crypto:webcrypto,TextEncoder,Blob,URL:{createObjectURL(blob){exportedBlob=blob;return 'test-blob';},revokeObjectURL(){}},setTimeout:()=>0,AbortSignal,Date,console});
const run=source=>vm.runInContext(source,context);
const el=id=>nodes.get(id);
const input=(id,value)=>{el(id).value=value;el(id).listeners.input?.();};
const clone=value=>JSON.parse(JSON.stringify(value));
async function importReview(value){await el('import').onchange({target:{files:[{text:async()=>JSON.stringify(value)}],value:'fixture.json'}});}
(async()=>{
  run(fs.readFileSync(path.join(folder,'reviewer.js'),'utf8'));
  await run('initialize()');
  assert.equal(run('texts.size'),40,'all embedded controlled texts verified');
  input('reviewer','reviewer-fixture');el('start').click();
  assert.match(el('error').textContent,/human/);
  el('human').checked=true;el('independent').checked=true;el('start').click();
  const index=manifest.items.findIndex(x=>x.kind==='controlled_example');
  run(`nav(${index})`);assert.equal(el('save').disabled,false);
  el('read').checked=true;
  input('relevance','POLITICAL');el('relevance').onchange();
  input('author_framing','LEFT');el('author_framing').onchange();
  input('issue_policy_stance','NO_EXPLICIT_STANCE');
  input('attribution','AUTHOR_NARRATION');input('context_sufficiency','SUFFICIENT');
  input('uncertainty_reason','NONE');input('confidence','low');
  input('rationale','Synthetic automated DOM test only; this is not a real human annotation.');
  input('review_phase','initial_independent_10');input('review_pass_id','DOM-test-only');
  el('save').click();assert.match(el('error').textContent,/exposure|context/);
  for(const id of ['model_predictions','legacy_labels','other_reviewer_answers'])input(id,'false');
  input('model_predictions','true');input('exposure_notes','Saw a synthetic machine fixture before this automated test.');
  input('external_context_used','true');input('external_context_notes','Synthetic fixture context only; no actual article was reviewed.');
  el('save').click();assert.match(el('error').textContent,/Saved/);
  assert.equal(el('derived_label').textContent,'LEFT','no-policy-stance must not become CENTER');
  const item=manifest.items[index],key=manifest.pilot_id+':reviewer-fixture';
  let saved=JSON.parse(storage.get(key));assert.equal(saved.annotations[0].label,'LEFT');
  assert.equal(saved.annotations[0].prior_exposure.model_predictions,true);
  assert.equal(saved.annotations[0].text_context.text_sha256,item.text_sha256);
  // Reopening workspace restores all provenance fields, not just the label.
  el('start').click();assert.equal(el('model_predictions').value,'true');
  assert.equal(el('external_context_used').value,'true');
  // Cancelled navigation preserves dirty fields; accepted navigation resets them.
  input('rationale','Unsaved fixture text');confirmations.push(false);el('next').click();
  assert.equal(el('heading').textContent,item.id);assert.equal(el('rationale').value,'Unsaved fixture text');
  confirmations.push(false);el('export').click();assert.equal(exportedBlob,undefined);
  confirmations.push(true);el('export').click();
  let exported=JSON.parse(await exportedBlob.text());assert.equal(exported.annotations[0].rationale,saved.annotations[0].rationale);
  confirmations.push(true);run(`nav(${index+1})`);assert.equal(el('heading').textContent,manifest.items[index+1].id);
  // Invalid imports must never modify either current workspace or stored records.
  const invalid=[];
  for(const [field,value] of [['pilot_id','wrong'],['rubric_version','v1'],['schema_version',1],['reviewer_id',''],['reviewer_id',' '],['reviewer_kind','machine'],['annotation_method','model_generated'],['independently_completed',false]]){const candidate=clone(saved);candidate[field]=value;invalid.push(candidate);}
  const dup=clone(saved);dup.annotations.push(clone(dup.annotations[0]));invalid.push(dup);
  const mixed=clone(saved);mixed.annotations[0].reviewer_id='different-human';invalid.push(mixed);
  const exposure=clone(saved);delete exposure.annotations[0].prior_exposure.model_predictions;invalid.push(exposure);
  for(const value of invalid){const before=JSON.stringify([...storage]);await importReview(value);assert.match(el('error').textContent,/Import rejected/);assert.equal(JSON.stringify([...storage]),before);}
  // Valid import round-trips exact exposure/context provenance.
  await importReview(exported);assert.match(el('error').textContent,/provenance preserved/);
  saved=JSON.parse(storage.get(key));assert.deepEqual(saved.annotations[0].prior_exposure,exported.annotations[0].prior_exposure);assert.deepEqual(saved.annotations[0].text_context,exported.annotations[0].text_context);
  run(`nav(${index})`);assert.equal(el('model_predictions').value,'true');assert.equal(el('external_context_used').value,'true');
  // Exact-span UI mapping, independent direction, duplicate rejection and round-trip.
  const quote=item.text.slice(0,Math.min(25,item.text.length));
  input('span_quote',quote);input('span_direction','RIGHT');input('span_attribution','QUOTED');
  el('addSpan').click();assert.match(el('error').textContent,/Exact span added/);
  assert.equal(el('span_status').value,'ANNOTATED');
  el('addSpan').click();assert.match(el('error').textContent,/nonoverlapping/);
  el('save').click();assert.match(el('error').textContent,/Saved/);
  el('export').click();exported=JSON.parse(await exportedBlob.text());
  assert.equal(exported.annotations[0].label,'LEFT','span direction must not alter article framing');
  assert.equal(exported.annotations[0].evidence_spans[0].direction,'RIGHT');
  assert.equal(exported.annotations[0].evidence_spans[0].text,quote);
  assert.equal(exported.annotations[0].evidence_spans[0].source_text_sha256,item.text_sha256);
  await importReview(exported);assert.match(el('error').textContent,/provenance preserved/);
  const badSpan=clone(exported);badSpan.annotations[0].evidence_spans[0].start+=1;badSpan.annotations[0].evidence_spans[0].end+=1;
  await importReview(badSpan);assert.match(el('error').textContent,/Import rejected.*exactly match/);
  const badHash=clone(exported);badHash.annotations[0].evidence_spans[0].source_text_sha256='changed';
  await importReview(badHash);assert.match(el('error').textContent,/Import rejected.*hash mismatch/);
  const historical=manifest.items.find(x=>x.kind==='historical_article'),missingSnapshot=clone(exported),historicalRow=missingSnapshot.annotations[0];
  historicalRow.id=historical.id;historicalRow.text_sha256=historical.text_sha256;historicalRow.text_context.text_sha256=historical.text_sha256;historicalRow.evidence_spans[0].source_text_sha256=historical.text_sha256;
  await importReview(missingSnapshot);assert.match(el('error').textContent,/Import rejected.*Load the exact verified source snapshot/);
  // JS indexes UTF-16 internally, but exported offsets count Unicode codepoints.
  const unicode='😀 do not support taxes. do not support taxes. e\u0301';
  const offsets=JSON.parse(run('JSON.stringify(exactOccurrences('+JSON.stringify(unicode)+',"do not support taxes"))'));
  assert.deepEqual(offsets,[2,24]);
  assert.deepEqual(JSON.parse(run('JSON.stringify(exactOccurrences("aaaa","aa"))')),[0,1,2],'repeated occurrence finder handles overlapping textual occurrences');
  const unicodeSpan={span_protocol_version:1,span_status:'ANNOTATED',evidence_spans:[{start:2,end:22,text:'do not support taxes',source_text_sha256:'fixture-hash',direction:'RIGHT',attribution:'AUTHOR'}]};
  run('texts.set("unicode-fixture",'+JSON.stringify(unicode)+')');
  run('validateSpans('+JSON.stringify(unicodeSpan)+',{id:"unicode-fixture",text_sha256:"fixture-hash"})');
  assert.equal(unicodeSpan.evidence_spans[0].text,'do not support taxes','negation is preserved exactly');
  // Simulate a fresh-page restore of historical spans using test-only pinned text.
  // The fixture is in memory only; no production manifest or real annotation is modified.
  const reloadHash=createHash('sha256').update(unicode).digest('hex');
  const reloadItem={id:'historical-reload-fixture',kind:'historical_article',dataset_id:'reload-fixture',text:null,text_sha256:reloadHash};
  const reloadIndex=run('pilot.items.length');run('pilot.items.push('+JSON.stringify(reloadItem)+')');
  const reloadReview=clone(exported);reloadReview.reviewer_id='reviewer-reload-fixture';
  const reloadRow=reloadReview.annotations[0];reloadRow.id=reloadItem.id;reloadRow.reviewer_id=reloadReview.reviewer_id;reloadRow.text_sha256=reloadHash;reloadRow.text_context.text_sha256=reloadHash;
  reloadRow.evidence_spans=clone(unicodeSpan.evidence_spans);reloadRow.evidence_spans[0].source_text_sha256=reloadHash;
  const reloadKey=manifest.pilot_id+':'+reloadReview.reviewer_id,reloadRaw=JSON.stringify(reloadReview);storage.set(reloadKey,reloadRaw);
  run('texts.delete("historical-reload-fixture");active="";answers={};dirty=false;current=0;render()');
  input('reviewer',reloadReview.reviewer_id);el('start').click();
  assert.match(el('error').textContent,/Could not open stored review.*After a page reload/);
  assert.equal(storage.get(reloadKey),reloadRaw,'failed restore must preserve the complete saved export');
  const fileEvent=text=>({target:{files:[{name:'reload-fixture.json',text:async()=>JSON.stringify({ID:'reload-fixture',content_original:text})}]}});
  await el('files').onchange(fileEvent(unicode+' changed'));
  assert.match(el('status').textContent,/0 matching article snapshots verified; 1 failed/);
  el('start').click();assert.match(el('error').textContent,/Could not open stored review/);
  assert.equal(storage.get(reloadKey),reloadRaw,'wrong snapshot cannot unlock or rewrite annotations');
  await el('files').onchange(fileEvent(unicode));
  assert.match(el('status').textContent,/1 matching article snapshots verified; 0 failed/);
  el('start').click();assert.equal(run('active'),reloadReview.reviewer_id);
  run('nav('+reloadIndex+')');assert.equal(el('heading').textContent,reloadItem.id);
  assert.equal(el('span_status').value,'ANNOTATED');assert.equal(el('model_predictions').value,'true');
  assert.deepEqual(JSON.parse(run('JSON.stringify(draftSpans)')),reloadRow.evidence_spans);
  assert.equal(storage.get(reloadKey),reloadRaw,'successful restore must also preserve original provenance');
  // Corrupt local state is rejected rather than overwritten as a new empty review.
  const corruptKey=manifest.pilot_id+':corrupt-fixture';storage.set(corruptKey,'{"schema_version":1}');input('reviewer','corrupt-fixture');el('start').click();assert.match(el('error').textContent,/Could not open stored review/);assert.equal(storage.get(corruptKey),'{"schema_version":1}');
  console.log(JSON.stringify({checks:50,exported}));
})().catch(error=>{console.error(error);process.exitCode=1;});
