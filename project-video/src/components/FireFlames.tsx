import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

// Frame-driven animation keeps Studio playback and exported frames identical.
export const FireFlames: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const time = frame / fps;
  const fade = interpolate(frame, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity: fade, overflow: "hidden" }}>
      <svg viewBox="0 0 1920 1080" width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="draftly-flame" x1="0" y1="1" x2="0" y2="0">
            <stop offset="0" stopColor="#ff4b08" stopOpacity="0.8" />
            <stop offset="0.45" stopColor="#ff9d22" stopOpacity="0.65" />
            <stop offset="1" stopColor="#ffe8a0" stopOpacity="0" />
          </linearGradient>
          <radialGradient id="draftly-fire-glow">
            <stop stopColor="#ff6b12" stopOpacity="0.45" />
            <stop offset="1" stopColor="#ff6b12" stopOpacity="0" />
          </radialGradient>
          <filter id="draftly-fire-soft"><feGaussianBlur stdDeviation="8" /></filter>
        </defs>
        <ellipse cx="960" cy="1120" rx="1250" ry="380" fill="url(#draftly-fire-glow)" />
        <g filter="url(#draftly-fire-soft)">
          {Array.from({ length: 28 }, (_, i) => {
            const x = i * 74 - 40;
            const phase = time * 3.2 + i * 2.39;
            const height = 150 + 95 * (0.5 + 0.5 * Math.sin(phase)) + (i % 4) * 23;
            const sway = Math.sin(phase * 0.8) * 34;
            const tip = 1080 - height;
            return <path key={i} d={`M ${x - 60} 1100 C ${x - 95} ${1080 - height * 0.4}, ${x + sway + 40} ${tip + 70}, ${x + sway} ${tip} C ${x + sway - 18} ${tip + 110}, ${x + 100} ${1080 - height * 0.45}, ${x + 65} 1100 Z`} fill="url(#draftly-flame)" />;
          })}
        </g>
        {Array.from({ length: 65 }, (_, i) => {
          const progress = ((time * (0.15 + (i % 5) * 0.025) + i * 0.618) % 1);
          const x = ((i * 137.51) % 1920) + Math.sin(time * 1.5 + i) * 26;
          const y = 1100 - progress * 1050;
          const opacity = Math.sin(progress * Math.PI) * 0.75;
          return <ellipse key={i} cx={x} cy={y} rx={1.5 + i % 3} ry={3 + i % 4} fill={i % 3 ? "#ffba52" : "#fff0bc"} opacity={opacity} transform={`rotate(${Math.sin(time + i) * 22} ${x} ${y})`} />;
        })}
      </svg>
    </AbsoluteFill>
  );
};