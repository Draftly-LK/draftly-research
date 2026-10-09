import React from 'react';
import {Video, Audio} from '@remotion/media';
import {AbsoluteFill, Freeze, Img, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {BrandBug, Desk, FilmBase, Note, SourcePage, Stamp, clamp, palette, type} from './style';
import media from './media.json';

const ease = Easing.bezier(.2,.8,.2,1);

export const FolderArrival: React.FC = () => {
  const frame = useCurrentFrame();
  return <AbsoluteFill><Desk/>
    <div style={{position:'absolute',left:480,top:220,width:960,height:650,transform:`translateY(${interpolate(frame,[0,19,24],[-880,8,0],{...clamp,easing:ease})}px) rotate(-3deg)`,boxShadow:'0 22px 42px rgba(0,0,0,.28)',background:'#AE9874',borderRadius:'3px 3px 7px 7px'}}>
      <div style={{position:'absolute',left:0,top:-45,width:280,height:60,background:'#AE9874',borderRadius:'14px 18px 0 0'}}/>
      <div style={{position:'absolute',inset:28,overflow:'hidden'}}><SourcePage id="title" style={{width:700,position:'absolute',left:102,top:14,rotate:'0deg'}}/></div>
      <div style={{position:'absolute',inset:0,background:'#B6A17D',borderTop:'1px solid #C8B691',transformOrigin:'left center',transform:`perspective(1800px) rotateY(${interpolate(frame,[76,136],[0,-135],{...clamp,easing:ease})}deg)`,backfaceVisibility:'hidden',boxShadow:'-4px 0 8px rgba(0,0,0,.08)'}}>
        <div style={{position:'absolute',left:80,top:100,width:570,padding:28,border:'1px solid #5F553F',color:palette.ink}}><div style={{fontSize:21,letterSpacing:3}}>CLIENT FILE</div><div style={{fontFamily:type.display,fontSize:60,marginTop:14}}>One property transfer.</div></div>
        <div style={{position:'absolute',left:80,bottom:62,fontSize:26,color:palette.ink}}>Follow the evidence.</div>
      </div>
    </div>
    <div style={{position:'absolute',left:96,top:64,fontSize:23,letterSpacing:2,color:palette.cream,opacity:interpolate(frame,[42,62],[0,1],clamp)}}>SRI LANKAN NOTARIAL &amp; CONVEYANCING WORK</div>
  </AbsoluteFill>;
};

export const ExtentInspection: React.FC<{document: 'title'|'instrument'; compare?: boolean}> = ({document,compare}) => {
  const frame=useCurrentFrame();
  const {fps}=useVideoConfig();
  return <AbsoluteFill style={{background:'#F2EFE9',color:palette.ink}}>
    <Stamp text={compare?'Compare the records':'Read the source'} dark/>
    <div style={{position:'absolute',left:96,top:150,width:610,height:808,overflow:'hidden'}}><SourcePage id={document} style={{width:'100%',height:780,objectFit:'contain',objectPosition:'left top',boxShadow:'none',filter:'drop-shadow(0 12px 18px rgba(15,27,46,.18))',translate:`0 ${interpolate(frame,[0,1.1*fps],[28,0],{...clamp,easing:ease})}px`}}/></div>
    <div style={{position:'absolute',left:800,top:190,right:96}}>
      <div style={{fontSize:26,letterSpacing:2,color:'#566377'}}>{document==='title'?'TITLE CERTIFICATE':'TRANSFER INSTRUMENT · PAGE 2'}</div>
      <div style={{fontFamily:type.display,fontSize:76,lineHeight:1.07,marginTop:26}}>One detail.<br/>Read in context.</div>
      <div style={{marginTop:66,background:'#fff',padding:'34px 18px',position:'relative'}}>
        <Img src={staticFile(`evidence/${document}-extent.png`)} style={{width:'100%',height:84,objectFit:'contain'}}/>
        <svg width="100%" height="30" style={{position:'absolute',left:18,bottom:10}} viewBox="0 0 950 30"><path d="M260 14 Q460 9 870 14" stroke={palette.gold} fill="none" strokeWidth="9" strokeLinecap="round" strokeDasharray="620" strokeDashoffset={interpolate(frame,[1.5*fps,2.25*fps],[620,0],clamp)}/></svg>
      </div>
      <div style={{fontSize:44,marginTop:34,fontVariantNumeric:'tabular-nums'}}>0.0159 hectares</div>
      <div style={{fontSize:26,marginTop:20,color:'#566377'}}>{compare?'The same extent appears in the instrument.':'The source page stays available for inspection.'}</div>
    </div>
    <Note dark>Source display copies. Originals unchanged.</Note>
  </AbsoluteFill>;
};

export const EvidenceQuestion: React.FC = () => {
  const frame=useCurrentFrame();const {fps}=useVideoConfig();
  return <AbsoluteFill>
    <Stamp text="A question in the supplied file"/><BrandBug/>
    <div style={{position:'absolute',left:96,top:155,fontFamily:type.display,fontSize:74,lineHeight:1.12}}>What does each record describe?</div>
    <div style={{position:'absolute',left:96,top:350,width:1020}}>
      <div style={{fontSize:25,color:palette.cream,marginBottom:18}}>TITLE CERTIFICATE &amp; TRANSFER INSTRUMENT</div>
      <div style={{background:'#fff',padding:'36px 26px'}}><Img src={staticFile('evidence/title-extent.png')} style={{width:950,height:100,objectFit:'contain'}}/></div>
      <div style={{fontSize:82,marginTop:26,fontVariantNumeric:'tabular-nums'}}>0.0159 <span style={{fontSize:34,color:palette.muted}}>hectares</span></div>
      <div style={{position:'absolute',width:1000,height:3,background:palette.gold,top:217,scale:`${interpolate(frame,[14,45],[0,1],clamp)} 1`,transformOrigin:'left'}}/>
    </div>
    <div style={{position:'absolute',left:1260,top:350,width:560,opacity:interpolate(frame,[1.2*fps,1.7*fps],[0,1],clamp)}}>
      <div style={{fontSize:25,color:palette.cream,marginBottom:18}}>SURVEY EXTRACT</div>
      <div style={{background:'#fff',width:230,height:172,padding:14}}><Img src={staticFile('evidence/survey-extent.png')} style={{width:200,height:144,objectFit:'contain'}}/></div>
      <div style={{fontSize:82,marginTop:26,fontVariantNumeric:'tabular-nums'}}>0.0153</div><div style={{fontSize:34,color:palette.muted}}>hectares</div>
    </div>
    <Note>A difference to investigate. No legal conclusion is implied.</Note>
  </AbsoluteFill>;
};

export const ProductHandoff: React.FC = () => {
  const frame=useCurrentFrame();const {fps}=useVideoConfig();
  const clip=(media.replacements as Record<string,{file:string;duration:number}>)['case-001-reopen.mp4'];
  const lastFrame=clip?Math.max(0,Math.floor(clip.duration*fps)-1):0;
  const video=clip?<Video src={staticFile(clip.file)} muted premountFor={fps} style={{width:'100%',height:'100%'}}/>:null;
  return <AbsoluteFill style={{background:palette.paper}}>
    <div style={{position:'absolute',inset:0,overflow:'hidden'}}>
      {clip?(frame>lastFrame?<Freeze frame={lastFrame}>{video}</Freeze>:video):<SourcePage id="title" style={{width:900,margin:'0 auto'}}/>}
    </div>
    <div style={{position:'absolute',left:269,top:374,width:1080,height:660,overflow:'hidden',opacity:interpolate(frame,[0,1.1*fps],[1,0],clamp)}}><SourcePage id="title" style={{width:1080}}/></div>
    <div style={{position:'absolute',left:96,bottom:46,padding:'14px 22px',background:palette.navy,color:palette.cream,fontSize:26}}>{clip?'Draftly source review · prepared extraction · review demonstration':'The source will stay in view during review.'}</div>
  </AbsoluteFill>;
};

export const OpeningVisual: React.FC = () => {
  const {fps}=useVideoConfig();
  return <>
    <Sequence name="Folder arrives" durationInFrames={7*fps} premountFor={fps}><FolderArrival/></Sequence>
    <Sequence name="Certificate extent" from={7*fps} durationInFrames={8*fps} premountFor={fps}><ExtentInspection document="title"/></Sequence>
    <Sequence name="Instrument extent" from={15*fps} durationInFrames={8*fps} premountFor={fps}><ExtentInspection document="instrument" compare/></Sequence>
    <Sequence name="A genuine question" from={23*fps} durationInFrames={13*fps} premountFor={fps}><EvidenceQuestion/></Sequence>
    <Sequence name="Document to review viewer" from={36*fps} durationInFrames={9*fps} premountFor={fps}><ProductHandoff/></Sequence>
  </>;
};

export const Opening: React.FC<{sound?:boolean}> = ({sound=true}) => {
  const {fps}=useVideoConfig();
  return <FilmBase><OpeningVisual/>{sound&&<>
    <Sequence from={18} durationInFrames={2*fps} premountFor={fps}><Audio src={staticFile('sound/folder.wav')} volume={.65}/></Sequence>
    <Sequence from={76} durationInFrames={2*fps} premountFor={fps}><Audio src={staticFile('sound/page.wav')} volume={.3}/></Sequence>
    <Sequence from={15*fps} durationInFrames={2*fps} premountFor={fps}><Audio src={staticFile('sound/page.wav')} volume={.24}/></Sequence>
    <Sequence from={9*fps} durationInFrames={2*fps} premountFor={fps}><Audio src={staticFile('sound/pen.wav')} volume={.26}/></Sequence>
    <Sequence from={36*fps} premountFor={fps}><Audio src={staticFile('sound/score.wav')} volume={(f)=>interpolate(f,[0,2*fps,7*fps,9*fps],[0,.16,.16,0],clamp)}/></Sequence>
  </>}</FilmBase>;
};
