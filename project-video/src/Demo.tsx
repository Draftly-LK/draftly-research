import { Audio } from "@remotion/media";
import React from "react";
import { AbsoluteFill, interpolate, Sequence, staticFile, useCurrentFrame } from "remotion";
import { Closing } from "./components/Brand";
import { CaseLawSlot } from "./components/CaseLawSlot";
import { Captions } from "./components/Captions";
import { Footage, Segment } from "./components/Footage";
import { OnScreen } from "./components/OnScreen";
import { Problem } from "./components/Problem";
import { BundleScene, CompareScene, DifferenceScene, MontageScene, RetrievalGraphic, WhyScene } from "./components/Scenes";
import { MUSIC, SECTION_MEDIA, SHOW_CAPTIONS } from "./media";
import { SCRIPT, ScriptSection } from "./script";
import { FPS } from "./theme";
import { lineSpans } from "./timing";

const PREPARED = "Prepared extraction demo";

// Footage per section (draftly-video-script-updated.md). Rates are fitted
// automatically unless forced.
export const SEGMENTS: Record<string, Segment[]> = {
  matter: [
    { clip: "02-intake", to: 48.6 },
    { clip: "02-intake", from: 48.6, hold: 6.2, overlay: "fileExplorer" },
    { clip: "02-intake", from: 49.7, to: 59.5 },
  ],
  verify: [
    { clip: "03-process", to: 18, rate: 0.9, label: PREPARED },
    { clip: "03-process", from: 18, rate: 0.9, zoom: { scale: 1.3, x: 0.62, y: 0.5 }, label: PREPARED },
    { clip: "04-review", to: 9, rate: 0.9, label: PREPARED },
    { clip: "04-review", from: 9, rate: 0.9, zoom: { scale: 1.18, x: 0.78, y: 0.55 }, label: PREPARED },
    { clip: "05-facts", from: 13.5, zoom: { scale: 1.6, x: 0.55, y: 0.38 } },
  ],
  difference: [
    { clip: "06-checks", rate: 0.85 },
    { clip: "07-checks-passing", zoom: { scale: 1.5, x: 0.55, y: 0.32 } },
  ],
  instrument: [
    { clip: "10-draft", rate: 0.85 },
    { clip: "11-draft-confirm-a", rate: 0.85 },
    { clip: "12-draft-confirm-b", rate: 0.85 },
  ],
  status: [
    { clip: "13-preflight", from: 3, to: 34 },
    { clip: "15-export", from: 2, to: 8 },
    { clip: "15-export", from: 30, to: 49 },
  ],
};

const FadeIn: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  return <AbsoluteFill style={{ opacity: interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" }) }}>{children}</AbsoluteFill>;
};

const Clip: React.FC<{ segments: Segment[]; durationInFrames: number; onScreen?: string }> = ({ segments, durationInFrames, onScreen }) => (
  <FadeIn>
    <Footage segments={segments} durationInFrames={durationInFrames} />
    {onScreen ? <OnScreen text={onScreen} /> : null}
  </FadeIn>
);

const SectionView: React.FC<{ s: ScriptSection }> = ({ s }) => {
  const total = s.seconds * FPS;
  const audio = SECTION_MEDIA[s.id]?.audio;
  const spans = lineSpans(s.lines, 0, total - 8);
  let body: React.ReactNode;

  switch (s.id) {
    case "problem":
      body = <Problem durationInFrames={total} />;
      break;
    case "why":
      body = <WhyScene d={total} />;
      break;
    case "bundle":
      body = <BundleScene d={total} />;
      break;
    case "compare":
      body = <CompareScene d={total} />;
      break;
    case "difference": {
      const g = spans[2].to;
      body = (
        <>
          <Sequence durationInFrames={g}>
            <DifferenceScene d={g} spans={spans} />
          </Sequence>
          <Sequence from={g} durationInFrames={total - g}>
            <Clip segments={SEGMENTS.difference} durationInFrames={total - g} />
          </Sequence>
        </>
      );
      break;
    }
    case "research": {
      const a = spans[2].to; // scope and catalogue
      const b = spans[4].to; // the retrieval challenge
      const c = spans[6].to; // a citation opened
      const e = spans[7].to; // case law
      body = (
        <>
          <Sequence durationInFrames={a}>
            <Clip segments={[{ clip: "18-research-scope", rate: 0.55 }, { clip: "17-legal-sources", from: 1.5, to: 14 }]} durationInFrames={a} />
          </Sequence>
          <Sequence from={a} durationInFrames={b - a}>
            <RetrievalGraphic d={b - a} mode="overview" />
          </Sequence>
          <Sequence from={b} durationInFrames={c - b}>
            <Clip segments={[{ clip: "19-citation" }]} durationInFrames={c - b} />
          </Sequence>
          <Sequence from={c} durationInFrames={e - c}>
            <CaseLawSlot durationInFrames={e - c} />
          </Sequence>
          <Sequence from={e} durationInFrames={total - e}>
            <RetrievalGraphic d={total - e} mode="evaluate" />
          </Sequence>
        </>
      );
      break;
    }
    case "closing": {
      const m = spans[2].to;
      body = (
        <>
          <Sequence durationInFrames={m}>
            <MontageScene d={m} />
          </Sequence>
          <Sequence from={m} durationInFrames={total - m}>
            <Closing durationInFrames={total - m} />
          </Sequence>
        </>
      );
      break;
    }
    default:
      body = <Clip segments={SEGMENTS[s.id]} durationInFrames={total} onScreen={s.onScreen} />;
  }

  return (
    <AbsoluteFill>
      {body}
      {SHOW_CAPTIONS ? <Captions lines={s.lines} startFrame={0} endFrame={total - 8} position="bottom" /> : null}
      {audio ? <Audio src={staticFile(audio)} /> : null}
    </AbsoluteFill>
  );
};

export const Demo: React.FC = () => {
  let at = 0;
  return (
    <AbsoluteFill style={{ background: "#0B1628" }}>
      {SCRIPT.map((s) => {
        const from = at;
        at += s.seconds * FPS;
        return (
          <Sequence key={s.id} from={from} durationInFrames={s.seconds * FPS} name={s.title}>
            <SectionView s={s} />
          </Sequence>
        );
      })}
      {MUSIC ? <Audio src={staticFile(MUSIC)} volume={0.08} /> : null}
    </AbsoluteFill>
  );
};
