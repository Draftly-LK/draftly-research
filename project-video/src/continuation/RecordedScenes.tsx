import React from 'react';
import {Video} from '@remotion/media';
import {AbsoluteFill, Easing, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {clamp, palette, type} from '../film/style';

type Crop = {x: number; y: number; width: number; height: number};
/** Editorial camera move; the recorded product pixels are never reauthored. */
export const RecordedCrop: React.FC<{file: string; trim?: number; crop: Crop; settle?: number}> = ({file, trim = 0, crop, settle = .75}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const progress = interpolate(frame, [0, settle * fps], [0, 1], {...clamp, easing: Easing.bezier(.2,.8,.2,1)});
  const scale = 1760 / crop.width;
  const drift = interpolate(progress, [0, 1], [18, 0]);
  return <div style={{position:'absolute',left:80,top:218,width:1760,height:730,overflow:'hidden',background:'#F3F5F8',border:'1px solid #536071',boxShadow:'0 18px 40px rgba(0,0,0,.2)'}}>
    <div style={{position:'absolute',width:1920,height:1080,transformOrigin:'0 0',transform:`translate(${-crop.x*scale}px,${-crop.y*scale+drift}px) scale(${scale})`}}>
      <Video src={staticFile(file)} trimBefore={Math.round(trim*fps)} muted style={{width:1920,height:1080}}/>
    </div>
  </div>;
};

const Heading: React.FC<{label: string; headline: string; note: string}> = ({label, headline, note}) => <>
  <div style={{position:'absolute',left:80,top:48,fontSize:25,letterSpacing:1.5,color:palette.cream}}>{label}</div>
  <div style={{position:'absolute',left:80,top:101,fontSize:57,lineHeight:1.05,fontFamily:type.display,color:palette.cream}}>{headline}</div>
  <div style={{position:'absolute',left:80,right:80,bottom:53,fontSize:26,color:palette.cream}}>{note}</div>
</>;

export const DocumentsScene: React.FC = () => {
  const {fps}=useVideoConfig();
  return <AbsoluteFill>
    <Heading label="CASE-001 · ACTUAL PRODUCT RECORDING" headline="Bring the documents together. Review the facts." note="Prepared extraction · inspect the source, then approve the fact"/>
    <Sequence durationInFrames={2.5*fps}><RecordedCrop file="footage/case-001-process.mp4" crop={{x:260,y:160,width:1580,height:656}}/></Sequence>
    <Sequence from={2.5*fps} durationInFrames={5.5*fps}><RecordedCrop file="footage/case-001-accept-facts.mp4" crop={{x:905,y:665,width:1000,height:415}}/></Sequence>
  </AbsoluteFill>;
};

export const ResearchScene: React.FC = () => {
  const {fps}=useVideoConfig();
  return <AbsoluteFill>
    <Heading label="CASE-001 · RESEARCH" headline="Follow the evidence. Inspect the authority." note="Registration of Title Act · supporting passage for lawyer inspection"/>
    <Sequence durationInFrames={1.6*fps}><RecordedCrop file="footage/17-legal-sources.mp4" trim={2} crop={{x:260,y:15,width:1580,height:656}} settle={.45}/></Sequence>
    <Sequence from={1.6*fps} durationInFrames={1.4*fps}><RecordedCrop file="footage/18-research-scope.mp4" trim={5} crop={{x:550,y:115,width:1250,height:518}} settle={.4}/></Sequence>
    <Sequence from={3*fps} durationInFrames={4*fps}><RecordedCrop file="footage/19-citation.mp4" trim={28} crop={{x:686,y:505,width:844,height:350}} settle={.6}/></Sequence>
    <div style={{position:'absolute',right:96,top:55,fontSize:24,color:palette.muted}}>Before drafting: inspect registration requirements.</div>
  </AbsoluteFill>;
};

export const DraftScene: React.FC = () => <AbsoluteFill>
  <Heading label="CASE-001 · ACTUAL PRODUCT RECORDING" headline="Prepare the draft. Keep the lawyer in control." note="Working draft · unresolved items remain · approval and export are separate"/>
  <RecordedCrop file="footage/case-001-draft-current.mp4" trim={2} crop={{x:255,y:0,width:1480,height:614}}/>
</AbsoluteFill>;
