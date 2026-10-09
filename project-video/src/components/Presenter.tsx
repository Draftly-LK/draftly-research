import { Video } from "@remotion/media";
import React from "react";
import { interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { CAMERA } from "../media";
import { C, FONT } from "../theme";

type Member = keyof typeof CAMERA;

// Picture-in-picture presenter: the member's camera clip if supplied,
// otherwise a placeholder that says what to record.
export const Presenter: React.FC<{ member: Member; durationInFrames: number; corner?: "right" | "left" }> = ({
  member,
  durationInFrames,
  corner = "right",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 200 } });
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const src = CAMERA[member];
  const size = 300;
  return (
    <div
      style={{
        position: "absolute",
        top: 150,
        [corner]: 56,
        width: size,
        opacity: enter * exit,
        transform: `translateY(${(1 - enter) * 30}px)`,
        fontFamily: FONT.ui,
      }}
    >
      <div
        style={{
          width: size,
          height: size,
          borderRadius: "50%",
          overflow: "hidden",
          border: `4px solid ${C.gold}`,
          background: C.navy,
          boxShadow: "0 10px 30px rgba(11,22,40,0.35)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {src ? (
          <Video src={staticFile(src)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <div style={{ color: C.cream, textAlign: "center", fontSize: 22, lineHeight: 1.35, padding: 30 }}>
            <div style={{ fontSize: 40, marginBottom: 8 }}>●</div>
            Camera clip
            <br />
            goes here
          </div>
        )}
      </div>
      <div
        style={{
          marginTop: 14,
          textAlign: "center",
          color: C.white,
          background: "rgba(11,22,40,0.86)",
          borderRadius: 999,
          padding: "8px 18px",
          fontSize: 24,
          fontWeight: 600,
        }}
      >
        {member}
      </div>
    </div>
  );
};
