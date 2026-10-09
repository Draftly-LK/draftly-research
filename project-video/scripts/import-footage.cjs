// Only successful, label-checked case recordings enter the active film.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),ts=require('typescript');
const root=path.resolve(__dirname,'..');
const probe=path.join(root,'node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe');
const stateFile=path.join(root,'capture/case-state.json');
const state=fs.existsSync(stateFile)?JSON.parse(fs.readFileSync(stateFile,'utf8')):{};
const manifestFile=path.join(root,'src/film/media.json');
const manifest=JSON.parse(fs.readFileSync(manifestFile,'utf8'));
for(const name of state.checkedClips??[]){
 const file=path.join(root,'public/footage',name+'.mp4');
 const duration=Number(cp.execFileSync(probe,['-v','error','-show_entries','format=duration','-of','csv=p=0',file]).toString().trim());
 manifest.replacements[name+'.mp4']={file:'footage/'+name+'.mp4',duration};
}
const edit=ts.transpileModule(fs.readFileSync(path.join(root,'src/film/edit.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const mod={exports:{}};new Function('module','exports',edit)(mod,mod.exports);
manifest.missingRecordings=[...new Set(mod.exports.ALL_SHOTS.filter(shot=>shot.replacement&&!manifest.replacements[shot.replacement]).map(shot=>shot.replacement))];
fs.writeFileSync(manifestFile,JSON.stringify(manifest,null,2)+'\n');
console.log('Imported '+Object.keys(manifest.replacements).length+' checked product recordings.');
