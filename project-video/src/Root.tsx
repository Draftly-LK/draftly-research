import React from "react";
import { Composition } from "remotion";
import { Demo } from "./Demo";
import { TOTAL_SECONDS } from "./script";
import { FPS } from "./theme";

export const RemotionRoot: React.FC = () => (
  <Composition id="DraftlyDemo" component={Demo} durationInFrames={TOTAL_SECONDS * FPS} fps={FPS} width={1920} height={1080} />
);
