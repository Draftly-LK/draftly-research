// Fast, resumable export: Remotion renders designed frames and authored motion;
// FFmpeg places the original recordings inside those frames at natural speed.
const fs=require('node:fs');const path=require('node:path');const crypto=require('node:crypto');
const{execFileSync}=require('node:child_process');
const{bundle}=require('@remotion/bundler');const{getCompositions,renderMedia,renderStill}=require('@remotion/renderer');
const{Input,ALL_FORMATS,FilePathSource}=require('mediabunny');
const root=path.resolve(__dirname,'..');const out=path.join(root,'out/long-film');fs.mkdirSync(out,{recursive:true});
const shots=JSON.parse(fs.readFileSync(path.join(root,'src/long-film/edit.json'),'utf8'));
const editorialOnly=process.argv.includes('--editorial');const previews=process.argv.includes('--stills');
const only=process.argv.find(a=>a.startsWith('--only='))?.slice(7);
const ff=(args)=>execFileSync('ffmpeg',['-hide_banner','-loglevel','error','-y',...args],{stdio:'inherit'});
const encode=['-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-r','30','-video_track_timescale','15360'];
async function metadata(file){const input=new Input({formats:ALL_FORMATS,source:new FilePathSource(file)});try{const v=await input.getPrimaryVideoTrack();return{duration:await input.computeDuration(),width:v.displayWidth,height:v.displayHeight};}finally{input.dispose();}}
async function connect(){
 const base=path.join(root,'node_modules/@remotion/renderer/dist/browser');
 const{HeadlessBrowser}=require(path.join(base,'Browser.js'));const{Connection}=require(path.join(base,'Connection.js'));const{NodeWebSocketTransport}=require(path.join(base,'NodeWebSocketTransport.js'));
 const info=await(await fetch('http://127.0.0.1:9223/json/version')).json();const t=await NodeWebSocketTransport.create(info.webSocketDebuggerUrl);const c=new Connection(t);
 const b=new HeadlessBrowser({connection:c,defaultViewport:{width:1920,height:1080},runner:{closeProcess:async()=>{}}});await c.send('Target.setDiscoverTargets',{discover:true});return b;
}
(async()=>{
 if(shots.reduce((n,s)=>n+s.seconds,0)!==600)throw new Error('Timeline must be exactly 600 seconds');
 const media={};for(const s of shots.filter(s=>s.kind==='recording')){const f=path.join(root,'public',s.file);if(!fs.existsSync(f)){if(editorialOnly)continue;throw new Error('Missing recording '+s.file);}media[s.file]=await metadata(f);}
 fs.writeFileSync(path.join(root,'src/long-film/media.json'),JSON.stringify(media,null,2));
 const browser=await connect();
 try{
  const serveUrl=await bundle({entryPoint:path.join(root,'src/index.ts'),publicDir:path.join(root,'public')});
  const template=(await getCompositions(serveUrl,{browserInstance:browser})).find(c=>c.id==='DraftlyLongShot');
  const common=fs.readFileSync(path.join(root,'src/long-film/FullFilm.tsx'),'utf8');
  for(let i=0;i<shots.length;i++){
   const shot=shots[i];if(only&&!only.split(',').includes(shot.id))continue;if(editorialOnly&&['recording','opening'].includes(shot.kind))continue;
   const name=String(i).padStart(2,'0')+'-'+shot.id;const destination=path.join(out,name+'.mp4');const stamp=destination+'.json';
   const inputProps={shot,plateOnly:false};const composition={...template,durationInFrames:Math.round(shot.seconds*30),props:inputProps};
   const dependencies=shot.kind==='recording'?[common,fs.statSync(path.join(root,'public',shot.file)).mtimeMs,media[shot.file]]:[common,...['Editorial.tsx','ResearchEditorial.tsx'].map(f=>fs.readFileSync(path.join(root,'src/long-film',f),'utf8'))];
   if(shot.kind==='opening')dependencies.push(fs.readFileSync(path.join(root,'src/film/Opening.tsx'),'utf8'));
   if(shot.kind==='source'){const source=shot.source.includes('/')?shot.source:`evidence/${shot.source}.png`;dependencies.push(fs.statSync(path.join(root,'public',source)).mtimeMs);}
   if(shot.kind==='bundle')dependencies.push(fs.statSync(path.join(root,'public/evidence/identity.png')).mtimeMs);
   const hash=crypto.createHash('sha256').update(JSON.stringify([shot,dependencies,fs.readFileSync(__filename,'utf8')])).digest('hex');
   if(previews){await renderStill({serveUrl,composition,browserInstance:browser,inputProps,frame:Math.min(composition.durationInFrames-1,Math.round((shot.animateSeconds??2)*30)),output:path.join(out,name+'.png')});console.log('Preview '+shot.id);continue;}
   if(fs.existsSync(destination)&&fs.existsSync(stamp)&&JSON.parse(fs.readFileSync(stamp)).hash===hash){console.log('Cached '+shot.id);continue;}
   console.log(`Export ${i+1}/${shots.length} ${shot.id} (${shot.seconds}s)`);
   if(shot.kind==='opening'){
    const head=path.join(out,'opening-aligned-head.mp4');const normalizedHead=path.join(out,'opening-aligned-head-normalized.mp4');const tail=path.join(out,'opening-preserved-tail.mp4');
    const headStamp=head+'.json';const headHash=crypto.createHash('sha256').update(['Opening.tsx','style.tsx'].map(f=>fs.readFileSync(path.join(root,'src/film',f),'utf8')).join('\n')).digest('hex');
    if(!fs.existsSync(head)||!fs.existsSync(headStamp)||JSON.parse(fs.readFileSync(headStamp)).hash!==headHash){
     await renderMedia({serveUrl,composition,browserInstance:browser,inputProps,frameRange:[0,209],outputLocation:head,codec:'h264',crf:18,x264Preset:'veryfast',concurrency:4,muted:true});
     fs.writeFileSync(headStamp,JSON.stringify({hash:headHash}));
    }
    ff(['-i',head,'-an','-c:v','copy','-video_track_timescale','15360',normalizedHead]);
    ff(['-ss','7','-i',path.join(root,'out/draftly-opening.mp4'),'-frames:v','1140',...encode,tail]);
    const openingList=path.join(out,'opening-concat.txt');fs.writeFileSync(openingList,"file 'opening-aligned-head-normalized.mp4'\nfile 'opening-preserved-tail.mp4'\n");
    ff(['-f','concat','-safe','0','-i',openingList,'-an','-c:v','copy','-video_track_timescale','15360',destination]);
   }else if(shot.kind==='recording'){
    const plate=path.join(out,name+'-plate.png');const plateProps={shot,plateOnly:true};await renderStill({serveUrl,composition:{...composition,props:plateProps},browserInstance:browser,inputProps:plateProps,frame:30,output:plate});
    const start=shot.start??0;const end=Math.min(shot.end??Infinity,media[shot.file].duration);const[x,y,w]=shot.crop??[260,180,1580];const h=Math.floor((740*w/1780)/2)*2;
    if(start>=end||x+w>1920||y+h>1080)throw new Error('Invalid source crop/range '+shot.id);
    const filter=`[1:v]trim=start=${start}:end=${end},setpts=PTS-STARTPTS,crop=${w}:${h}:${x}:${y},scale=1780:740:flags=lanczos,fps=30,tpad=stop_mode=clone:stop_duration=${shot.seconds}[ui];[0:v][ui]overlay=70:215:shortest=1,format=yuv420p[v]`;
    ff(['-loop','1','-framerate','30','-i',plate,'-i',path.join(root,'public',shot.file),'-filter_complex',filter,'-map','[v]','-frames:v',String(shot.seconds*30),...encode,destination]);
   }else{
    const animate=Math.min(shot.seconds,shot.animateSeconds??shot.seconds);const animation=path.join(out,name+'-motion.mp4');
    await renderMedia({serveUrl,composition,browserInstance:browser,inputProps,frameRange:[0,Math.round(animate*30)-1],outputLocation:animation,codec:'h264',crf:18,x264Preset:'veryfast',concurrency:4,muted:true});
    if(animate===shot.seconds)ff(['-i',animation,'-an','-c:v','copy','-video_track_timescale','15360',destination]);
    else ff(['-i',animation,'-vf',`tpad=stop_mode=clone:stop_duration=${shot.seconds-animate}`,'-frames:v',String(shot.seconds*30),...encode,destination]);
   }
   const info=await metadata(destination);if(Math.abs(info.duration-shot.seconds)>.08)throw new Error('Segment duration mismatch '+shot.id);
   fs.writeFileSync(stamp,JSON.stringify({hash,seconds:shot.seconds,file:destination}));
  }
  if(editorialOnly||previews||only)return;
  const list=path.join(out,'concat.txt');fs.writeFileSync(list,shots.map((s,i)=>`file '${String(i).padStart(2,'0')}-${s.id}.mp4'`).join('\n'));
  const video=path.join(out,'full-picture.mp4');ff(['-f','concat','-safe','0','-i',list,'-an','-c:v','copy','-movflags','+faststart',video]);
  const sound=f=>path.join(root,'public/sound',f+'.wav');
  const filters=['[1:a]atrim=0:45,asetpts=PTS-STARTPTS[a0]','[2:a]atrim=start=9:end=564,asetpts=PTS-STARTPTS,volume=0.13,afade=t=in:d=2,afade=t=out:st=547:d=8,adelay=45000|45000[a1]','[3:a]asplit=2[p1][p2]','[p1]volume=0.2,adelay=95000|95000[a2]','[p2]volume=0.2,adelay=135000|135000[a3]','[4:a]volume=0.16,adelay=238000|238000[a4]','[5:a]volume=0.18,adelay=365000|365000[a5]','[6:a]volume=0.25,adelay=587000|587000[a6]','[a0][a1][a2][a3][a4][a5][a6]amix=inputs=7:normalize=0,apad,atrim=0:600[a]'].join(';');
  const output=path.join(root,'out/draftly-full-film.mp4');
  ff(['-i',video,'-i',path.join(root,'out/draftly-opening.mp4'),'-i',sound('score'),'-i',sound('page'),'-i',sound('click'),'-i',sound('pen'),'-i',sound('folder'),'-filter_complex',filters,'-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-t','600','-movflags','+faststart',output]);
  console.log('Complete: '+output);
 }finally{browser.disconnect();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
