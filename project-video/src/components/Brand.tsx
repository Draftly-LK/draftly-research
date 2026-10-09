import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Backdrop } from "./Backdrop";
import { C, FONT } from "../theme";

export const Wordmark: React.FC<{ scale?: number; enter?: number }> = ({ scale = 1, enter = 1 }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 34 * scale, opacity: enter }}>
    <Img src={staticFile("brand/logo-tw-white.png")} style={{ width: 210 * scale, height: 210 * scale, transform: `translateY(${(1 - enter) * 20}px)` }} />
    <div>
      <div style={{ fontFamily: FONT.display, fontWeight: 700, color: C.white, fontSize: 150 * scale, lineHeight: 1 }}>Draftly</div>
      <div style={{ fontFamily: FONT.ui, color: C.gold, fontSize: 34 * scale, letterSpacing: 6 * scale, marginTop: 10 * scale, fontWeight: 600 }}>
        NOTARIAL WORKSPACE
      </div>
    </div>
  </div>
);

// Logo reveal used at the start of "Meet Draftly".
export const LogoReveal: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - 6, fps, config: { damping: 200 } });
  const out = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const line = interpolate(frame, [30, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: out }}>
      <Backdrop />

      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column" }}>
        <Wordmark enter={enter} />
        <div style={{ marginTop: 60, fontFamily: FONT.ui, color: C.cream, fontSize: 40, opacity: line, textAlign: "center", lineHeight: 1.5 }}>
          Sri Lankan notarial and conveyancing work
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Closing: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const logo = spring({ frame, fps, config: { damping: 200 } });
  const fadeEnd = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: fadeEnd }}>
      <Backdrop />
      <AbsoluteFill style={{ alignItems: "center", paddingTop: 90 }}>
        <Wordmark scale={0.62} enter={logo} />
        <div style={{ marginTop: 34, fontFamily: FONT.display, color: C.cream, fontSize: 52, fontWeight: 600 }}>
          Follow the evidence. Keep the lawyer in control.
        </div>
        <div
          style={{
            position: "absolute", top: 700, left: 0, right: 0, textAlign: "center", fontFamily: FONT.ui, color: C.muted, fontSize: 22, lineHeight: 1.6,
            opacity: interpolate(frame, [6 * fps, 7 * fps], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          }}
        >
          Group 06 · Department of Computer Science and Engineering, University of Moratuwa · Mentor: Dr. Nisansa de Silva
          <br />
          Demo recorded with synthetic data only. Draftly supports lawyers; it does not give legal advice.
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
