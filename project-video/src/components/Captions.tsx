import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { C, FONT } from "../theme";
import { lineSpans } from "../timing";

// Burned-in captions. Lines share the section's time in proportion to their
// length, which matches spoken pace closely enough for review drafts.
export const Captions: React.FC<{ lines: string[]; startFrame: number; endFrame: number; narrator?: string; position?: "top" | "bottom" }> = ({
  lines,
  startFrame,
  endFrame,
  narrator,
  position = "bottom",
}) => {
  const frame = useCurrentFrame();
  const timed = lineSpans(lines, startFrame, endFrame).map((sp, i) => ({ text: lines[i], ...sp }));
  const current = timed.find((t) => frame >= t.from && frame < t.to);
  if (!current) return null;
  const fade = Math.min(
    interpolate(frame, [current.from, current.from + 6], [0, 1], { extrapolateRight: "clamp" }),
    interpolate(frame, [current.to - 6, current.to], [1, 0], { extrapolateLeft: "clamp" }),
  );
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        ...(position === "top" ? { top: 120 } : { bottom: 56 }),
        display: "flex",
        justifyContent: "center",
        opacity: fade,
      }}
    >
      <div
        style={{
          maxWidth: 1400,
          padding: "14px 28px",
          borderRadius: 14,
          background: "rgba(11, 22, 40, 0.86)",
          color: C.white,
          fontFamily: FONT.ui,
          fontSize: 36,
          lineHeight: 1.35,
          textAlign: "center",
          boxShadow: "0 6px 24px rgba(11,22,40,0.25)",
        }}
      >
        {narrator ? (
          <span style={{ color: C.gold, fontWeight: 600, marginRight: 12, fontSize: 26, letterSpacing: 0.4 }}>
            {narrator.toUpperCase()}
          </span>
        ) : null}
        {current.text}
      </div>
    </div>
  );
};
