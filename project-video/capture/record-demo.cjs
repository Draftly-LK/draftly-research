// Real product interactions in the fresh film database, controlled through MCP.
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('D:/projects/Draftly-Project/draftly-platform/frontend/node_modules/@playwright/test');
const {Recorder} = require('./lib.cjs');
const ROOT = path.resolve(__dirname, '..');
const SOURCE = path.join(ROOT, 'out/demo-bundle');
const STATE = path.join(ROOT, 'out/continuation/demo-state.json');
const APP = 'http://127.0.0.1:4315', API = 'http://127.0.0.1:4325';
const state = fs.existsSync(STATE) ? JSON.parse(fs.readFileSync(STATE)) : {};
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
 async prepareRemaining() {
  const inbox=await api(`/api/v1/matters/${state.matterId}/document-inbox`);
  for(const source of inbox.sourceFiles.filter(s=>s.state==='STORED')){
   const run=await api(`/api/v1/source-files/${source.id}/process`,'POST',undefined,source.version);
   console.log('Actual remaining process result: '+JSON.stringify({state:run.state,failureReason:run.failureReason}));
  }
 },
 async intake() {
  await api('/api/v1/me/provision','POST');
  await open(APP+'/new');await click('Continue with RTA');
  await fields({'Matter reference':'DEMO-001 · Workflow film','Optional client reference':'Illustrative conveyancing matter'});await click('Next');
  await click('Yes');await click('Next');
  const category=snapshot.split('\n').find(l=>l.includes('button "Ownership change'));
  await mcp('click',{pageId:1,uid:category.match(/uid=([^ ]+)/)[1],includeSnapshot:true});await snap();await click('Next');
  const sale=snapshot.split('\n').find(l=>l.includes('button "Transfer by sale'));
  await mcp('click',{pageId:1,uid:sale.match(/uid=([^ ]+)/)[1],includeSnapshot:true});await snap();await click('Next');
  await click('Whole registered parcel');await click('Ordinary parcel');
  const unknown=page.getByRole('checkbox',{name:'Unknown',exact:true});
  if(await unknown.count())await rec.click(unknown);
  const dispute=page.getByRole('group',{name:/active dispute/}).getByRole('button',{name:'No',exact:true});
  await rec.click(dispute);await snap();await click('Next');await click('Next');
  await rec.start('workflow-demo-upload');
  await page.locator('input[type=file]').setInputFiles(fs.readdirSync(SOURCE).filter(f=>f.endsWith('.pdf')).map(f=>path.join(SOURCE,f)));
  await page.waitForTimeout(1000);await snap();await click('Create a matter');
  await page.waitForURL(/\/matters\/mat_/,{timeout:120000});state.matterId=page.url().match(/matters\/(mat_[^/]+)/)[1];save();
  await page.waitForTimeout(2000);await clean();await rec.stop();console.log('DEMO matter created: '+state.matterId);
 },
 async process() {
  await open(matter('/processing'));await rec.start('workflow-demo-process');
  await page.waitForTimeout(600);
  while(await page.getByRole('button',{name:'Process',exact:true}).count()) {
   const locator=page.getByRole('button',{name:'Process',exact:true}).first();
   await rec.click(locator,{after:600});
   await page.waitForLoadState('networkidle',{timeout:120000}).catch(()=>{});await snap();
  }
  await page.waitForTimeout(1600);await clean();await rec.stop();state.inbox=await api(`/api/v1/matters/${state.matterId}/document-inbox`);save();
 },
 async review() {
  state.inbox=await api(`/api/v1/matters/${state.matterId}/document-inbox`);
  const title=state.inbox.documents.find(d=>/title_certificate/i.test(d.classId??''));
  if(!title)throw new Error('No actual prepared certificate');state.titleDocumentId=title.id;save();
  await open(matter(`/documents/${title.id}/review`));await page.getByLabel('Extent',{exact:true}).waitFor();
  await rec.start('workflow-demo-review');await page.waitForTimeout(500);
  await fields({'Extent':'0.0159 hectares'});
  const parent=page.getByLabel('Extent',{exact:true}).locator('..').locator('..');
  await rec.click(parent.getByRole('button',{name:'Approve',exact:true}),{after:700});await snap();
  await page.waitForTimeout(4500);await clean();await rec.stop();
 },
 async inspect() {
  for(const [route,name] of [['','overview'],['/facts','facts'],['/checks','checks']]){
   await open(matter(route));await rec.start(`workflow-demo-${name}`);await page.waitForTimeout(2200);await rec.scroll(220);await page.waitForTimeout(1800);await clean();await rec.stop();
  }
 },
 async draft() {
  await open(matter('/drafts'));await rec.start('workflow-demo-draft');await page.waitForTimeout(500);await click('New draft');
  await page.waitForURL(/drafts\/frm_/,{timeout:90000});state.formId=page.url().match(/drafts\/(frm_[^/]+)/)[1];save();
  await page.getByRole('document',{name:'Gazette form'}).waitFor({timeout:120000});
  await page.waitForTimeout(1200);await snap();
  const field=page.getByRole('button',{name:/^\(i\) Extent/});await rec.click(field,{after:1800});await snap();
  await page.waitForTimeout(3800);await clean();await rec.stop();
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
