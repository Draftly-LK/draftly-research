import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Backdrop } from "./Backdrop";
import { C, FONT } from "../theme";

// Section opener on the navy backdrop: kicker in gold, title in the display serif.
export const TitleCard: React.FC<{ kicker: string; title: string; narrator?: string; durationInFrames: number }> = ({
  kicker,
  title,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rise = spring({ frame, fps, config: { damping: 200 } });
  const out = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const rule = interpolate(frame, [6, 30], [0, 160], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: out }}>
      <Backdrop />
      <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 180, fontFamily: FONT.ui }}>
        <div style={{ transform: `translateY(${(1 - rise) * 40}px)`, opacity: rise }}>
          <div style={{ color: C.gold, fontSize: 30, fontWeight: 600, letterSpacing: 3, textTransform: "uppercase" }}>
            {kicker}
          </div>
          <div style={{ height: 3, width: rule, background: C.gold, margin: "22px 0 30px" }} />
          <div style={{ color: C.white, fontFamily: FONT.display, fontWeight: 600, fontSize: 92, lineHeight: 1.08, maxWidth: 1400 }}>
            {title}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
