import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C } from "../theme";

// The navy surface: one diagonal gradient under faint "land parcel" lines,
// white at 7%, drawn once and scaled to fit (never tiled).
const PARCELS = [
  "M0 210 L340 160 L420 420 L60 470 Z",
  "M340 160 L760 120 L820 380 L420 420 Z",
  "M760 120 L1180 70 L1240 330 L820 380 Z",
  "M1180 70 L1640 40 L1700 300 L1240 330 Z",
  "M1640 40 L1920 20 L1920 290 L1700 300 Z",
  "M60 470 L420 420 L470 700 L20 760 Z",
  "M420 420 L820 380 L900 650 L470 700 Z",
  "M820 380 L1240 330 L1300 620 L900 650 Z",
  "M1240 330 L1700 300 L1760 600 L1300 620 Z",
  "M1700 300 L1920 290 L1920 590 L1760 600 Z",
  "M20 760 L470 700 L520 1080 L0 1080 Z",
  "M470 700 L900 650 L980 1080 L520 1080 Z",
  "M900 650 L1300 620 L1380 1080 L980 1080 Z",
  "M1300 620 L1760 600 L1820 1080 L1380 1080 Z",
  "M1760 600 L1920 590 L1920 1080 L1820 1080 Z",
  "M0 0 L1920 0 L1920 20 L1640 40 L1180 70 L760 120 L340 160 L0 210 Z",
];

export const Backdrop: React.FC<{ drift?: boolean }> = ({ drift = true }) => {
  const frame = useCurrentFrame();
  const shift = drift ? interpolate(frame, [0, 900], [0, -40], { extrapolateRight: "clamp" }) : 0;
  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(135deg, #1B3156 0%, ${C.navyMid} 55%, ${C.navyDeep} 100%)`,
      }}
    >
      <svg
        viewBox="0 0 1920 1080"
        preserveAspectRatio="xMidYMid slice"
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", transform: `translateX(${shift}px) scale(1.04)` }}
      >
        {PARCELS.map((d, i) => (
          <path key={i} d={d} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={1.2} />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
