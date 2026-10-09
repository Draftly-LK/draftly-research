import React from 'react';

import {Audio, Video} from '@remotion/media';

import {AbsoluteFill, Freeze, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

import edit from './edit.json';

import measured from './media.json';

import {Opening} from '../film/Opening';

import {FilmBase, clamp, palette, type} from '../film/style';

import {ScatteredScene} from '../continuation/ScatteredScene';

import {PractitionerStory, SourceInspection, EvidenceComparison, ClosingLong} from './Editorial';

import {ResearchContribution, PlannedSourceInspection} from './ResearchEditorial';



export interface LongShotSpec {

 id:string;chapter:string;seconds:number;from:number;kind:string;

 file?:string;headline?:string;note?:string;source?:string;detail?:string;

 crop?:number[];start?:number;end?:number;animateSeconds?:number;

}

export const LONG_EDIT=edit as LongShotSpec[];

export const PANEL={x:70,y:215,width:1780,height:740};

const metadata=measured as Record<string,{duration:number;width:number;height:number}>;



export const RecordingFrame:React.FC<{shot:LongShotSpec;plateOnly?:boolean}>=({shot,plateOnly=false})=>{

 const frame=useCurrentFrame();const {fps}=useVideoConfig();

 const [x,y,w]=shot.crop??[260,180,1580];const scale=PANEL.width/w;

 const start=shot.start??0;const end=Math.min(shot.end??Infinity,metadata[shot.file!]?.duration??shot.seconds);

 const playable=Math.max(1,Math.floor((end-start)*fps));

 const video=<Video src={staticFile(shot.file!)} trimBefore={Math.round(start*fps)} trimAfter={Math.floor(end*fps)} muted premountFor={fps} style={{width:1920,height:1080}}/>;

 return <FilmBase>

  <div style={{position:'absolute',left:80,top:49,color:palette.cream,fontSize:26,letterSpacing:1.1}}>{shot.chapter.toUpperCase()}</div>

  <div style={{position:'absolute',left:80,right:80,top:107,fontFamily:type.display,fontSize:55,lineHeight:1.08,color:palette.cream}}>{shot.headline}</div>

  <div style={{position:'absolute',left:PANEL.x,top:PANEL.y,width:PANEL.width,height:PANEL.height,background:'#F3F5F8',overflow:'hidden'}}>

   {!plateOnly&&<div style={{position:'absolute',left:-x*scale,top:-y*scale,width:1920,height:1080,scale,transformOrigin:'0 0'}}>{frame>=playable?<Freeze frame={playable-1}>{video}</Freeze>:video}</div>}

  </div>

  <div style={{position:'absolute',left:80,right:80,bottom:48,color:palette.cream,fontSize:27,lineHeight:1.3}}>{shot.note}</div>

 </FilmBase>;

};



export const LongShot:React.FC<{shot:LongShotSpec;plateOnly?:boolean}>=({shot,plateOnly=false})=>{

 switch(shot.kind){

  case 'opening':return <Opening sound={false}/>;

  case 'recording':return <RecordingFrame shot={shot} plateOnly={plateOnly}/>;

  case 'people':return <PractitionerStory/>;

  case 'bundle':return <FilmBase><ScatteredScene/></FilmBase>;

  case 'source':return <SourceInspection source={shot.source!} headline={shot.headline!} note={shot.note!} detail={shot.detail}/>;

  case 'comparison':return <EvidenceComparison/>;

  case 'researchGraphic':return <ResearchPaperStory/>;

  case 'planned':return <PlannedSourceInspection/>;

  case 'closing':return <ClosingLong/>;

  default:throw new Error('Unrecognized film shot '+shot.kind);

 }

};



const ResearchPaperStory:React.FC=()=>{

 const frame=useCurrentFrame();const{fps}=useVideoConfig();return <FilmBase>

  <ResearchContribution/>

  {frame<8*fps&&<AbsoluteFill style={{opacity:interpolate(frame,[7*fps,8*fps],[1,0],clamp)}}><SourceInspection source="research/paper-title.png" headline="Research behind the workflow." note="Research paper · provisional reference labels await lawyer validation." detail="Does statutory structure help retrieve every indispensable provision?"/></AbsoluteFill>}

 </FilmBase>;

};



export const LongAudio:React.FC=()=>{

 const {fps}=useVideoConfig();

 return <>

  <Sequence durationInFrames={45*fps}><OpeningAudio/></Sequence>

  <Sequence from={45*fps} durationInFrames={555*fps} premountFor={fps}><Audio src={staticFile('sound/score.wav')} trimBefore={9*fps} volume={f=>interpolate(f,[0,2*fps,547*fps,555*fps],[0,.13,.13,0],clamp)}/></Sequence>

  <Sequence from={95*fps} durationInFrames={2*fps} premountFor={fps}><Audio src={staticFile('sound/page.wav')} volume={.2}/></Sequence>

  <Sequence from={135*fps} durationInFrames={2*fps} premountFor={fps}><Audio src={staticFile('sound/page.wav')} volume={.2}/></Sequence>

  <Sequence from={238*fps} durationInFrames={fps} premountFor={fps}><Audio src={staticFile('sound/click.wav')} volume={.16}/></Sequence>

  <Sequence from={365*fps} durationInFrames={fps} premountFor={fps}><Audio src={staticFile('sound/pen.wav')} volume={.18}/></Sequence>

  <Sequence from={587*fps} durationInFrames={2*fps} premountFor={fps}><Audio src={staticFile('sound/folder.wav')} volume={.25}/></Sequence>

 </>;

};

const OpeningAudio:React.FC=()=>{

 const{fps}=useVideoConfig();return <>

 <Sequence from={18} durationInFrames={2*fps}><Audio src={staticFile('sound/folder.wav')} volume={.65}/></Sequence>

 <Sequence from={76} durationInFrames={2*fps}><Audio src={staticFile('sound/page.wav')} volume={.3}/></Sequence>

 <Sequence from={15*fps} durationInFrames={2*fps}><Audio src={staticFile('sound/page.wav')} volume={.24}/></Sequence>

 <Sequence from={9*fps} durationInFrames={2*fps}><Audio src={staticFile('sound/pen.wav')} volume={.26}/></Sequence>

 <Sequence from={36*fps} durationInFrames={9*fps}><Audio src={staticFile('sound/score.wav')} volume={f=>interpolate(f,[0,2*fps,7*fps,9*fps],[0,.16,.16,0],clamp)}/></Sequence>

 </>;

};

export const FullFilm:React.FC=()=>{

 const{fps}=useVideoConfig();return <FilmBase>

 {LONG_EDIT.map(shot=><Sequence key={shot.id} name={shot.chapter+' / '+shot.id} from={shot.from*fps} durationInFrames={shot.seconds*fps} premountFor={fps}><LongShot shot={shot}/></Sequence>)}

 <LongAudio/>

 </FilmBase>;

};
