'use strict';
const pilot=JSON.parse(document.getElementById('pilot-data').textContent),$=id=>document.getElementById(id),texts=new Map();
const fields=['relevance','author_framing','issue_policy_stance','attribution','context_sufficiency','uncertainty_reason','confidence','rationale','review_phase','review_pass_id','rubric_freeze_id'];
const exposures=['model_predictions','legacy_labels','other_reviewer_answers'];
const formFields=[...fields,...exposures,'exposure_notes','external_context_used','external_context_notes','read','skip'];
let current=0,active='',answers={},dirty=false,loading=false;
const key=()=>pilot.pilot_id+':'+active;
const allowed={relevance:['POLITICAL','NONPOLITICAL','UNCERTAIN'],author_framing:['LEFT','CENTER','RIGHT','UNCERTAIN','NOT_APPLICABLE'],issue_policy_stance:['NOT_ASSESSED','NO_EXPLICIT_STANCE','LEFT','CENTER','RIGHT','MIXED','UNCERTAIN','NOT_APPLICABLE'],attribution:['AUTHOR_NARRATION','QUOTED_SPEAKERS_ONLY','MIXED_AUTHOR_AND_QUOTES','NO_STANCE_EXPRESSED','UNCLEAR'],context_sufficiency:['SUFFICIENT','INSUFFICIENT','UNCERTAIN'],uncertainty_reason:['NONE','INSUFFICIENT_CONTEXT','MIXED_AUTHOR_POSITIONS','ATTRIBUTION_UNCLEAR','SARCASM_OR_AMBIGUITY','OUTSIDE_US_SCHEME','OTHER'],confidence:['low','medium','high'],review_phase:['initial_independent_10','post_discussion_rereview','frozen_main']};
const nonempty=(value,min=1)=>typeof value==='string'&&value.trim().length>=min;
const timestamp=value=>typeof value==='string'&&/([zZ]|[+-]\d\d:\d\d)$/.test(value)&&Number.isFinite(Date.parse(value));
function message(s){$('error').textContent=s;}
function derived(relevance,framing){return relevance==='POLITICAL'?framing:relevance;}
function envelope(rows=Object.values(answers),reviewer=active){return {schema_version:2,pilot_id:pilot.pilot_id,rubric_version:'v2',reviewer_id:reviewer,reviewer_kind:'human',annotation_method:'manual',independently_completed:true,exported_at:new Date().toISOString(),annotations:rows};}
function validateReview(review){
  if(!review||review.schema_version!==2||review.pilot_id!==pilot.pilot_id||review.rubric_version!=='v2')throw Error('Pilot or rubric mismatch. Preserve v1 exports and perform a new v2 review; no automatic migration.');
  if(typeof review.reviewer_id!=='string'||!/^[A-Za-z0-9_-]{2,40}$/.test(review.reviewer_id))throw Error('A valid nonempty reviewer ID is required.');
  if(review.reviewer_kind!=='human'||review.annotation_method!=='manual'||review.independently_completed!==true)throw Error('Only explicitly attested independent human manual reviews qualify; machine labels cannot be imported as human reviews.');
  if(!timestamp(review.exported_at)||!Array.isArray(review.annotations))throw Error('Valid export timestamp and annotation array required.');
  const known=new Map(pilot.items.map(x=>[x.id,x])),seen=new Set();
  for(const row of review.annotations){
    if(!row||typeof row!=='object'||!known.has(row.id)||seen.has(row.id))throw Error('Unknown or duplicate item ID.');
    seen.add(row.id);
    if(row.reviewer_id!==review.reviewer_id)throw Error('Inconsistent reviewer identity.');
    if(row.text_sha256!==known.get(row.id).text_sha256)throw Error('Text snapshot mismatch.');
    if(row.rubric_version!=='v2'||!timestamp(row.completed_at))throw Error('Per-item rubric mismatch or missing completion timestamp.');
    if(row.status==='skipped'){if(!nonempty(row.skip_reason,3))throw Error('Skip reason required.');continue;}
    if(row.status!=='reviewed'||row.full_text_read!==true)throw Error('Complete frozen-text review is required.');
    const context=row.text_context,exposure=row.prior_exposure;
    if(!context||context.scope!=='complete_frozen_text'||context.text_sha256!==known.get(row.id).text_sha256||typeof context.external_context_used!=='boolean')throw Error('Exact frozen text context and external-context disclosure required.');
    if(context.external_context_used&&!nonempty(context.external_context_notes,10))throw Error('Disclose what outside context you read and where (at least 10 characters).');
    if(!exposure||exposures.some(k=>typeof exposure[k]!=='boolean'))throw Error('Answer each prior-exposure question explicitly.');
    if(exposures.some(k=>exposure[k])&&!nonempty(exposure.notes,10))throw Error('Exposure details required (at least 10 characters).');
    for(const [field,values] of Object.entries(allowed))if(!values.includes(row[field]))throw Error('Choose a valid '+field.replaceAll('_',' ')+'.');
    if(!nonempty(row.review_pass_id))throw Error('Review pass ID required.');
    if(row.review_phase!=='initial_independent_10'&&!nonempty(row.rubric_freeze_id))throw Error('Record the agreed rubric freeze ID for a post-discussion or main pass.');
    if((row.relevance==='POLITICAL'&&(row.author_framing==='NOT_APPLICABLE'||row.label!==row.author_framing))||(row.relevance==='NONPOLITICAL'&&(row.author_framing!=='NOT_APPLICABLE'||row.label!=='NONPOLITICAL'))||(row.relevance==='UNCERTAIN'&&(row.author_framing!=='UNCERTAIN'||row.label!=='UNCERTAIN')))throw Error('Final label must follow relevance and author framing, never policy stance.');
    if(row.relevance==='NONPOLITICAL'&&!['NOT_ASSESSED','NOT_APPLICABLE','NO_EXPLICIT_STANCE'].includes(row.issue_policy_stance))throw Error('Nonpolitical material cannot have a directional policy stance.');
    if((row.label==='UNCERTAIN')===(row.uncertainty_reason==='NONE'))throw Error('Choose a reason for UNCERTAIN; choose NONE for a resolved primary label.');
    if(['LEFT','CENTER','RIGHT'].includes(row.label)&&row.context_sufficiency!=='SUFFICIENT')throw Error('Resolved political author framing requires sufficient context.');
    if(!nonempty(row.rationale,15))throw Error('Explain your evidence in at least 15 characters.');
    if(row.evidence_spans&&(!Array.isArray(row.evidence_spans)||row.evidence_spans.length))throw Error('Exact-span exports are not implemented in v2.');
  }
  return review;
}
function store(){try{localStorage.setItem(key(),JSON.stringify(envelope()));return true;}catch(e){message('Browser storage failed. Export before closing.');return false;}}
function progress(){$('progress').textContent=Object.values(answers).filter(x=>x.status==='reviewed').length+' / '+pilot.items.length+' reviewed';}
function syncLabel(){$('derived_label').textContent=derived($('relevance').value,$('author_framing').value)||'not selected';}
function render(){
  const item=pilot.items[current],a=answers[item.id]||{};
  $('heading').textContent=item.id;$('jump').value=String(current);$('kind').textContent=item.kind==='controlled_example'?'AI-authored controlled example':'Historical natural article';
  $('text').textContent=texts.get(item.id)||'Verified article text is not loaded. Load its frozen snapshot above. Do not judge from a URL or headline.';
  $('source').replaceChildren();if(item.url){const link=document.createElement('a');link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Original URL (outside review context; may differ from frozen text)';$('source').appendChild(link);}else $('source').textContent='Original AI-authored diagnostic text. No human gold label assigned.';
  $('hash').textContent='Exact supplied text SHA-256: '+item.text_sha256;
  $('read').checked=a.full_text_read===true;
  for(const field of fields)$(field).value=a[field]||(field==='issue_policy_stance'?'NOT_ASSESSED':'');
  for(const field of exposures)$(field).value=typeof a.prior_exposure?.[field]==='boolean'?String(a.prior_exposure[field]):'';
  $('exposure_notes').value=a.prior_exposure?.notes||'';
  $('external_context_used').value=typeof a.text_context?.external_context_used==='boolean'?String(a.text_context.external_context_used):'';
  $('external_context_notes').value=a.text_context?.external_context_notes||'';
  $('skip').value=a.skip_reason||'';
  for(const field of formFields)$(field).disabled=loading;
  $('save').disabled=!active||!texts.has(item.id)||loading;$('skipButton').disabled=!active||loading;
  $('prev').disabled=current===0||loading;$('next').disabled=current===pilot.items.length-1||loading;$('jump').disabled=loading;
  syncLabel();message('');progress();
}
for(const id of formFields)$(id).addEventListener('input',()=>{dirty=true;});
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
for(let i=0;i<pilot.items.length;i++){const option=document.createElement('option');option.value=String(i);option.textContent=pilot.items[i].id;$('jump').appendChild(option);}
$('start').onclick=()=>{
  if(dirty&&!confirm('Discard the unsaved judgment?'))return;
  const id=$('reviewer').value.trim();
  if(!/^[A-Za-z0-9_-]{2,40}$/.test(id)){message('Use 2-40 letters, numbers, underscores or hyphens for your reviewer ID.');return;}
  if(!$('human').checked||!$('independent').checked){message('Confirm human manual review and independent judgment with exposure disclosure.');return;}
  let restored={};try{const raw=localStorage.getItem(pilot.pilot_id+':'+id);if(raw){const data=validateReview(JSON.parse(raw));if(data.reviewer_id!==id)throw Error('Workspace identity mismatch.');restored=Object.fromEntries(data.annotations.map(x=>[x.id,x]));}}catch(e){message('Could not open stored review: '+e.message+' Export/retain the original data; it has not been overwritten.');return;}
  active=id;answers=restored;dirty=false;render();
};
function nav(n){if(loading)return;if(dirty&&!confirm('Discard the unsaved judgment?')){$('jump').value=String(current);return;}dirty=false;current=n;render();}
$('prev').onclick=()=>nav(Math.max(0,current-1));$('next').onclick=()=>nav(Math.min(pilot.items.length-1,current+1));$('jump').onchange=e=>nav(Number(e.target.value));
$('relevance').onchange=()=>{const relevance=$('relevance').value;$('author_framing').value=relevance==='NONPOLITICAL'?'NOT_APPLICABLE':relevance==='UNCERTAIN'?'UNCERTAIN':'';dirty=true;syncLabel();};
$('author_framing').onchange=()=>{dirty=true;syncLabel();};
$('save').onclick=()=>{
  const item=pilot.items[current];if(!active||!texts.has(item.id)||!$('read').checked||loading||!$('human').checked||!$('independent').checked){message('Read the complete verified text and confirm the checkbox.');return;}
  const row={id:item.id,status:'reviewed',reviewer_id:active,rubric_version:'v2',text_sha256:item.text_sha256,full_text_read:true,completed_at:new Date().toISOString()};
  for(const field of fields)row[field]=$(field).value.trim();row.label=derived(row.relevance,row.author_framing);
  row.prior_exposure={notes:$('exposure_notes').value.trim()};for(const field of exposures)row.prior_exposure[field]=$(field).value===''?null:$(field).value==='true';
  row.text_context={scope:'complete_frozen_text',text_sha256:item.text_sha256,external_context_used:$('external_context_used').value===''?null:$('external_context_used').value==='true',external_context_notes:$('external_context_notes').value.trim()};
  try{validateReview(envelope([row]));}catch(e){message(e.message);return;}
  if(answers[item.id]&&!confirm('Replace this saved judgment? Export the earlier pass first if you need to preserve it.'))return;
  answers[item.id]=row;dirty=false;const stored=store();progress();if(stored)message('Saved. Export to preserve this review pass.');
};
$('skipButton').onclick=()=>{if(!active||loading)return;const reason=$('skip').value.trim();if(reason.length<3){message('Record a reason for skipping.');return;}const item=pilot.items[current];if(answers[item.id]&&!confirm('Replace this saved judgment with a skip? Preserve the earlier export first.'))return;answers[item.id]={id:item.id,status:'skipped',reviewer_id:active,rubric_version:'v2',text_sha256:item.text_sha256,skip_reason:reason,completed_at:new Date().toISOString()};dirty=false;const stored=store();progress();if(stored)message('Skip recorded.');};
$('export').onclick=()=>{
  if(!active){message('Open your reviewer workspace first.');return;}
  if(dirty&&!confirm('Export saved judgments only? The current unsaved changes will not be included.'))return;
  try{const payload=validateReview(envelope());const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='review-'+active+'-v2-'+new Date().toISOString().replaceAll(':','-')+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message('Exported saved judgments. Check that your browser downloaded the file.');}catch(e){message('Export validation failed: '+e.message);}
};
$('import').onchange=async e=>{
  const file=e.target.files[0];if(!file)return;
  try{const review=validateReview(JSON.parse(await file.text()));if(dirty&&!confirm('Discard unsaved changes and import this review?'))return;
    const existing=localStorage.getItem(pilot.pilot_id+':'+review.reviewer_id);
    if(existing&&!confirm('Replace this reviewer workspace with the imported export? Preserve the existing export first.'))return;
    // Preserve the exact imported provenance. Validation happens before any mutation.
    localStorage.setItem(pilot.pilot_id+':'+review.reviewer_id,JSON.stringify(review));
    active=review.reviewer_id;answers=Object.fromEntries(review.annotations.map(x=>[x.id,x]));$('reviewer').value=active;$('human').checked=true;$('independent').checked=true;dirty=false;render();message('Imported validated v2 review. Exposure and context provenance preserved.');
  }catch(err){message('Import rejected: '+err.message+' Existing workspace unchanged.');}finally{e.target.value='';}
};
async function hashText(text){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))).map(x=>x.toString(16).padStart(2,'0')).join('');}
async function verifySnapshot(item,data){if(typeof data.content_original!=='string'||String(data.ID)!==String(item.dataset_id))throw Error('Snapshot ID/content mismatch');const text=data.content_original.trim();if(await hashText(text)!==item.text_sha256)throw Error('Text hash mismatch');texts.set(item.id,text);}
async function beginLoad(){if(dirty&&!confirm('Discard unsaved changes before loading article snapshots?'))return false;dirty=false;loading=true;$('loadRemote').disabled=true;$('files').disabled=true;render();return true;}
function endLoad(){loading=false;$('loadRemote').disabled=false;$('files').disabled=false;render();}
$('loadRemote').onclick=async()=>{
  if(loading||!await beginLoad())return;let count=0,failed=0;
  try{for(const item of pilot.items.filter(x=>x.dataset_id)){try{const url='https://raw.githubusercontent.com/ramybaly/Article-Bias-Prediction/'+pilot.dataset_revision+'/data/jsons/'+encodeURIComponent(item.dataset_id)+'.json';const response=await fetch(url,{signal:AbortSignal.timeout(15000),credentials:'omit',referrerPolicy:'no-referrer'});if(!response.ok)throw Error('Unavailable');await verifySnapshot(item,await response.json());count++;}catch(e){failed++;}$('status').textContent=count+' article snapshots verified; '+failed+' failed.';}}finally{endLoad();$('status').textContent=count+' verified article snapshots loaded; '+failed+' failed. Use the dataset folder if remote downloads are blocked.';}
};
$('files').onchange=async e=>{
  if(loading||!await beginLoad())return;let count=0,failed=0;
  try{const wanted=new Map(pilot.items.filter(x=>x.dataset_id).map(x=>[x.dataset_id+'.json',x]));for(const file of e.target.files){const item=wanted.get(file.name);if(!item)continue;try{await verifySnapshot(item,JSON.parse(await file.text()));count++;}catch(err){failed++;}}}finally{endLoad();$('status').textContent=count+' matching article snapshots verified; '+failed+' failed. No article text was uploaded.';}
};
async function initialize(){let failed=0;for(const item of pilot.items.filter(x=>x.text!==null)){if(await hashText(item.text)===item.text_sha256)texts.set(item.id,item.text);else failed++;}render();if(failed)$('status').textContent=failed+' controlled texts failed hash verification and cannot be reviewed.';}
render();initialize().catch(()=>{$('status').textContent='Hash verification unavailable. Serve this folder on localhost to enable secure browser hashing.';});
