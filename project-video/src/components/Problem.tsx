import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { SCRIPT } from "../script";
import { lineSpans } from "../timing";
import { C, FONT } from "../theme";
import { Backdrop } from "./Backdrop";
import { OnScreenDark } from "./OnScreen";

// Section 1. The synthetic bundle arrives, the workflow behind the request is
// listed, the information is scattered, and one property detail is checked and
// copied across. Each change lands on the spoken line it illustrates.

const LINES = SCRIPT[0].lines;
const DOCS = [
  { file: "synthetic-identity-card.png", label: "Identity document", x: 330, y: 360, r: -5, tag: "Scanned page" },
  { file: "synthetic-survey-plan.png", label: "Survey plan", x: 740, y: 400, r: 3, tag: "Handwritten entry" },
  { file: "synthetic-title-certificate.png", label: "Title certificate", x: 1150, y: 360, r: -3, tag: "Sinhala · Tamil · English" },
  { file: "synthetic-form8-instrument.png", label: "Form 8 transfer instrument", x: 1560, y: 400, r: 4, tag: "" },
];
const CHIPS = ["Read", "Identify parties", "Compare details", "Examine records", "Find the law", "Prepare instrument"];
const CARD_W = 400;

const Card: React.FC<{ d: (typeof DOCS)[number]; enter: number; dim: number; ring?: number }> = ({ d, enter, dim, ring = 0 }) => (
  <div
    style={{
      position: "absolute",
      left: d.x - CARD_W / 2,
      top: d.y - 160 + (1 - enter) * -520,
      width: CARD_W,
      transform: `rotate(${d.r * enter}deg)`,
      opacity: enter * dim,
      filter: "drop-shadow(0 18px 30px rgba(0,0,0,0.4))",
    }}
  >
    <Img src={staticFile(`docs/${d.file}`)} style={{ width: CARD_W, display: "block", borderRadius: 8 }} />
    <div style={{ marginTop: 10, textAlign: "center", fontFamily: FONT.ui, fontSize: 24, fontWeight: 600, color: C.cream }}>{d.label}</div>
    {ring > 0 ? (
      <div
        style={{
          position: "absolute",
          left: 14,
          top: 172,
          width: 150,
          height: 22,
          borderRadius: 11,
          border: `3px solid ${C.gold}`,
          opacity: ring,
          boxShadow: `0 0 18px ${C.gold}`,
        }}
      />
    ) : null}
  </div>
);

const Chip: React.FC<{ text: string; at: number; frame: number; x: number; y: number; gold?: boolean }> = ({ text, at, frame, x, y, gold }) => {
  const { fps } = useVideoConfig();
  const e = spring({ frame: frame - at, fps, config: { damping: 18 } });
  return (
    <div
      style={{
        position: "absolute", left: x, top: y + (1 - e) * 30, opacity: e, transform: "translateX(-50%)",
        fontFamily: FONT.ui, fontSize: 28, fontWeight: 600, whiteSpace: "nowrap",
        color: gold ? C.navyMid : C.white, background: gold ? C.cream : "rgba(255,255,255,0.12)",
        border: `2px solid ${gold ? C.amberBorder : "rgba(255,255,255,0.35)"}`, borderRadius: 999, padding: "10px 24px",
      }}
    >
      {text}
    </div>
  );
};

export const Problem: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sp = lineSpans(LINES, 0, durationInFrames - 8);
  const p = (i: number) => interpolate(frame, [sp[i].from, sp[i].to], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const out = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  const enters = DOCS.map((_, i) => spring({ frame: frame - 20 - i * 14, fps, config: { damping: 16, mass: 0.8 } }));
  // Cards dim while the workflow chips and final words take the stage.
  const dim = interpolate(frame, [sp[6].from, sp[6].from + 30], [1, 0.22], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const showTags = frame >= sp[3].from && frame < sp[5].from;
  const tagO = interpolate(frame, [sp[3].from, sp[3].from + 14, sp[4].to - 14, sp[4].to], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const ring = interpolate(frame, [sp[5].from + 10, sp[5].from + 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const copy = interpolate(frame, [sp[5].from + 50, sp[5].to - 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad) });

  const words = ["Read.", "Compare.", "Research.", "Prepare."];
  return (
    <AbsoluteFill style={{ opacity: out }}>
      <Backdrop />
      <OnScreenDark text="A property transfer starts with documents." />
      <div style={{ position: "absolute", top: 150, left: 0, right: 0, textAlign: "center", fontFamily: FONT.ui, fontSize: 24, color: C.gold, letterSpacing: 2, fontWeight: 600, opacity: enters[0] }}>
        SYNTHETIC DEMONSTRATION DOCUMENTS
      </div>

      {DOCS.map((d, i) => (
        <Card key={d.file} d={d} enter={enters[i]} dim={dim} ring={i === 2 ? ring : 0} />
      ))}

      {/* L2: the workflow behind the request */}
      {CHIPS.map((c, i) => {
        const at = sp[2].from + (i * (sp[2].to - sp[2].from)) / CHIPS.length;
        const gone = frame > sp[3].from;
        return !gone ? <Chip key={c} text={c} at={at} frame={frame} x={170 + i * 316} y={690} /> : null;
      })}

      {/* L3: scattered, mixed formats */}
      {showTags
        ? DOCS.filter((d) => d.tag).map((d) => (
            <div key={d.tag} style={{ position: "absolute", left: d.x - 170, top: d.y + 150, width: 340, textAlign: "center", opacity: tagO }}>
              <span style={{ fontFamily: FONT.ui, fontSize: 24, fontWeight: 600, color: C.navyMid, background: C.cream, border: `2px solid ${C.amberBorder}`, borderRadius: 999, padding: "6px 18px" }}>
                {d.tag}
              </span>
            </div>
          ))
        : null}

      {/* L4: how the documents relate */}
      {frame >= sp[4].from && frame < sp[5].from ? (
        <>
          <Chip text="Which details can be relied on?" at={sp[4].from + 10} frame={frame} x={620} y={690} gold />
          <Chip text="What still needs clarification?" at={sp[4].from + 70} frame={frame} x={1300} y={690} gold />
        </>
      ) : null}

      {/* L5: notes, legal sources and the form, with one detail checked and copied */}
      {frame >= sp[5].from ? (
        <>
          {[["Notes", 420], ["Legal sources", 960], ["Form", 1500]].map(([t, x], i) => (
            <Chip key={t as string} text={t as string} at={sp[5].from + 8 + i * 12} frame={frame} x={x as number} y={720} />
          ))}
          <div
            style={{
              position: "absolute",
              left: 1150 - 130 + (1500 - 1150) * copy,
              top: 360 + 10 + (720 - 370) * copy,
              opacity: ring * (1 - 0.0 * copy),
              fontFamily: "monospace",
              fontSize: 26,
              fontWeight: 700,
              color: C.navyMid,
              background: C.gold,
              borderRadius: 8,
              padding: "4px 12px",
            }}
          >
            Parcel 0099
          </div>
        </>
      ) : null}

      {/* L6: the problem, in four words */}
      {frame >= sp[6].from ? (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "row", gap: 26 }}>
          {words.map((w, i) => {
            const e = spring({ frame: frame - sp[6].from - 20 - i * 24, fps, config: { damping: 200 } });
            return (
              <span key={w} style={{ fontFamily: FONT.display, fontWeight: 700, fontSize: 84, color: i === 3 ? C.gold : C.white, opacity: e, transform: `translateY(${(1 - e) * 24}px)` }}>
                {w}
              </span>
            );
          })}
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
