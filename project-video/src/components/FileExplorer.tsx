import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT } from "../theme";

// An animated recreation of the Windows "Open" dialog. The recorded browser
// attaches files by script and cannot show the real dialog, so this overlay
// stands in for it: same four synthetic files, same steps a person would take.
// It is drawn, not filmed; the video's caption says so.

const FILES = [
  { name: "synthetic-identity-card.png", kind: "PNG File", size: "7 KB", doc: "synthetic-identity-card.png" },
  { name: "synthetic-survey-plan.png", kind: "PNG File", size: "8 KB", doc: "synthetic-survey-plan.png" },
  { name: "synthetic-title-certificate.png", kind: "PNG File", size: "7 KB", doc: "synthetic-title-certificate.png" },
  { name: "synthetic-form8-instrument.png", kind: "PNG File", size: "7 KB", doc: "synthetic-form8-instrument.png" },
];

const WIN_W = 1180;
const WIN_H = 700;
const ROW_Y0 = 232; // first file row, inside the window
const ROW_H = 58;

const Arrow: React.FC<{ x: number; y: number; press: number }> = ({ x, y, press }) => (
  <svg
    width="30"
    height="30"
    viewBox="0 0 24 24"
    style={{ position: "absolute", left: x - 4, top: y - 3, transform: `scale(${1 - press * 0.12})`, filter: "drop-shadow(0 2px 3px rgba(0,0,0,.35))" }}
  >
    <path d="M3 2l7.5 19 2.6-8.1L21 10.3z" fill="#0F1F38" stroke="#fff" strokeWidth="1.6" strokeLinejoin="round" />
  </svg>
);

export const FileExplorer: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = (s: number) => Math.round(s * fps);

  // Beats (seconds): window in 0.2-0.8, select 1.4-3.6, Open at 4.5, window out 5.4.
  const enter = spring({ frame: frame - t(0.2), fps, config: { damping: 200 } });
  const out = interpolate(frame, [durationInFrames - t(0.7), durationInFrames - t(0.2)], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const win = Math.min(enter, out);

  // Rows are selected in turn: click the first, then shift+click the last.
  const first = t(1.6);
  const last = t(3.2);
  const sel = (i: number) => {
    if (frame < first) return false;
    if (frame < last) return i === 0;
    return true; // shift-click selects the range
  };

  // Cursor path: from the page, to the first file, to the last file, to Open.
  const winLeft = (1920 - WIN_W) / 2;
  const winTop = (1080 - WIN_H) / 2 - 20;
  const rowCentre = (i: number) => ({ x: winLeft + 330, y: winTop + ROW_Y0 + i * ROW_H + ROW_H / 2 });
  const openBtn = { x: winLeft + WIN_W - 230, y: winTop + WIN_H - 52 };
  const ease = Easing.bezier(0.4, 0, 0.2, 1);
  const stops = [
    { f: t(0.2), x: 1100, y: 420 },
    { f: t(1.5), ...rowCentre(0) },
    { f: t(3.1), ...rowCentre(3) },
    { f: t(4.4), ...openBtn },
  ];
  let cx = stops[0].x;
  let cy = stops[0].y;
  for (let i = 0; i < stops.length - 1; i++) {
    const a = stops[i];
    const b = stops[i + 1];
    if (frame >= a.f && frame <= b.f) {
      const k = interpolate(frame, [a.f, b.f], [0, 1], { easing: ease });
      cx = a.x + (b.x - a.x) * k;
      cy = a.y + (b.y - a.y) * k;
    } else if (frame > b.f) {
      cx = b.x;
      cy = b.y;
    }
  }
  const pressAt = [t(1.6), t(3.2), t(4.5)];
  const press = Math.max(0, ...pressAt.map((p) => 1 - Math.min(1, Math.abs(frame - p) / 4)));
  const opening = frame >= t(4.5);

  return (
    <AbsoluteFill style={{ opacity: win }}>
      <AbsoluteFill style={{ background: "rgba(11,22,40,0.45)" }} />
      <div
        style={{
          position: "absolute",
          left: winLeft,
          top: winTop,
          width: WIN_W,
          height: WIN_H,
          borderRadius: 12,
          background: "#FFFFFF",
          boxShadow: "0 30px 80px rgba(0,0,0,0.5)",
          overflow: "hidden",
          fontFamily: "Segoe UI, " + FONT.ui + ", sans-serif",
          color: "#1b1b1b",
          transform: `scale(${0.96 + 0.04 * enter}) translateY(${(1 - enter) * 24}px)`,
        }}
      >
        {/* Title bar */}
        <div style={{ height: 46, background: "#F3F3F3", display: "flex", alignItems: "center", padding: "0 16px", borderBottom: "1px solid #E1E1E1" }}>
          <Img src={staticFile("brand/logo-mark-black.png")} style={{ width: 22, height: 22, marginRight: 12 }} />
          <div style={{ fontSize: 17 }}>Open</div>
          <div style={{ marginLeft: "auto", fontSize: 20, letterSpacing: 24, color: "#444" }}>—  ☐  ✕</div>
        </div>
        {/* Address bar */}
        <div style={{ height: 56, display: "flex", alignItems: "center", gap: 14, padding: "0 18px", borderBottom: "1px solid #EDEDED" }}>
          <span style={{ color: "#777", fontSize: 20 }}>←  →  ↑</span>
          <div style={{ flex: 1, height: 36, border: "1px solid #D0D0D0", borderRadius: 4, display: "flex", alignItems: "center", padding: "0 12px", fontSize: 17, color: "#333" }}>
            This PC  ›  Desktop  ›  draftly-synthetic-docs
          </div>
          <div style={{ width: 280, height: 36, border: "1px solid #D0D0D0", borderRadius: 4, display: "flex", alignItems: "center", padding: "0 12px", fontSize: 17, color: "#777" }}>
            Search draftly-synthetic-docs
          </div>
        </div>
        <div style={{ display: "flex", height: WIN_H - 46 - 56 - 96 }}>
          {/* Navigation pane */}
          <div style={{ width: 250, borderRight: "1px solid #EDEDED", padding: "14px 0", fontSize: 17, color: "#333" }}>
            {["Quick access", "Desktop", "Downloads", "Documents", "This PC", "Network"].map((n, i) => (
              <div key={n} style={{ padding: "8px 22px", fontWeight: i === 1 ? 600 : 400, background: i === 1 ? "#E5F1FB" : "transparent" }}>
                {n}
              </div>
            ))}
          </div>
          {/* File list */}
          <div style={{ flex: 1, padding: "10px 0" }}>
            <div style={{ display: "flex", padding: "6px 24px", fontSize: 15, color: "#666", borderBottom: "1px solid #EDEDED" }}>
              <div style={{ flex: 1 }}>Name</div>
              <div style={{ width: 150 }}>Type</div>
              <div style={{ width: 100 }}>Size</div>
            </div>
            {FILES.map((f, i) => (
              <div
                key={f.name}
                style={{
                  height: ROW_H,
                  display: "flex",
                  alignItems: "center",
                  padding: "0 24px",
                  fontSize: 19,
                  background: sel(i) ? "#CCE8FF" : "transparent",
                  outline: sel(i) ? "1px solid #99D1FF" : "none",
                }}
              >
                <div style={{ width: 30, height: 36, marginRight: 14, border: "1px solid #9AA5B1", borderRadius: 3, background: "#FBFAF6", position: "relative" }}>
                  <div style={{ position: "absolute", left: 4, right: 4, top: 8, height: 3, background: "#B03A2E" }} />
                  <div style={{ position: "absolute", left: 4, right: 10, top: 16, height: 3, background: "#9AA5B1" }} />
                  <div style={{ position: "absolute", left: 4, right: 6, top: 23, height: 3, background: "#9AA5B1" }} />
                </div>
                <div style={{ flex: 1 }}>{f.name}</div>
                <div style={{ width: 150, color: "#555" }}>{f.kind}</div>
                <div style={{ width: 100, color: "#555" }}>{f.size}</div>
              </div>
            ))}
          </div>
        </div>
        {/* Footer */}
        <div style={{ height: 96, borderTop: "1px solid #E1E1E1", background: "#F9F9F9", padding: "12px 24px", fontSize: 17 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 130, color: "#444" }}>File name:</div>
            <div style={{ flex: 1, height: 36, border: "1px solid #7A7A7A", background: "#fff", display: "flex", alignItems: "center", padding: "0 12px", whiteSpace: "nowrap", overflow: "hidden" }}>
              {frame >= last ? FILES.map((f) => `"${f.name}"`).join(" ") : frame >= first ? `"${FILES[0].name}"` : ""}
            </div>
            <div style={{ width: 150, height: 36, border: "1px solid #D0D0D0", display: "flex", alignItems: "center", padding: "0 12px", color: "#444" }}>All files</div>
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 14, marginTop: 10 }}>
            <div
              style={{
                width: 130, height: 34, borderRadius: 4, display: "flex", alignItems: "center", justifyContent: "center",
                background: opening ? "#0067C0" : "#0F6CBD", color: "#fff", fontWeight: 600,
                boxShadow: opening ? "0 0 0 3px rgba(15,108,189,0.35)" : "none",
              }}
            >
              Open
            </div>
            <div style={{ width: 130, height: 34, borderRadius: 4, border: "1px solid #C8C8C8", display: "flex", alignItems: "center", justifyContent: "center", background: "#fff" }}>
              Cancel
            </div>
          </div>
        </div>
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 24, textAlign: "center", fontFamily: FONT.ui, opacity: enter }}>
        <div style={{ color: C.cream, fontSize: 32, fontWeight: 600 }}>Choosing the evidence files from the computer</div>
        <div style={{ color: C.muted, fontSize: 20, marginTop: 4 }}>Illustration of the file dialog · synthetic files only</div>
      </div>
      <Arrow x={cx} y={cy} press={press} />
    </AbsoluteFill>
  );
};
