const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),ts=require('typescript');
const root=path.resolve(__dirname,'..');
const media=JSON.parse(fs.readFileSync(path.join(root,'src/film/media.json'),'utf8'));
const source=fs.readFileSync(path.join(root,'src/film/edit.ts'),'utf8');
const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const mod={exports:{}};new Function('module','exports',js)(mod,mod.exports);
const {ALL_SHOTS,TOTAL_SECONDS}=mod.exports;
const missing=[...new Set(ALL_SHOTS.filter(s=>s.replacement&&!media.replacements[s.replacement]).map(s=>s.replacement))];
for(const [name,clip] of Object.entries(media.replacements)){
 if(!clip.file.startsWith('footage/')||!fs.existsSync(path.join(root,'public',clip.file)))throw new Error(`Missing imported clip: ${name}`);
 if(!Number.isFinite(clip.duration)||clip.duration<=0)throw new Error(`Invalid duration: ${name}`);
}
for(const file of ['edit.ts','Opening.tsx','Scenes.tsx','AppShot.tsx','Film.tsx']){
 if(/synthetic/i.test(fs.readFileSync(path.join(root,'src/film',file),'utf8')))throw new Error('Forbidden display label in active film');
}
const evidence=JSON.parse(fs.readFileSync(path.join(root,'src/film/evidence-sources.json'),'utf8'));
const bundle=path.resolve(root,'../../draftly-platform/inputs/case-001');
const originals=fs.readdirSync(bundle).filter(n=>n.endsWith('.pdf'));
for(const record of evidence){
 const original=originals.find(n=>n.startsWith('source-'+String(record.sourceNumber).padStart(3,'0')+'-'));
 const digest=crypto.createHash('sha256').update(fs.readFileSync(path.join(bundle,original))).digest('hex');
 if(digest!==record.sha256)throw new Error('Original source checksum changed: '+record.sourceNumber);
}
// Inspect the source manifest, not source text or private field values.
const assets=['title','instrument','survey','resolution','payment','identity','instrument-cover','title-extent','instrument-extent','survey-extent'];
for(const name of assets)if(!fs.existsSync(path.join(root,'public/evidence',name+'.png')))throw new Error('Missing evidence display copy: '+name);
console.log(`Edit: ${TOTAL_SECONDS}s. Voiceover: off. Caption estimation: off. Imported clips: ${Object.keys(media.replacements).length}.`);
console.log(missing.length?'Recordings still required:\n'+missing.map(n=>'  public/footage/'+n).join('\n'):'All active recording slots are filled.');
if(process.argv.includes('--final')&&missing.length)throw new Error('Final render is waiting for the listed recordings. Use render:review for the current edit.');
