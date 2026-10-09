import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {Shot} from './edit';
import {BrandBug, Desk, Note, SourcePage, Stamp, clamp, palette, type} from './style';
import {EvidenceQuestion} from './Opening';

const names:Record<string,string>={title:'Title certificate · page 1',instrument:'Transfer instrument · page 2',survey:'Survey extract',resolution:'Board resolution',payment:'Payment record',identity:'Identity document','instrument-cover':'Transfer instrument · cover'};
const ease=Easing.bezier(.2,.8,.2,1);

export const EvidenceSource:React.FC<{shot:Shot}>=({shot})=>{
  const f=useCurrentFrame();const {fps}=useVideoConfig();const id=shot.source??'title';
  return <AbsoluteFill style={{background:'#E9E5DD',color:palette.ink}}>
    <Stamp text={names[id]??'Source evidence'} dark/>
    <div style={{position:'absolute',left:90,top:134,width:1100,height:820,overflow:'hidden'}}>
      <SourcePage id={id} style={{width:id==='survey'?1100:790,margin:'0 auto',translate:`0 ${interpolate(f,[0,1.2*fps],[22,0],{...clamp,easing:ease})}px`}}/>
    </div>
    <div style={{position:'absolute',left:1250,top:220,right:90}}>
      <div style={{fontFamily:type.display,fontSize:61,lineHeight:1.14}}>{shot.headline??'Keep the source in view.'}</div>
      {(id==='title'||id==='instrument')&&<><div style={{marginTop:70,fontSize:72,fontVariantNumeric:'tabular-nums'}}>0.0159</div><div style={{fontSize:30}}>hectares</div><div style={{marginTop:32,background:'#fff',padding:12}}><Img src={staticFile(`evidence/${id}-extent.png`)} style={{width:'100%',height:75,objectFit:'contain'}}/></div></>}
      {id==='survey'&&<><div style={{marginTop:70,fontSize:72}}>0.0153</div><div style={{fontSize:30}}>hectares</div></>}
      <div style={{width:90,height:4,background:palette.gold,marginTop:45}}/>
    </div>
    <Note dark>{shot.label??'Read the complete record before deciding what the detail means.'}</Note>
  </AbsoluteFill>;
};

export const Bundle:React.FC=()=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();
 const pages=['title','instrument','survey','resolution','payment','identity','instrument-cover'];
 const active=Math.min(6,Math.floor(f/(1.35*fps)));
 return <AbsoluteFill><Desk/><Stamp text="Seven supplied source files"/>
  {pages.map((id,i)=><SourcePage key={id} id={id} style={{position:'absolute',width:480,left:330+i*155,top:220+(i%2)*50,rotate:`${(i-3)*4}deg`,zIndex:active===i?15:i,translate:`0 ${interpolate(f,[i*.12*fps,(i*.12+.6)*fps],[70,0],{...clamp,easing:ease})}px`}}/>)}
  <div style={{position:'absolute',left:96,bottom:88,right:96,background:palette.navy,padding:'22px 30px',zIndex:20,display:'flex',justifyContent:'space-between',fontSize:30}}><span>{names[pages[active]]}</span><span style={{color:palette.cream}}>One bundle. Relationships still need examination.</span></div>
 </AbsoluteFill>;
};

export const ManualComparison:React.FC=()=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();
 return <AbsoluteFill style={{background:'#E9E5DD',color:palette.ink}}><Stamp text="Compare the pages before comparing the values" dark/>
  <div style={{position:'absolute',left:110,top:135,width:780,height:700,overflow:'hidden'}}><SourcePage id="title" style={{width:780,translate:`0 ${interpolate(f,[0,1.25*fps],[15,0],{...clamp,easing:ease})}px`}}/></div>
  <div style={{position:'absolute',left:1020,top:135,width:790,height:700,overflow:'hidden'}}><SourcePage id="survey" style={{width:1050,translate:'-100px 0'}}/></div>
  <div style={{position:'absolute',left:110,top:680,width:780,background:'#fff',padding:'20px 10px'}}><Img src={staticFile('evidence/title-extent.png')} style={{width:760,height:95,objectFit:'contain'}}/><div style={{fontSize:43,marginTop:12}}>0.0159 hectares</div></div>
  <div style={{position:'absolute',left:1020,top:640,width:790,background:'#fff',padding:20,display:'flex',alignItems:'center',gap:38}}><Img src={staticFile('evidence/survey-extent.png')} style={{width:190,height:185,objectFit:'contain'}}/><div style={{fontSize:43}}>0.0153 hectares</div></div>
  <svg width="1920" height="1080" style={{position:'absolute',inset:0}}><path d="M500 850 C620 875 1210 875 1430 850" stroke={palette.gold} strokeWidth="4" fill="none" strokeDasharray="950" strokeDashoffset={interpolate(f,[3*fps,4.1*fps],[950,0],clamp)}/></svg>
  <Note dark>Do these records describe the same parcel and transaction?</Note>
 </AbsoluteFill>;
};

export const Practitioners:React.FC=()=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();
 const phase=f<10*fps?0:f<20*fps?1:2;
 return <AbsoluteFill><Desk/>
  <div style={{position:'absolute',left:225,top:140,width:1460,height:790,background:'#F5F0E6',color:palette.ink,boxShadow:'0 25px 45px #0005',rotate:'-1deg',padding:'60px 75px'}}>
   <div style={{fontSize:22,letterSpacing:3,color:'#5D655F'}}>WORKFLOW DEVELOPMENT</div>
   <div style={{fontFamily:type.display,fontSize:65,marginTop:24}}>{phase===0?'Start with practice.':phase===1?'Develop the workflow together.':'Bring research expertise into the design.'}</div>
   <div style={{position:'absolute',left:75,top:235,bottom:70,width:3,background:'#C4AA74'}}/>
   <div style={{marginTop:75,marginLeft:50,fontSize:38,lineHeight:1.6,maxWidth:1120}}>
    {phase===0?<><div>Discussions with five lawyers.</div><div style={{display:'flex',gap:55,marginTop:42}}>{[1,2,3,4,5].map((n)=><div key={n} style={{fontSize:64,borderBottom:`3px solid ${palette.gold}`,width:100,textAlign:'center',opacity:interpolate(f,[n*.7*fps,(n*.7+.3)*fps],[0,1],clamp)}}>{n}</div>)}</div></>:phase===1?<><div>One lawyer contributed to developing the workflow.</div><div style={{marginTop:44,fontSize:30,color:'#566377'}}>Source inspection → review decisions → working instrument</div></>:<><div>Guidance from Legal IR and NLP experts.</div><div style={{marginTop:44,fontSize:30,color:'#566377'}}>Questions, evidence and retrieval design.</div></>}
   </div>
   <div style={{position:'absolute',left:125,bottom:58,fontSize:24,color:'#566377'}}>Contributions to development. No formal legal certification is claimed.</div>
  </div>
 </AbsoluteFill>;
};

export const EvidenceThread:React.FC<{mode?:string}>=({mode})=><AbsoluteFill style={{background:'#E9E5DD',color:palette.ink}}>
 <Stamp text="Follow the extent" dark/>
 <SourcePage id="title" style={{position:'absolute',left:95,top:160,width:800}}/>
 <div style={{position:'absolute',left:1010,top:260,right:110}}><div style={{fontSize:28}}>SOURCE → PROPOSED VALUE → REVIEW</div><div style={{fontSize:124,fontFamily:type.display,marginTop:40}}>0.0159</div><div style={{fontSize:39}}>hectares</div><div style={{marginTop:60,fontSize:34,lineHeight:1.5}}>{mode==='source'?'The value travels with a page reference.':'Return to the evidence before carrying a value into the instrument.'}</div></div>
 <Note dark>One property detail. Its meaning stays tied to the record.</Note>
</AbsoluteFill>;

export const ResearchEditorial:React.FC<{shot:Shot}>=({shot})=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();
 const mode=shot.mode;
 return <AbsoluteFill><BrandBug/><Stamp text={mode==='case'?'Inspect a research lead':mode==='evaluation'?'Research evaluation':'A question arising from the matter'}/>
  <div style={{position:'absolute',left:96,top:170,width:680,height:780,overflow:'hidden'}}><SourcePage id={mode==='case'?'survey':'title'} style={{width:680}}/></div>
  <div style={{position:'absolute',left:880,top:200,right:105}}>
   <div style={{fontFamily:type.display,fontSize:71,lineHeight:1.12}}>{mode==='case'?'A case-law result needs inspection.':mode==='evaluation'?'Can the supporting passage be found again?':mode==='citation'?'Which passage supports the answer?':mode==='matter'?'Take the file’s question into the conversation.':shot.headline??'What does each record describe?'}</div>
   <div style={{width:160,height:4,background:palette.gold,marginTop:44,scale:`${interpolate(f,[0,fps],[0,1],clamp)} 1`,transformOrigin:'left'}}/>
   <div style={{fontSize:34,lineHeight:1.5,marginTop:50,color:palette.cream}}>{mode==='case'?'Open the source. Check the facts, context and relevance. A research lead is not an authoritative conclusion.':mode==='evaluation'?'Keep the question, cited source and inspected passage together. No benchmark result is asserted here.':mode==='citation'?'The lawyer must inspect the supporting text in its context.':mode==='matter'?'Use the matter’s evidence to frame the question. Then enter the dedicated Research workspace.':'Check parcel identity, the transaction and the role of each supplied record.'}</div>
  </div>
  <Note>{mode==='citation'||mode==='matter'||mode==='case'?'Editorial sequence · current product recording still required.':'The evidence raises the question; the practitioner decides what follows.'}</Note>
 </AbsoluteFill>;
};

export const PlannedInspection:React.FC=()=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();
 return <AbsoluteFill style={{background:'#E9E5DD',color:palette.ink}}><Stamp text="Planned · date-sensitive source inspection" dark/>
  <SourcePage id="instrument" style={{position:'absolute',left:96,top:155,width:740}}/>
  <div style={{position:'absolute',left:970,top:220,right:96}}><div style={{fontFamily:type.display,fontSize:73}}>Inspect the law<br/>at the relevant date.</div>
   <div style={{position:'relative',marginTop:100,height:150}}><div style={{height:3,background:palette.ink,width:700}}/>{['Transaction date','Current date'].map((t,i)=><div key={t} style={{position:'absolute',left:i*460,top:-10,opacity:interpolate(f,[i*2*fps,i*2*fps+15],[0,1],clamp)}}><div style={{width:23,height:23,borderRadius:12,background:palette.gold}}/><div style={{marginTop:26,fontSize:29}}>{t}</div></div>)}</div>
   <div style={{fontSize:31,lineHeight:1.5}}>Amendment history and date-sensitive inspection are shown as planned work.</div>
  </div><Note dark>Planned capability. Not demonstrated in this recording.</Note>
 </AbsoluteFill>;
};

export const Closing:React.FC=()=>{
 const f=useCurrentFrame();const {fps}=useVideoConfig();
 return <AbsoluteFill><Desk/>
  <div style={{position:'absolute',left:335,top:145,width:920,height:800,overflow:'hidden',rotate:'-3deg'}}><SourcePage id="title" style={{width:920}}/></div>
  <div style={{position:'absolute',left:330,top:170,width:980,height:700,background:'#B6A17D',rotate:'-3deg',transformOrigin:'left center',transform:`perspective(2000px) rotateY(${interpolate(f,[2*fps,4*fps],[-120,0],{...clamp,easing:ease})}deg)`,backfaceVisibility:'hidden',boxShadow:'0 28px 40px #0004'}}><div style={{position:'absolute',left:70,top:90,fontFamily:type.display,fontSize:69,color:palette.ink}}>One property transfer.</div></div>
  <div style={{position:'absolute',inset:0,background:palette.navy,opacity:interpolate(f,[7*fps,8.5*fps],[0,1],clamp)}}/>
  <div style={{position:'absolute',left:96,top:330,opacity:interpolate(f,[8.5*fps,9.5*fps],[0,1],clamp)}}><Img src={staticFile('brand/logo-mark-white.png')} style={{width:95,height:95}}/><div style={{fontFamily:type.display,fontSize:108,marginTop:24}}>Draftly</div><div style={{fontSize:56,marginTop:30}}>Follow the evidence.</div><div style={{fontSize:29,marginTop:52,color:palette.cream}}>Evidence stays visible. Decisions stay with the practitioner.</div></div>
 </AbsoluteFill>;
};

export {EvidenceQuestion};
