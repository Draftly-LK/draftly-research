import { Video } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  Easing,
  Freeze,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from "remotion";
import durations from "../footage.json";
import { Backdrop } from "./Backdrop";
import { FileExplorer } from "./FileExplorer";
import { C, FONT, FPS } from "../theme";

export interface Zoom {
  scale: number;
  x: number; // focal point, 0..1 of the frame width
  y: number; // focal point, 0..1 of the frame height
}

export interface Segment {
  clip: string; // file in public/footage, without .mp4
  from?: number; // seconds into the clip
  to?: number;
  zoom?: Zoom;
  label?: string; // small pill shown over this segment
  rate?: number; // force a playback rate for this segment
  hold?: number; // seconds: freeze the frame at `from` instead of playing
  overlay?: "fileExplorer"; // drawn over a held frame
  crop?: { y: number; h: number; caption?: string }; // show only a horizontal strip, on the navy backdrop
}

const clipLength = (clip: string): number => {
  const d = (durations as Record<string, number>)[clip];
  if (d === undefined) throw new Error(`No duration for clip ${clip}; run scripts/probe-footage`);
  return d;
};

export interface Planned extends Segment {
  start: number; // frame in the section
  frames: number;
  rate: number;
  fromS: number;
  toS: number;
}

// Lay segments end to end. Segments without a forced rate share one rate,
// chosen so the whole fits; spare time freezes on the last frame.
export function plan(segments: Segment[], available: number): Planned[] {
  const spans = segments.map((s) => ({ s, fromS: s.from ?? 0, toS: s.hold ? (s.from ?? 0) + s.hold : s.to ?? clipLength(s.clip) }));
  const forced = spans.filter((x) => x.s.rate || x.s.hold);
  const forcedFrames = forced.reduce((n, x) => n + ((x.toS - x.fromS) / (x.s.hold ? 1 : x.s.rate!)) * FPS, 0);
  const free = spans.filter((x) => !x.s.rate && !x.s.hold);
  const freeSeconds = free.reduce((n, x) => n + (x.toS - x.fromS), 0);
  const freeAvail = Math.max(1, available - forcedFrames) / FPS;
  const shared = freeSeconds > 0 ? Math.max(1, freeSeconds / freeAvail) : 1;
  let at = 0;
  return spans.map(({ s, fromS, toS }) => {
    const rate = s.hold ? 1 : s.rate ?? shared;
    const frames = Math.max(1, Math.round(((toS - fromS) / rate) * FPS));
    const p = { ...s, start: at, frames, rate, fromS, toS };
    at += frames;
    return p;
  });
}

const ZoomBox: React.FC<{ zoom?: Zoom; frames: number; children: React.ReactNode }> = ({ zoom, frames, children }) => {
  const frame = useCurrentFrame();
  if (!zoom) return <AbsoluteFill>{children}</AbsoluteFill>;
  const ease = Easing.bezier(0.4, 0, 0.2, 1);
  const k = Math.min(
    interpolate(frame, [0, 24], [0, 1], { extrapolateRight: "clamp", easing: ease }),
    interpolate(frame, [frames - 24, frames], [1, 0], { extrapolateLeft: "clamp", easing: ease }),
  );
  const scale = 1 + (zoom.scale - 1) * k;
  return (
    <AbsoluteFill style={{ transform: `scale(${scale})`, transformOrigin: `${zoom.x * 100}% ${zoom.y * 100}%` }}>
      {children}
    </AbsoluteFill>
  );
};

const Pill: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute",
        top: 28,
        right: 40,
        opacity: o,
        background: C.cream,
        color: C.navyMid,
        border: `2px solid ${C.amberBorder}`,
        borderRadius: 999,
        padding: "10px 22px",
        fontFamily: FONT.ui,
        fontSize: 26,
        fontWeight: 600,
        boxShadow: "0 6px 18px rgba(11,22,40,0.25)",
      }}
    >
      {text}
    </div>
  );
};

export const Footage: React.FC<{ segments: Segment[]; durationInFrames: number }> = ({ segments, durationInFrames }) => {
  const planned = plan(segments, durationInFrames);
  const used = planned.reduce((n, p) => n + p.frames, 0);
  const last = planned[planned.length - 1];
  const tail = Math.max(0, durationInFrames - used);
  return (
    <AbsoluteFill style={{ background: C.paper }}>
      {planned.map((p, i) => (
        <Sequence key={i} from={p.start} durationInFrames={p.frames + (p === last ? tail : 0)}>
          <ZoomBox zoom={p.zoom} frames={p.frames + (p === last ? tail : 0)}>
            <Strip crop={p.crop}>
              {p.hold ? (
                <Freeze frame={0}>
                  <Video src={staticFile(`footage/${p.clip}.mp4`)} trimBefore={Math.round(p.fromS * FPS)} muted />
                </Freeze>
              ) : p === last && tail > 0 ? (
                <TailFreeze p={p} />
              ) : (
                <Video
                  src={staticFile(`footage/${p.clip}.mp4`)}
                  trimBefore={Math.round(p.fromS * FPS)}
                  trimAfter={Math.round(p.toS * FPS)}
                  playbackRate={p.rate}
                  muted
                />
              )}
            </Strip>
          </ZoomBox>
          {p.overlay === "fileExplorer" ? <FileExplorer durationInFrames={p.frames} /> : null}
          {p.label ? <Pill text={p.label} /> : null}
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

// A horizontal strip of the frame, centred on the navy backdrop, at full sharpness.
const Strip: React.FC<{ crop?: Segment["crop"]; children: React.ReactNode }> = ({ crop, children }) => {
  const frame = useCurrentFrame();
  if (!crop) return <AbsoluteFill>{children}</AbsoluteFill>;
  const top = (1080 - crop.h) / 2 + (crop.caption ? 50 : 0);
  const o = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <Backdrop />
      {crop.caption ? (
        <div style={{ position: "absolute", top: top - 110, width: "100%", textAlign: "center", color: C.white, fontFamily: FONT.display, fontSize: 64, fontWeight: 600, opacity: o }}>
          {crop.caption}
        </div>
      ) : null}
      <div style={{ position: "absolute", top, left: 0, width: 1920, height: crop.h, overflow: "hidden", boxShadow: "0 18px 50px rgba(0,0,0,0.45)", opacity: o }}>
        <div style={{ position: "absolute", top: -crop.y, left: 0, width: 1920, height: 1080 }}>{children}</div>
      </div>
    </AbsoluteFill>
  );
};

// The last segment plays, then holds its final frame for the spare time.
const TailFreeze: React.FC<{ p: Planned }> = ({ p }) => {
  const frame = useCurrentFrame();
  const video = (
    <Video
      src={staticFile(`footage/${p.clip}.mp4`)}
      trimBefore={Math.round(p.fromS * FPS)}
      trimAfter={Math.round(p.toS * FPS)}
      playbackRate={p.rate}
      muted
    />
  );
  return frame < p.frames - 1 ? video : <Freeze frame={p.frames - 1}>{video}</Freeze>;
};
