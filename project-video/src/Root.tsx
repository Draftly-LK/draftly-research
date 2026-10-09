import React from "react";
import { Composition } from "remotion";
import { Opening } from "./film/Opening";
import {Film} from './film/Film';
import {TOTAL_SECONDS} from './film/edit';
import {WorkflowFilm} from './continuation/WorkflowFilm';
import {FILM_SECONDS} from './continuation/timing';
import {ContinuationReview} from './continuation/ContinuationReview';
const FPS = 30;

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="DraftlyOpening" component={Opening} durationInFrames={45 * FPS} fps={FPS} width={1920} height={1080} />
    <Composition id="DraftlyDemo" component={Film} durationInFrames={TOTAL_SECONDS * FPS} fps={FPS} width={1920} height={1080} />
    <Composition id="DraftlyWorkflowFilm" component={WorkflowFilm} durationInFrames={FILM_SECONDS * FPS} fps={FPS} width={1920} height={1080} />
    <Composition id="DraftlyContinuationReview" component={ContinuationReview} durationInFrames={45 * FPS} fps={FPS} width={1920} height={1080} />
  </>
);
