import React from 'react';
import {Audio} from '@remotion/media';
import {Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';
import {Opening} from '../film/Opening';
import {FilmBase, clamp} from '../film/style';
import {ChecklistConcept, OverviewConcept} from './ChecklistConcept';
import {ClosingScene} from './ClosingScene';
import {PeopleSection} from './PeopleSection';
import {ScatteredScene} from './ScatteredScene';
import {DocumentsScene, DraftScene, ResearchScene} from './RecordedScenes';
import {at, timing} from './timing';

export const WorkflowFilm: React.FC = () => {
  const {fps}=useVideoConfig();
  return <FilmBase>
    <Sequence name="Preserved original intro" durationInFrames={timing.intro*fps}><Opening/></Sequence>
    <Sequence name="Scattered information" from={at.problem*fps} durationInFrames={timing.problem*fps}><ScatteredScene/></Sequence>
    <Sequence name="Practitioner contributions" from={at.people*fps} durationInFrames={timing.people*fps}><PeopleSection/></Sequence>
    <Sequence name="Documents and source review" from={at.documents*fps} durationInFrames={timing.documents*fps}><DocumentsScene/></Sequence>
    <Sequence name="Living checklist — concept" from={at.checklist*fps} durationInFrames={timing.checklist*fps}><ChecklistConcept/></Sequence>
    <Sequence name="Inspect legal sources" from={at.research*fps} durationInFrames={timing.research*fps}><ResearchScene/></Sequence>
    <Sequence name="Working draft review" from={at.draft*fps} durationInFrames={timing.draft*fps}><DraftScene/></Sequence>
    <Sequence name="Remaining work — concept" from={at.overview*fps} durationInFrames={timing.overview*fps}><OverviewConcept/></Sequence>
    <Sequence name="Draftly closing" from={at.closing*fps} durationInFrames={timing.closing*fps}><ClosingScene/></Sequence>
    <Sequence name="Continuation score" from={at.problem*fps} durationInFrames={60*fps}>
      <Audio src={staticFile('sound/score.wav')} trimBefore={9*fps} volume={f=>interpolate(f,[0,.7*fps,11.5*fps,12*fps,19.5*fps,20*fps,38*fps,38.5*fps,58.8*fps,60*fps],[0,.14,.14,.09,.09,.13,.13,.08,.12,0],clamp)}/>
    </Sequence>
    <Sequence from={Math.round((at.problem+.35)*fps)} durationInFrames={2*fps}><Audio src={staticFile('sound/page.wav')} volume={.19}/></Sequence>
    <Sequence from={Math.round((at.checklist+5.2)*fps)} durationInFrames={fps}><Audio src={staticFile('sound/click.wav')} volume={.16}/></Sequence>
    <Sequence from={(at.checklist+14.4)*fps} durationInFrames={fps}><Audio src={staticFile('sound/pen.wav')} volume={.2}/></Sequence>
  </FilmBase>;
};
