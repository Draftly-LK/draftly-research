import React from 'react';
import {Audio} from '@remotion/media';
import {Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';
import {FilmBase, clamp, palette} from '../film/style';
import {ScatteredScene} from './ScatteredScene';
import {PeopleSection} from './PeopleSection';
import {ChecklistConcept, OverviewConcept} from './ChecklistConcept';
import {ResearchScene} from './RecordedScenes';
import {ClosingScene} from './ClosingScene';

/** A review reel of completed visuals; excludes the pending capture scenes. */
export const ContinuationReview: React.FC = () => {
 const {fps}=useVideoConfig();
 return <FilmBase>
  <Sequence durationInFrames={6*fps}><ScatteredScene/></Sequence>
  <Sequence from={6*fps} durationInFrames={6*fps}><PeopleSection/></Sequence>
  <Sequence from={12*fps} durationInFrames={18*fps}><ChecklistConcept/></Sequence>
  <Sequence from={30*fps} durationInFrames={7*fps}><ResearchScene/></Sequence>
  <Sequence from={37*fps} durationInFrames={5*fps}><OverviewConcept/></Sequence>
  <Sequence from={42*fps} durationInFrames={3*fps}><ClosingScene/></Sequence>
  <Audio src={staticFile('sound/score.wav')} trimBefore={9*fps} volume={f=>interpolate(f,[0,.7*fps,43.5*fps,45*fps],[0,.12,.12,0],clamp)}/>
  <div style={{position:'absolute',left:96,bottom:15,fontSize:20,color:palette.muted}}>EDIT PREVIEW · product capture scenes pending</div>
 </FilmBase>;
};
