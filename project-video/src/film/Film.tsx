import React from 'react';
import {Audio} from '@remotion/media';
import {Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {EDIT,Shot,TOTAL_SECONDS} from './edit';
import {FilmBase,clamp} from './style';
import {Opening} from './Opening';
import {AppShot} from './AppShot';
import {Bundle,Closing,EvidenceSource,EvidenceThread,ManualComparison,PlannedInspection,Practitioners,ResearchEditorial,EvidenceQuestion} from './Scenes';
import media from './media.json';

const ShotVisual:React.FC<{shot:Shot;sound:boolean}>=({shot,sound})=>{
 switch(shot.kind){
  case 'opening':return <Opening sound={sound}/>;
  case 'source':return <EvidenceSource shot={shot}/>;
  case 'bundle':return <Bundle/>;
  case 'practitioners':return <Practitioners/>;
  case 'manual':return <ManualComparison/>;
  case 'thread':return <EvidenceThread mode={shot.mode}/>;
  case 'question':return <EvidenceQuestion/>;
  case 'app':return <AppShot shot={shot}/>;
  case 'research':return shot.replacement&&(media.replacements as Record<string,unknown>)[shot.replacement]?<AppShot shot={shot}/>:<ResearchEditorial shot={shot}/>;
  case 'planned':return <PlannedInspection/>;
  case 'closing':return <Closing/>;
 }
};

// One intentionally data-driven timeline: edit seconds and recording ranges in edit.ts.
export const Film:React.FC<{sound?:boolean}>=({sound=true})=>{
 const {fps}=useVideoConfig();let cursor=0;
 const timeline=EDIT.flatMap(chapter=>chapter.shots.map(shot=>{const from=cursor;cursor+=shot.seconds;return {chapter,shot,from};}));
 return <FilmBase>
  {timeline.map(({chapter,shot,from})=><Sequence key={shot.id} name={`${chapter.title} / ${shot.id}`} from={Math.round(from*fps)} durationInFrames={Math.round(shot.seconds*fps)} premountFor={fps}><ShotVisual shot={shot} sound={sound}/></Sequence>)}
  {sound&&<><Sequence from={45*fps} durationInFrames={(TOTAL_SECONDS-45)*fps} premountFor={fps}>
   <Audio src={staticFile('sound/score.wav')} trimBefore={9*fps} volume={f=>{
    const t=f/fps+45;const current=timeline.find(item=>t>=item.from&&t<item.from+item.shot.seconds);
    const index=current?timeline.indexOf(current):0;
    const volume=(i:number)=>['source','manual','question','research','planned'].includes(timeline[Math.max(0,i)].shot.kind)?.065:.13;
    const level=current?interpolate(t,[current.from,current.from+.5],[volume(index-1),volume(index)],clamp):.065;
    return interpolate(f,[0,2*fps,(TOTAL_SECONDS-49)*fps,(TOTAL_SECONDS-45)*fps],[0,level,level,0],clamp);
   }}/>
  </Sequence>
  <Sequence from={95*fps} durationInFrames={2*fps} premountFor={fps}><Audio src={staticFile('sound/page.wav')} volume={.22}/></Sequence>
  <Sequence from={135*fps} durationInFrames={2*fps} premountFor={fps}><Audio src={staticFile('sound/page.wav')} volume={.2}/></Sequence>
  <Sequence from={581*fps} durationInFrames={2*fps} premountFor={fps}><Audio src={staticFile('sound/folder.wav')} volume={.3}/></Sequence>
  </>}
 </FilmBase>;
};
