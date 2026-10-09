import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const center = { x: 960, y: 450 };
const edge = Array.from({ length: 24 }, (_, i) => {
  const angle = (i / 24) * Math.PI * 2;
  const radius = Math.min(1020 / Math.max(Math.abs(Math.cos(angle)), 0.001), 690 / Math.max(Math.abs(Math.sin(angle)), 0.001));
  return { x: center.x + Math.cos(angle) * radius, y: center.y + Math.sin(angle) * radius, angle };
});

export const LightningGlass: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const strike = Math.round(fps * 1.1);
  const age = frame - strike;
  const bolt = interpolate(age, [-3, 0, 5, 9], [0, 1, 0.85, 0], clamp);
  const flash = interpolate(age, [0, 2, 8], [0.65, 0.2, 0], clamp);
  const fly = interpolate(age, [8, fps * 1.5], [0, 1], clamp);
  const glass = interpolate(age, [0, 3, fps * 1.1, fps * 1.6], [0, 1, 0.65, 0], clamp);
  const shake = age >= 0 && age < 15 ? Math.sin(age * 2.7) * (15 - age) : 0;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden", transform: `translate(${shake}px, ${shake * 0.45}px)` }}>
      <svg viewBox="0 0 1920 1080" width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
        <defs>
          <filter id="draftly-lightning-glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="12" /></filter>
          <linearGradient id="draftly-glass" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#e2f5ff" stopOpacity="0.18" /><stop offset="0.5" stopColor="#9bd8ff" stopOpacity="0.025" /><stop offset="1" stopColor="#ffffff" stopOpacity="0.3" /></linearGradient>
        </defs>
        <g opacity={bolt} fill="none" strokeLinejoin="miter">
          <path d="M 1230 -40 L 1100 120 L 1170 140 L 1010 270 L 1070 280 L 960 450 M 1010 270 L 870 220 L 780 290 M 1100 120 L 1350 220 L 1290 290" stroke="#63bcff" strokeWidth="24" filter="url(#draftly-lightning-glow)" />
          <path d="M 1230 -40 L 1100 120 L 1170 140 L 1010 270 L 1070 280 L 960 450" stroke="#f4fcff" strokeWidth="5" />
          <path d="M 1010 270 L 870 220 L 780 290 M 1100 120 L 1350 220 L 1290 290" stroke="#b4e7ff" strokeWidth="3" />
        </g>
        <rect width="1920" height="1080" fill="#d9f2ff" opacity={age >= 0 ? flash : 0} />
        <g opacity={glass}>
          {edge.map((point, i) => {
            const next = edge[(i + 1) % edge.length];
            const angle = point.angle + Math.PI / 24;
            const distance = fly * (550 + (i % 4) * 130);
            const dx = Math.cos(angle) * distance;
            const dy = Math.sin(angle) * distance + fly * fly * 360;
            const rotation = fly * ((i % 2 ? 1 : -1) * (18 + i % 7 * 8));
            const midX = (center.x + point.x + next.x) / 3;
            const midY = (center.y + point.y + next.y) / 3;
            const kinkX = center.x + (point.x - center.x) * 0.42 + Math.sin(i * 3) * 35;
            const kinkY = center.y + (point.y - center.y) * 0.42;
            return <g key={i} transform={`translate(${dx} ${dy}) rotate(${rotation} ${midX} ${midY})`}>
              <path d={`M ${center.x} ${center.y} L ${kinkX} ${kinkY} L ${point.x} ${point.y} L ${next.x} ${next.y} Z`} fill="url(#draftly-glass)" stroke="#d9f4ff" strokeOpacity="0.65" strokeWidth="1.6" />
              <path d={`M ${kinkX} ${kinkY} l ${Math.cos(angle + 1) * 85} ${Math.sin(angle + 1) * 85}`} fill="none" stroke="#e4f6ff" strokeOpacity="0.55" strokeWidth="1" />
            </g>;
          })}
        </g>
      </svg>
    </AbsoluteFill>
  );
};