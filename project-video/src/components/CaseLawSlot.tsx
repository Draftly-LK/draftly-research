import { Video } from "@remotion/media";
import React from "react";
import { AbsoluteFill, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Backdrop } from "./Backdrop";
import { CASE_LAW_CLIP } from "../media";
import { C, FONT } from "../theme";

// Case-law search runs on the hosted site only (it needs the retrieval
// service). Until that clip is recorded, this card says what goes here.
export const CaseLawSlot: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const o = Math.min(
    interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" }),
    interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], { extrapolateLeft: "clamp" }),
  );
  if (CASE_LAW_CLIP) {
    return (
      <AbsoluteFill style={{ opacity: o }}>
        <Video src={staticFile(CASE_LAW_CLIP)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{ opacity: o }}>
      <Backdrop />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", fontFamily: FONT.ui, textAlign: "center" }}>
        <div style={{ color: C.gold, fontSize: 30, fontWeight: 600, letterSpacing: 3 }}>CASE LAW</div>
        <div style={{ color: C.white, fontFamily: FONT.display, fontSize: 76, fontWeight: 600, margin: "18px 0 26px" }}>
          9,601 judgments in the catalogue
        </div>
        <div style={{ color: C.cream, fontSize: 34, lineHeight: 1.5 }}>
          Similar-case search over 5,121 conveyancing cases
          <br />
          Every result marked as an unverified research lead
        </div>
        <div style={{ marginTop: 40, color: C.muted, fontSize: 22, border: `1px dashed ${C.muted}`, borderRadius: 12, padding: "10px 20px" }}>
          Placeholder: replace with the live-site screen recording (media.ts → CASE_LAW_CLIP)
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
