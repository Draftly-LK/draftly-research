// Record the actual interface against the isolated real-service film database.
// Source PDFs are unchanged. Candidate values are prepared from expected-fields.
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('D:/projects/Draftly-Project/draftly-platform/frontend/node_modules/@playwright/test');
const {Recorder}=require('./lib.cjs');
const ROOT=path.resolve(__dirname,'..');
const SOURCE=path.resolve(ROOT,'../../draftly-platform/inputs/case-001');
const STATE=path.join(__dirname,'case-state.json');
const state=fs.existsSync(STATE)?JSON.parse(fs.readFileSync(STATE,'utf8')):{};
const save=(newMatter=false)=>{const current=fs.existsSync(STATE)?JSON.parse(fs.readFileSync(STATE,'utf8')):{};state.checkedClips=[...new Set([...(current.checkedClips??[]),...(state.checkedClips??[])])];if(!newMatter&&current.matterId)state.matterId=current.matterId;fs.writeFileSync(STATE,JSON.stringify({...current,...state},null,2));};
const APP='http://127.0.0.1:4311', API='http://127.0.0.1:4321';
async function api(url,method='GET',body,version){
 const r=await fetch(API+url,{method,headers:{Authorization:'Bearer film-local','Content-Type':'application/json',...(version?{'If-Match':`"${version}"`}:{})},body:body?JSON.stringify(body):undefined});
 const result=await r.json();
 if(!r.ok)throw new Error(`${r.status}: ${result.error?.code??'API request failed'}`);
 return result;
}
let page,rec,browser,cleanClip=false;
const role=(r,name)=>page.getByRole(r,{name,exact:true});
const matter=(suffix='')=>`${APP}/matters/${state.matterId}${suffix}`;
async function open(url){await page.goto(url,{waitUntil:'load',timeout:120000});await page.locator('main').first().waitFor({timeout:120000});await page.waitForTimeout(2200);}
async function clean(){if(/synthetic/i.test(await page.locator('body').innerText()))throw new Error('Forbidden fixture label visible in recording');cleanClip=true;}
const stages={
 async prepare(){
  const inbox=await api(`/api/v1/matters/${state.matterId}/document-inbox`);
  for(const source of inbox.sourceFiles.filter(s=>s.state!=='PROCESSED')){
   const run=await api(`/api/v1/source-files/${source.id}/process`,'POST',undefined,source.version);
   console.log('Local prepared processing: '+run.state+' · '+(run.failureReason??'complete'));
  }
 },
 async intake(){
  await open(APP+'/new');await role('button','Continue with RTA').waitFor();
  await rec.start('case-001-intake');await rec.hold(1800);
  await rec.click(role('button','Continue with RTA'));
  await rec.type(page.getByLabel('Matter reference'),'CASE-001 · Source review',{delay:30});
  await rec.type(page.getByLabel('Optional client reference'),'Approved client bundle',{delay:25});
  await rec.click(role('button','Next'));
  await rec.click(role('button','Yes'));
  await rec.hold(1200);await rec.click(role('button','Next'));
  await rec.click(page.getByRole('button',{name:/^Ownership change/}));
  await rec.hold(1200);await rec.click(role('button','Next'));
  await rec.click(page.getByRole('button',{name:/^Transfer by sale/}));
  await rec.hold(1800);await clean();await rec.stop();
  await rec.start('case-001-scope');await rec.click(role('button','Next'));
  await rec.click(role('button','Whole registered parcel'));
  await rec.click(role('button','Ordinary parcel'));
  // The file's party relationships and dispute state need practitioner input.
  const party=page.getByRole('checkbox',{name:'Unknown',exact:true});
  if(await party.count())await rec.click(party);
  await rec.click(page.getByRole('group',{name:/active dispute/}).getByRole('button',{name:'Unknown',exact:true}));
  await rec.hold(2500);await rec.click(role('button','Next'));
  await page.getByText('Step 6 of 7').waitFor();await rec.hold(4000);await clean();await rec.stop();
  await rec.start('case-001-attach');await rec.click(role('button','Next'));
  await page.locator('input[type=file]').setInputFiles(fs.readdirSync(SOURCE).filter(f=>f.endsWith('.pdf')).map(f=>path.join(SOURCE,f)));
  await rec.hold(3500);await clean();await rec.click(role('button','Create a matter'));
  await page.waitForURL(/\/matters\/mat_/, {timeout:120000});
  state.matterId=page.url().match(/matters\/(mat_[^/]+)/)[1];save(true);
  await rec.hold(3000);await clean();await rec.stop();
 },
 async attach(){
  await open(matter('/documents'));
  await rec.start('case-001-attach');
  await page.locator('input[type=file]').setInputFiles(fs.readdirSync(SOURCE).filter(f=>f.endsWith('.pdf')).map(f=>path.join(SOURCE,f)));
  await rec.hold(4500);await clean();
  console.log((await page.locator('main').first().innerText()).slice(0,1700));
  await rec.stop();
 },
 async process(){
  await open(matter('/processing'));
  await rec.start('case-001-process');await rec.hold(2000);
  while(await role('button','Process').count()){
   await rec.click(role('button','Process').first(),{after:600});
   await page.waitForLoadState('networkidle',{timeout:120000}).catch(()=>{});
   await rec.hold(900);
  }
  await rec.scroll(300);await rec.hold(2200);
  await clean();await rec.hold(2500);await rec.stop();
  state.inbox=await api(`/api/v1/matters/${state.matterId}/document-inbox`);save();
 },
 async review(){
  const inbox=await api(`/api/v1/matters/${state.matterId}/document-inbox`);
  const title=inbox.documents.find(d=>/TITLE_CERTIFICATE/.test(d.classId??''))??inbox.documents.find(d=>/title/i.test(d.classId??''));
  if(!title)throw new Error('No prepared certificate review available');
  state.titleDocumentId=title.id;save();
  await open(matter(`/documents/${title.id}/review`));
  await page.getByLabel('Extent',{exact:true}).waitFor();await clean();
  await rec.start('case-001-review');await rec.hold(2400);
  await rec.moveTo(page.getByLabel('Extent',{exact:true}),{pause:2200});
  const extent=page.getByLabel('Extent',{exact:true}).locator('..').locator('..');
  await rec.click(extent.getByRole('button',{name:'Approve',exact:true}),{after:2000});
  await clean();await rec.hold(2800);await rec.stop();
  await open(matter(`/documents/${title.id}/review`));
  await rec.start('case-001-reopen');await rec.hold(2800);
  await rec.moveTo(page.getByLabel('Extent',{exact:true}),{pause:2600});
  await clean();await rec.stop();
 },
 async inspect(){await open(matter('/facts'));await rec.start('case-001-facts');await rec.hold(2800);await clean();await rec.scroll(350);await rec.hold(3000);await rec.stop();},
 async checks(){await open(matter('/checks'));await rec.start('case-001-checks');await rec.hold(4000);await clean();await rec.scroll(350);await rec.hold(3000);await rec.stop();},
 async draft(){
  await open(matter('/drafts'));await role('button','New draft').waitFor();
  await rec.start('case-001-draft');await rec.hold(1800);await rec.click(role('button','New draft'));
  await page.waitForURL(/drafts\/frm_/,{timeout:60000});state.formId=page.url().match(/drafts\/(frm_[^/]+)/)[1];save();
  await page.getByRole('document',{name:'Gazette form'}).waitFor();await rec.hold(2500);
  const field=page.getByRole('button',{name:/^\(i\) Extent/});await rec.moveTo(field,{pause:1200});await rec.click(field,{after:2000});
  await clean();await rec.stop();
 },
 async draftField(){
  await open(matter('/drafts/'+state.formId));await page.getByRole('document',{name:'Gazette form'}).waitFor();
  await rec.start('case-001-draft-field');await rec.hold(1500);
  await rec.click(page.getByRole('button',{name:/^\(i\) Extent/}),{after:2600});await clean();await rec.stop();
  await rec.start('case-001-draft-confirm');
  const confirm=page.getByRole('complementary').getByRole('button',{name:'Confirm',exact:true});
  if(await confirm.isEnabled())await rec.click(confirm,{after:2500});
  await clean();await rec.hold(2300);await rec.stop();
 },
 async status(){
  await open(matter('/drafts/'+state.formId));
  const run=role('button','Run preflight');await run.waitFor();await rec.moveTo(run,{pause:700});
  await rec.start('case-001-preflight');await rec.hold(1800);await rec.click(run,{after:2800});await clean();await rec.hold(2500);await rec.stop();
  await open(matter('/exports'));await rec.start('case-001-manifest');await rec.hold(3000);await clean();await rec.hold(1800);await rec.stop();
  await rec.start('case-001-review-record');await rec.scroll(400);await clean();await rec.hold(3000);await rec.stop();
 },
 async research(){await open(APP+'/research');await rec.start('case-001-research-scope');await rec.hold(1500);await rec.click(role('button','New conversation'));await rec.click(role('button','All sources'));await rec.hold(1500);await rec.click(role('button','Statutes & amendments'));await rec.hold(1500);await rec.click(role('button','Case law'));await rec.hold(1500);await rec.click(role('button','Statutes & amendments'));await clean();await rec.hold(1500);await rec.stop();},
 async library(){await open(APP+'/library');await rec.start('case-001-legal-sources');await rec.hold(2200);console.log((await page.locator('main').innerText()).slice(0,1000));await clean();await rec.type(page.getByRole('textbox',{name:'Search legal sources'}),'Registration of Title',{delay:55});await rec.hold(2800);await rec.stop();},
};
(async()=>{
 await api('/api/v1/me/provision','POST');
 browser=await chromium.launch({channel:'chromium'});page=await browser.newPage({viewport:{width:1920,height:1080}});page.setDefaultTimeout(45000);rec=new Recorder(page);await rec.init();
 const originalStart=rec.start.bind(rec),originalStop=rec.stop.bind(rec);
 rec.start=async name=>{cleanClip=false;const current=fs.existsSync(STATE)?JSON.parse(fs.readFileSync(STATE,'utf8')):{};current.checkedClips=(current.checkedClips??[]).filter(clip=>clip!==name);state.checkedClips=(state.checkedClips??[]).filter(clip=>clip!==name);fs.writeFileSync(STATE,JSON.stringify(current,null,2));await originalStart(name);};
 rec.stop=async()=>{const name=rec.clip?.name;await originalStop();if(cleanClip&&name){state.checkedClips=[...new Set([...(state.checkedClips??[]),name])];save();}};
 for(const stage of process.argv.slice(2)){console.log('Recording '+stage);await stages[stage]();}
 await browser.close();
})().catch(async e=>{console.error(e.message);cleanClip=false;try{await rec.stop();await page.screenshot({path:path.join(ROOT,'out','capture-failure.png')});}catch{}try{await browser.close();}catch{}process.exitCode=1;});
