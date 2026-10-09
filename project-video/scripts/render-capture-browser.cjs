// Reuse only the owned film-capture Chrome; avoids repeated Windows startups.
// Internal connection adapter is pinned to the installed Remotion 4.0.534.
const path=require('node:path');
const {bundle}=require('@remotion/bundler');
const {getCompositions,renderMedia,renderStill}=require('@remotion/renderer');
const root=path.resolve(__dirname,'..');
const internal=name=>require(path.join(root,'node_modules/@remotion/renderer/dist/browser',name+'.js'));
const {HeadlessBrowser}=internal('Browser');
const {Connection}=internal('Connection');
const {NodeWebSocketTransport}=internal('NodeWebSocketTransport');
(async()=>{
 const info=await (await fetch('http://127.0.0.1:9223/json/version')).json();
 const transport=await NodeWebSocketTransport.create(info.webSocketDebuggerUrl);
 const connection=new Connection(transport);
 const browser=new HeadlessBrowser({connection,defaultViewport:{width:1920,height:1080},runner:{closeProcess:async()=>{}}});
 await connection.send('Target.setDiscoverTargets',{discover:true});
 console.log('Connected to the owned film capture browser.');
 try {
  let last=-1;
  const serveUrl=await bundle({entryPoint:path.join(root,'src/index.ts'),publicDir:path.join(root,'public'),onProgress:p=>{const pct=Math.floor(p/20)*20;if(pct!==last){last=pct;console.log(`Bundle ${pct}%`);}}});
  const compositions=await getCompositions(serveUrl,{browserInstance:browser});
  const preview=process.argv.includes('--preview');
  const composition=compositions.find(c=>c.id===(preview?'DraftlyContinuationReview':'DraftlyWorkflowFilm'));
  if(process.argv.includes('--stills')){
   for(const frame of [1440,1830,2310,2790,2880]){
    await renderStill({serveUrl,composition,browserInstance:browser,frame,output:path.join(root,`out/continuation/review-${frame}.png`),imageFormat:'png'});
    console.log(`Inspected frame ${frame}`);
   }
  }else{
   if(!preview)require('./check-workflow.cjs');
   let lastProgress=-1;
   await renderMedia({serveUrl,composition,browserInstance:browser,outputLocation:path.join(root,preview?'out/draftly-continuation-preview.mp4':'out/draftly-workflow-film.mp4'),codec:'h264',crf:18,concurrency:2,onProgress:p=>{const pct=Math.floor(p.progress*100/5)*5;if(pct!==lastProgress){lastProgress=pct;console.log(`Render ${pct}%`);}}});
   console.log('Render complete.');
  }
 }finally{browser.disconnect();}
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
