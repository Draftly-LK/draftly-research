// Real product interactions in the fresh film database, controlled through MCP.
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('D:/projects/Draftly-Project/draftly-platform/frontend/node_modules/@playwright/test');
const {Recorder} = require('./lib.cjs');
const ROOT = path.resolve(__dirname, '..');
const SOURCE = path.join(ROOT, 'out/demo-bundle');
const STATE = path.join(ROOT, 'out/continuation/real-state.json');
const APP = 'http://127.0.0.1:4315', API = 'http://127.0.0.1:4325';
const state = fs.existsSync(STATE) ? JSON.parse(fs.readFileSync(STATE)) : JSON.parse(fs.readFileSync(path.join(ROOT,'capture/case-state.json')));
const save = () => fs.writeFileSync(STATE, JSON.stringify(state,null,2));
let snapshot='', page, rec, browser;
async function mcp(name,args={}) {
 const res = await fetch('http://127.0.0.1:9234',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,arguments:args})});
 const data=await res.json(); if(!res.ok||data.isError)throw new Error(JSON.stringify(data));
 const text=(data.content??[]).filter(c=>c.type==='text').map(c=>c.text).join('\n');
 fs.appendFileSync(path.join(ROOT,'out/continuation/mcp-capture-log.txt'),`\n${name}\n${text}\n`);
 if(text.includes('## Latest page snapshot'))snapshot=text;
 return text;
}
const snap=()=>mcp('take_snapshot',{pageId:1});
function uid(role,name) {
 const found=snapshot.split('\n').filter(l=>l.includes(` ${role} "${name}"`)&&!l.includes('disabled'));
 if(found.length!==1)throw new Error(`Need one enabled ${role} ${name}; got ${found.length}`);
 return found[0].match(/uid=([^ ]+)/)[1];
}
async function click(name,role='button') {
 const locator=page.getByRole(role,{name,exact:true});
 if(await locator.count()===1)await rec.moveTo(locator,{steps:12,pause:80});
 await mcp('click',{pageId:1,uid:uid(role,name),includeSnapshot:true});
 await page.waitForTimeout(400);
 await page.waitForFunction(()=>![...document.querySelectorAll('button')].some(b=>/Saving\.\.\./.test(b.textContent??'')),{},{timeout:60000});
 await snap();
}
async function fields(values) {await mcp('fill_form',{pageId:1,elements:Object.entries(values).map(([name,value])=>({uid:uid('textbox',name),value})),includeSnapshot:true});}
async function open(url) {await mcp('navigate_page',{pageId:1,url,timeout:120000});await page.locator('main').first().waitFor();await page.waitForTimeout(1200);await snap();}
async function api(url,method='GET',body,version) {
 const r=await fetch(API+url,{method,headers:{Authorization:'Bearer film-local','Content-Type':'application/json',...(version?{'If-Match':`"${version}"`}:{})},body:body?JSON.stringify(body):undefined});
 const result=await r.json();if(!r.ok)throw new Error(`${r.status}: ${JSON.stringify(result)}`);return result;
}
async function clean() {if(/synthetic/i.test(await page.locator('body').innerText()))throw new Error('Forbidden fixture label visible');}
const matter=suffix=>`${APP}/matters/${state.matterId}${suffix??''}`;
const stages={
 async draftReview() {
  await open(matter('/drafts/'+state.formId));
  await page.getByRole('document',{name:'Gazette form'}).waitFor();
  const panel=page.locator('main aside');await panel.waitFor();
  await rec.click(page.getByRole('button',{name:/\(i\) Parcel No\.:/}),{after:1000});
  await rec.hold(900);await snap();console.log((await panel.innerText()).slice(0,1300));
  await rec.start('case-001-draft-current');await rec.hold(1300);
  await rec.click(panel.getByRole('button',{name:'Next',exact:true}),{after:1100});
  const confirm=panel.getByRole('button',{name:'Confirm',exact:true});
  if(await confirm.count()&&await confirm.isEnabled())await rec.click(confirm,{after:1100});
  await rec.hold(4300);await clean();await snap();await rec.stop();
 },
 async approveInstrument() {
  const inbox=await api(`/api/v1/matters/${state.matterId}/document-inbox`);
  const doc=inbox.documents.find(d=>d.classId==='rta.doc.prescribed_instrument');
  if(!doc)throw new Error('No actual instrument document');
  const review=await api(`/api/v1/detected-documents/${doc.id}/review`);
  const expected=JSON.parse(fs.readFileSync(path.resolve(ROOT,'../../draftly-platform/inputs/case-001/expected-fields.json'),'utf8'))['source-004-form8-instrument-of-transfer-with-stamp-receipt.pdf'].fields;
  const mismatch=review.candidates.filter(c=>!(c.key in expected)||String(c.editedValue??c.candidateValue)!==String(expected[c.key]));
  if(mismatch.length)throw new Error('Instrument candidates differ from supplied reviewed transcription: '+mismatch.map(c=>c.key).join(', '));
  await open(matter(`/documents/${doc.id}/review`));
  await page.getByRole('heading',{name:'Candidate fields',exact:true}).waitFor();
  const confirm=page.getByRole('button',{name:'Confirm type',exact:true});
  if(await confirm.count())await rec.click(confirm,{after:700});
  const approveAll=page.getByRole('button',{name:/^Approve all \d+ fields/});
  if(await approveAll.count()){
   await approveAll.scrollIntoViewIfNeeded();await rec.start('case-001-accept-instrument');await rec.hold(900);
   await rec.click(approveAll,{after:1000});await approveAll.waitFor({state:'hidden',timeout:60000});
   await rec.hold(3500);await clean();await rec.stop();
  }
  const result=await api(`/api/v1/detected-documents/${doc.id}/review`);
  console.log('Actual instrument candidate approvals: '+result.candidates.filter(c=>c.reviewState==='approved').length+'/'+result.candidates.length);
 },
 async approveTitle() {
  await open(matter(`/documents/${state.titleDocumentId}/review`));
  const parcel=page.getByLabel('Parcel no',{exact:true});await parcel.waitFor();
  const confirmType=page.getByRole('button',{name:'Confirm type',exact:true});
  if(await confirmType.count())await rec.click(confirmType,{after:900});
  await parcel.scrollIntoViewIfNeeded();await page.waitForTimeout(700);
  await rec.start('case-001-accept-facts');await rec.hold(1000);
  const row=parcel.locator('..').locator('..');
  const approve=row.getByRole('button',{name:'Approve',exact:true});
  if(await approve.isEnabled())await rec.click(approve,{after:1100});
  await snap();await rec.hold(3800);await clean();await rec.stop();
  const all=page.getByRole('button',{name:/^Approve all \d+ fields/});
  if(await all.count())await rec.click(all,{after:1500});
  await snap();save();
 },
 async inspect() {
  for(const [route,name] of [['','overview-current'],['/facts','facts-current'],['/checks','checks-current']]){
   await open(matter(route));await rec.start(`case-001-${name}`);await rec.hold(2600);await clean();await rec.stop();
  }
 },
 async draft() {
  await open(matter('/drafts'));await snap();console.log((await page.locator('main').innerText()).slice(0,2000));
  const newDraft=page.getByRole('button',{name:'New draft',exact:true});
  if(await newDraft.isEnabled()){
   await rec.click(newDraft,{after:1000});await page.waitForURL(/drafts\/frm_/,{timeout:60000});
   state.formId=page.url().match(/drafts\/(frm_[^/]+)/)[1];save();
  } else {
   console.log('New draft unavailable; captured actual state.');return;
  }
  await page.getByRole('document',{name:'Gazette form'}).waitFor({timeout:120000});
  await snap();await rec.start('case-001-draft-current');await rec.hold(1400);
  const extent=page.getByRole('button',{name:/^\(i\) Extent/});
  if(await extent.count())await rec.click(extent,{after:1600});
  await rec.hold(5000);await clean();await snap();await rec.stop();
 },
};
(async()=>{
 browser=await chromium.connectOverCDP('http://127.0.0.1:9223');page=browser.contexts()[0].pages().find(p=>p.url().startsWith(APP))??browser.contexts()[0].pages()[0];
 await page.setViewportSize({width:1920,height:1080});page.setDefaultTimeout(45000);rec=new Recorder(page);await rec.init();
 for(const name of process.argv.slice(2)){console.log('Recording '+name);await stages[name]();}
 await rec.session.detach();
})().catch(async err=>{
 console.error(err.stack);try{await rec.stop();await page.screenshot({path:path.join(ROOT,'out/continuation/capture-failure.png')});await snap();}catch{}
 process.exitCode=1;
}).finally(()=>{if(browser)browser.close().catch(()=>{});});
