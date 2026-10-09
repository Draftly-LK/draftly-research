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
 async research(){
  await open(APP+'/research');await rec.start('case-001-long-research-scope');await rec.hold(2300);
  await rec.click(page.getByRole('button',{name:'All sources',exact:true}),{after:2400});
  await rec.click(page.getByRole('button',{name:'Case law',exact:true}),{after:2400});
  await rec.click(page.getByRole('button',{name:'Statutes & amendments',exact:true}),{after:2400});await clean();await snap();await rec.stop();
  await rec.start('case-001-long-research-gap');
  await rec.type(page.getByRole('textbox',{name:'Ask a legal research question',exact:true}),'What does the Registration of Title Act require when transferring a registered land parcel?',{delay:30});
  await rec.hold(1000);await rec.click(page.getByRole('button',{name:'Send',exact:true}),{after:1800});
  await page.getByRole('button',{name:'Send',exact:true}).waitFor({timeout:45000});
  await rec.hold(5500);console.log((await page.locator('main').first().innerText()).slice(0,10000));await clean();await snap();await rec.stop();
 },
 async manifest(){
  await open(matter('/exports'));await rec.start('case-001-long-manifest');await rec.hold(1500);
  await rec.click(page.getByRole('button',{name:'Create export',exact:true}),{after:1000});
  console.log((await page.locator('main').first().innerText()).slice(0,14000));await snap();
  await page.getByRole('combobox').nth(0).selectOption(state.formId);
  await rec.click(page.locator('input[value="WORKING_DRAFT_MANIFEST"]'),{after:700});
  await rec.hold(2000);await snap();
  const buttons=page.getByRole('button',{name:'Create export',exact:true});
  await rec.click(buttons.last(),{after:2000});await rec.hold(4200);await clean();await snap();await rec.stop();
 },
 async overviewProbe(){await open(matter(''));console.log((await page.locator('main').first().innerText()).slice(0,15000));await snap();},

 async researchProbe(){await open(APP+'/research');console.log((await page.locator('main').first().innerText()).slice(0,14000));await snap();},
 async library(){
  await open(APP+'/library');await rec.start('case-001-long-library');await rec.hold(2800);
  await rec.type(page.getByRole('textbox',{name:'Search legal sources'}),'Registration of Title',{delay:65});await rec.hold(5000);
  await clean();await snap();await rec.stop();
 },
 async survey(){
  const inbox=await api(`/api/v1/matters/${state.matterId}/document-inbox`);const d=inbox.documents.find(x=>x.classId==='rta.doc.survey_plan');
  await open(matter('/documents/'+d.id+'/review'));await page.getByRole('heading',{name:'Candidate fields',exact:true}).waitFor();
  await rec.start('case-001-long-survey');await rec.hold(3400);await rec.scroll(390);await rec.hold(4200);
  const page2=page.getByRole('button',{name:'Page 2',exact:true});if(await page2.count())await rec.click(page2,{after:3600});
  await clean();await snap();await rec.stop();
 },
 async missing(){
  await open(matter('/missing-documents'));console.log((await page.locator('main').first().innerText()).slice(0,6500));
  await rec.start('case-001-long-missing');await rec.hold(3500);await rec.scroll(440);await rec.hold(4000);await rec.scroll(440);await rec.hold(4000);
  await clean();await snap();await rec.stop();
 },
 async approval(){
  await open(matter('/drafts/'+state.formId+'/approval'));await rec.start('case-001-long-approval');await rec.hold(3700);await rec.scroll(450);await rec.hold(4500);
  await clean();await snap();await rec.stop();
 },
 async exportProbe(){await open(matter('/exports'));console.log((await page.locator('main').first().innerText()).slice(0,18000));await snap();},

 async draftCreate(){
  await open(matter('/drafts'));await snap();
  await rec.start('case-001-long-draft-create');await rec.hold(1700);
  await rec.click(page.getByRole('button',{name:'New draft',exact:true}),{after:1000});
  await page.waitForURL(/drafts\/frm_/,{timeout:60000});state.formId=page.url().match(/drafts\/(frm_[^/]+)/)[1];save();
  await page.getByRole('document',{name:'Gazette form'}).waitFor({timeout:60000});
  await rec.hold(2400);await rec.scroll(440);await rec.hold(3500);await clean();await snap();await rec.stop();
 },
 async draftReviewLong(){
  await open(matter('/drafts/'+state.formId));await page.getByRole('document',{name:'Gazette form'}).waitFor();
  await rec.click(page.getByRole('button',{name:/\(i\) Parcel No\.:/}),{after:1000});
  const panel=page.locator('main aside');await rec.start('case-001-long-draft-review');await rec.hold(2200);
  await rec.click(panel.getByRole('button',{name:'Confirm',exact:true}),{after:2000});
  await rec.click(panel.getByRole('button',{name:'Next',exact:true}),{after:2200});
  await rec.click(panel.getByRole('button',{name:'Confirm',exact:true}),{after:3000});
  await clean();await snap();await rec.stop();
 },
 async draftGaps(){
  await open(matter('/drafts/'+state.formId));await page.getByRole('document',{name:'Gazette form'}).waitFor();
  await rec.click(page.getByRole('button',{name:/\(d\) Village or Town:/}),{after:800});
  await rec.start('case-001-long-draft-gaps');await rec.hold(3300);
  await rec.click(page.getByRole('button',{name:/\(f\) Assessment No\.:/}),{after:3300});
  await rec.click(page.getByRole('button',{name:/Consideration.*\(b\) Rs\. \(in letters\):/}),{after:3500});
  await clean();await snap();await rec.stop();
 },
 async preflight(){
  await open(matter('/drafts/'+state.formId));
  await page.getByRole('heading',{name:'Form readiness',exact:true}).scrollIntoViewIfNeeded();await rec.hold(800);
  await rec.start('case-001-long-preflight');await rec.hold(3000);
  const run=page.getByRole('button',{name:'Run preflight',exact:true});await rec.click(run,{after:1500});
  await page.getByRole('heading',{name:'Form readiness',exact:true}).scrollIntoViewIfNeeded();await rec.hold(5500);
  await clean();await snap();await rec.stop();
 },
 async facts(){
  await open(matter('/facts'));await rec.start('case-001-long-facts');await rec.hold(3300);
  await rec.scroll(520);await rec.hold(3500);await rec.scroll(520);await rec.hold(3500);
  await rec.scroll(-1040);await rec.hold(2200);await clean();await snap();await rec.stop();
 },
 async checks(){
  await open(matter('/checks'));await rec.start('case-001-long-checks');await rec.hold(3500);
  await rec.scroll(480);await rec.hold(3500);await rec.scroll(460);await rec.hold(3500);
  await clean();await snap();await rec.stop();
 },
 async records(){
  for(const [url,name] of [[matter('/exports'),'exports'],[APP+'/history','history'],[matter('/assistant'),'assistant'],[matter(''),'overview']]){
   await open(url);await rec.start('case-001-long-'+name);await rec.hold(3500);
   await rec.scroll(420);await rec.hold(4200);await clean();await snap();await rec.stop();
  }
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
