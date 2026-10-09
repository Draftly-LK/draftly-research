import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { C, FONT, FPS } from "../theme";

// The section's on-screen text line, from the script. Shown over footage for a
// few seconds, or kept up with `hold` for graphic scenes.
export const OnScreen: React.FC<{ text: string; seconds?: number; hold?: boolean; top?: number }> = ({
  text,
  seconds = 4.5,
  hold = false,
  top = 44,
}) => {
  const frame = useCurrentFrame();
  const end = seconds * FPS;
  const o = hold
    ? interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" })
    : Math.min(
        interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" }),
        interpolate(frame, [end - 12, end], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
      );
  if (!hold && frame > end) return null;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top, display: "flex", justifyContent: "center", opacity: o, zIndex: 20 }}>
      <div
        style={{
          fontFamily: FONT.display,
          fontWeight: 600,
          fontSize: 50,
          color: C.navyMid,
          background: C.cream,
          border: `2px solid ${C.amberBorder}`,
          borderRadius: 18,
          padding: "12px 34px",
          boxShadow: "0 10px 28px rgba(11,22,40,0.28)",
        }}
      >
        {text}
      </div>
    </div>
  );
};

// Same line, for dark graphic scenes.
export const OnScreenDark: React.FC<{ text: string; top?: number }> = ({ text, top = 56 }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top, textAlign: "center", opacity: o, zIndex: 20 }}>
      <span style={{ fontFamily: FONT.display, fontWeight: 600, fontSize: 56, color: C.cream }}>{text}</span>
    </div>
  );
};
