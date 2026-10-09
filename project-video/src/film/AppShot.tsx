import React from 'react';
import {Video} from '@remotion/media';
import {AbsoluteFill, Freeze, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Shot} from './edit';
import footage from '../footage.json';
import media from './media.json';
import {clamp,palette,type,SourcePage,Stamp,Note} from './style';

export const AppShot: React.FC<{shot:Shot}> = ({shot}) => {
  const frame=useCurrentFrame();const {fps}=useVideoConfig();
  const replacement=shot.replacement?(media.replacements as Record<string,{file:string;duration:number}>)[shot.replacement]:undefined;
  // No legacy case footage is permitted to fall through into this film.
  if(!replacement)return <AbsoluteFill style={{background:'#E9E5DD',color:palette.ink}}>
    <Stamp text="Evidence inspection · editorial review cut" dark/>
    <SourcePage id={shot.id.includes('draft')?'instrument':'title'} style={{position:'absolute',left:96,top:140,width:800}}/>
    <div style={{position:'absolute',left:1050,top:260,width:700,fontFamily:type.display,fontSize:68,lineHeight:1.15}}>{shot.headline??shot.label??'Keep the source available for review.'}</div>
    <Note dark>Current product recording required for this action.</Note>
  </AbsoluteFill>;
  const start=replacement?0:(shot.start??0);
  const end=replacement?replacement.duration:(shot.end??(footage as Record<string,number>)[shot.clip!]);
  const sourceFrames=Math.max(1,Math.floor((end-start)*fps));
  // Interface action plays at natural speed. A readable hold fills spare time.
  // When the shot is shorter, a mild speed-up is capped at 1.6x.
  const rate=Math.min(1.6,Math.max(1,(end-start)/shot.seconds));
  const playFrames=Math.floor(sourceFrames/rate);
  const [x,y,w,h]=shot.crop??[0,0,1,1];
  const scale=Math.max(1/w,1/h);
  const video=<Video src={staticFile(replacement?replacement.file:`footage/${shot.clip}.mp4`)} trimBefore={Math.round(start*fps)} trimAfter={Math.round(end*fps)} playbackRate={rate} muted premountFor={fps} style={{width:1920,height:1080}}/>;
  return <AbsoluteFill style={{background:palette.paper}}>
    <div style={{position:'absolute',left:0,top:0,width:1920,height:1080,overflow:'hidden'}}>
      <div style={{position:'absolute',left:960-(x+w/2)*1920*scale,top:540-(y+h/2)*1080*scale,width:1920,height:1080,scale,transformOrigin:'left top'}}>
        {frame>=playFrames?<Freeze frame={Math.max(0,playFrames-1)}>{video}</Freeze>:video}
      </div>
    </div>
    <div style={{position:'absolute',left:96,bottom:46,right:96,display:'flex',justifyContent:'space-between',alignItems:'end'}}>
      <div style={{maxWidth:1500,background:palette.navy,padding:'12px 20px',color:palette.cream,fontFamily:type.ui,fontSize:25,lineHeight:1.35,opacity:interpolate(frame,[0,8],[0,1],clamp)}}>{shot.label} · {shot.id.includes('review')||shot.id==='processing'?'Prepared extraction · review demonstration':'Recorded product interface'}</div>
    </div>
  </AbsoluteFill>;
};
