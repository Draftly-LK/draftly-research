import { Video } from "@remotion/media";
import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { SCRIPT } from "../script";
import { lineSpans, Span } from "../timing";
import { C, FONT } from "../theme";
import { Backdrop } from "./Backdrop";
import { Wordmark } from "./Brand";
import { LAWYERS } from "../media";
import { OnScreenDark } from "./OnScreen";

const sec = (id: string) => SCRIPT.find((s) => s.id === id)!;
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Fade/slide in at `at` frames.
const useIn = (at: number, damping = 200) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - at, fps, config: { damping } });
};

// Non-hook version, for use inside loops and conditionals.
const springAt = (frame: number, fps: number, at: number, damping = 200) => spring({ frame: frame - at, fps, config: { damping } });

const Pill: React.FC<{ text: string; at: number; style?: React.CSSProperties; gold?: boolean; size?: number }> = ({ text, at, style, gold, size = 30 }) => {
  const e = useIn(at, 20);
  return (
    <div
      style={{
        position: "absolute", opacity: e, transform: `translateY(${(1 - e) * 24}px)`, fontFamily: FONT.ui, fontSize: size, fontWeight: 600,
        color: gold ? C.navyMid : C.white, background: gold ? C.cream : "rgba(255,255,255,0.12)",
        border: `2px solid ${gold ? C.amberBorder : "rgba(255,255,255,0.35)"}`, borderRadius: 18, padding: "14px 28px", textAlign: "center",
        ...style,
      }}
    >
      {text}
    </div>
  );
};

const Fade: React.FC<{ d: number; children: React.ReactNode }> = ({ d, children }) => {
  const frame = useCurrentFrame();
  const o = Math.min(interpolate(frame, [0, 10], [0, 1], clamp), interpolate(frame, [d - 12, d], [1, 0], clamp));
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};

const Doc: React.FC<{ file: string; label?: string; w: number; style?: React.CSSProperties; dim?: number }> = ({ file, label, w, style, dim = 1 }) => (
  <div style={{ position: "absolute", width: w, opacity: dim, filter: "drop-shadow(0 14px 26px rgba(0,0,0,0.4))", ...style }}>
    <Img src={staticFile(`docs/${file}`)} style={{ width: w, display: "block", borderRadius: 8 }} />
    {label ? <div style={{ marginTop: 8, textAlign: "center", fontFamily: FONT.ui, fontSize: 22, fontWeight: 600, color: C.cream }}>{label}</div> : null}
  </div>
);

const Foot: React.FC<{ text: string }> = ({ text }) => (
  <div style={{ position: "absolute", top: 134, left: 0, right: 0, textAlign: "center", fontFamily: FONT.ui, fontSize: 24, color: C.muted }}>{text}</div>
);

// ---------------------------------------------------------------- Section 2
export const WhyScene: React.FC<{ d: number }> = ({ d }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = lineSpans(sec("why").lines, 0, d - 8);
  const lawyers = useIn(14);
  return (
    <Fade d={d}>
      <Backdrop />
      {frame < s[3].from ? <OnScreenDark text="Shaped by practitioners and research guidance." /> : null}
      {frame < s[3].from ? <Foot text="Project input and guidance, not formal legal validation or endorsement." /> : null}
      {frame < s[1].from ? (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: lawyers }}>
          <div style={{ fontFamily: FONT.display, fontWeight: 700, fontSize: 96, color: C.white }}>Discussions with 4 lawyers</div>
          <div style={{ display: "flex", gap: 44, marginTop: 56 }}>
            {LAWYERS.map((l, i) => {
              const e = springAt(frame, fps, 30 + i * 9, 14);
              return (
                <div key={i} style={{ opacity: e, transform: `scale(${0.6 + 0.4 * e})`, textAlign: "center", width: 230 }}>
                  {l.photo ? (
                    <Img src={staticFile(l.photo)} style={{ width: 200, height: 200, borderRadius: "50%", objectFit: "cover", border: `5px solid ${C.gold}`, boxShadow: "0 12px 30px rgba(0,0,0,0.45)" }} />
                  ) : (
                    <div style={{ width: 200, height: 200, borderRadius: "50%", background: C.navy, border: `5px solid ${C.gold}`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                      <div style={{ width: 66, height: 66, borderRadius: "50%", background: C.gold }} />
                      <div style={{ width: 110, height: 52, borderRadius: "55px 55px 0 0", background: C.cream, marginTop: 8 }} />
                    </div>
                  )}
                  {l.caption ? <div style={{ marginTop: 14, fontFamily: FONT.ui, fontSize: 26, fontWeight: 600, color: C.cream }}>{l.caption}</div> : null}
                </div>
              );
            })}
          </div>
        </AbsoluteFill>
      ) : null}
      {frame >= s[1].from && frame < s[2].from ? (
        <AbsoluteFill>
          {(() => {
            const k = interpolate(frame, [s[1].from + 70, s[1].to - 20], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
            const at = s[1].from;
            return (
              <>
                <Pill text="Document evidence" at={at + 6} gold style={{ left: 330 + 270 * k, top: 430, fontSize: 40 }} />
                <Pill text="Supporting law" at={at + 26} gold style={{ left: 1260 - 270 * k, top: 430, fontSize: 40 }} />
                <Pill text="Lawyer review" at={at + 70} style={{ left: 760, top: 640, fontSize: 52, opacity: interpolate(k, [0, 0.6], [0, 1], clamp), background: C.navy, border: `3px solid ${C.gold}` }} />
              </>
            );
          })()}
        </AbsoluteFill>
      ) : null}
      {frame >= s[2].from && frame < s[3].from ? (
        <AbsoluteFill>
          <Pill text="Practitioner collaboration — workflow development" at={s[2].from + 6} gold style={{ left: 300, top: 400, width: 560, fontSize: 40 }} />
          <Pill text="Expert guidance — Legal IR and NLP" at={s[2].from + 40} gold style={{ left: 1040, top: 400, width: 560, fontSize: 40 }} />
        </AbsoluteFill>
      ) : null}
      {frame >= s[3].from ? (
        <AbsoluteFill style={{ opacity: interpolate(frame, [s[3].from, s[3].from + 14], [0, 1], clamp) }}>
          <AbsoluteFill style={{ background: "#0B1628" }} />
          <Backdrop />
          <AbsoluteFill style={{ alignItems: "center", paddingTop: 60 }}>
            <Wordmark scale={0.62} enter={springAt(frame, fps, s[3].from + 6)} />
            <div style={{ marginTop: 34, width: 760, height: 428, borderRadius: 14, overflow: "hidden", boxShadow: "0 24px 60px rgba(0,0,0,0.5)", border: `3px solid ${C.gold}` }}>
              <Video src={staticFile("footage/01-home.mp4")} trimBefore={90} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </div>
            <div style={{ marginTop: 26, fontFamily: FONT.display, fontSize: 44, color: C.cream, fontWeight: 600 }}>Sri Lankan notarial and conveyancing work.</div>
          </AbsoluteFill>
        </AbsoluteFill>
      ) : null}
    </Fade>
  );
};

// ---------------------------------------------------------------- Section 3
const BUNDLE = [
  { file: "synthetic-identity-card.png", label: "Identity document", ok: true },
  { file: "synthetic-survey-plan.png", label: "Survey plan", ok: true },
  { file: "synthetic-title-certificate.png", label: "Title certificate", ok: true },
  { file: "synthetic-form8-instrument.png", label: "Form 8 transfer instrument", ok: true },
  { file: "synthetic-company-resolution.png", label: "Company resolution", ok: false },
  { file: "synthetic-payment-record.png", label: "Payment record", ok: false },
];

export const BundleScene: React.FC<{ d: number }> = ({ d }) => {
  const frame = useCurrentFrame();
  const s = lineSpans(sec("bundle").lines, 0, d - 8);
  const dim = interpolate(frame, [s[3].from, s[3].from + 20], [1, 0.15], clamp);
  const focus = interpolate(frame, [s[2].from + 150, s[2].from + 200, s[3].from - 20, s[3].from], [0, 1, 1, 0], clamp);
  const Q = ["Who are the parties?", "Which property?", "Which records support this transfer?"];
  return (
    <Fade d={d}>
      <Backdrop />
      <OnScreenDark text="One bundle. Several questions." />
      <div style={{ position: "absolute", top: 134, left: 0, right: 0, textAlign: "center", fontFamily: FONT.ui, fontSize: 26, fontWeight: 600, letterSpacing: 2, color: C.gold }}>
        SYNTHETIC CLIENT BUNDLE · INVENTED FOR THIS DEMONSTRATION
      </div>
      {BUNDLE.map((b, i) => {
        const col = i % 3;
        const row = Math.floor(i / 3);
        const e = useIn(20 + i * 16, 18);
        const x = 270 + col * 470;
        const y = 220 + row * 320;
        const isCompany = b.file.includes("company");
        const z = isCompany ? 1 + 0.18 * focus : 1;
        return (
          <React.Fragment key={b.file}>
            <Doc file={b.file} label={b.label} w={400} dim={dim * e} style={{ left: x, top: y + (1 - e) * -400, transform: `scale(${z})`, zIndex: isCompany ? 5 : 1 }} />
            {frame >= s[2].from + 20 && frame < s[3].from ? (
              <Pill text={b.ok ? "Extraction supported" : "Manual review"} at={s[2].from + 20 + i * 8} gold={b.ok} size={22} style={{ left: x + 10, top: y + 36, padding: "4px 14px", zIndex: 6, fontSize: 20 }} />
            ) : null}
          </React.Fragment>
        );
      })}
      {frame >= s[3].from ? (
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          {Q.map((q, i) => (
            <Pill key={q} text={q} gold at={s[3].from + 10 + i * 60} size={52} style={{ position: "relative", margin: "18px 0", padding: "20px 46px" }} />
          ))}
        </AbsoluteFill>
      ) : null}
    </Fade>
  );
};

// ---------------------------------------------------------------- Section 4
const Box: React.FC<{ text: string; x: number; y: number; at: number; hi?: boolean; strong?: boolean }> = ({ text, x, y, at, hi, strong }) => {
  const e = useIn(at, 20);
  return (
    <div
      style={{
        position: "absolute", left: x, top: y, width: 300, height: 110, display: "flex", alignItems: "center", justifyContent: "center", opacity: e,
        transform: `scale(${0.85 + 0.15 * e})`, fontFamily: FONT.ui, fontSize: 30, fontWeight: 600, textAlign: "center",
        color: strong ? C.navyMid : C.white, background: strong ? C.cream : "rgba(255,255,255,0.1)",
        border: `3px solid ${strong ? C.gold : "rgba(255,255,255,0.3)"}`, borderRadius: 18,
        boxShadow: hi ? `0 0 34px ${C.gold}` : "none",
      }}
    >
      {text}
    </div>
  );
};

export const CompareScene: React.FC<{ d: number }> = ({ d }) => {
  const frame = useCurrentFrame();
  const s = lineSpans(sec("compare").lines, 0, d - 8);
  const xs = [330, 700, 1070, 1440];
  const manual = ["Source page", "Notes", "Repeated comparison", "Draft"];
  const dr = ["Source page", "Proposed value", "Lawyer review", "Working draft"];
  const row = (labels: string[], y: number, start: number, strong: boolean) =>
    labels.map((t, i) => (
      <React.Fragment key={t}>
        <Box text={t} x={xs[i]} y={y} at={start + i * 22} strong={strong && i === 2} hi={strong && i === 2 && frame >= s[2].from} />
        {i < 3 ? (
          <div style={{ position: "absolute", left: xs[i] + 304, top: y + 42, fontSize: 40, color: C.gold, opacity: interpolate(frame, [start + i * 22 + 12, start + i * 22 + 28], [0, 1], clamp) }}>→</div>
        ) : null}
        {/* the same detail, carried through each step */}
        <div
          style={{
            position: "absolute", left: xs[i] + 90, top: y + 118, fontFamily: "monospace", fontSize: 24, fontWeight: 700, color: C.navyMid, background: C.gold, borderRadius: 8, padding: "3px 12px",
            opacity: interpolate(frame, [start + i * 22 + 10, start + i * 22 + 26], [0, 1], clamp),
          }}
        >
          Parcel 0099
        </div>
      </React.Fragment>
    ));
  return (
    <Fade d={d}>
      <Backdrop />
      <OnScreenDark text="Keep the detail connected to its evidence." />
      <div style={{ position: "absolute", left: 60, top: 292, fontFamily: FONT.ui, fontSize: 30, fontWeight: 600, color: C.muted, width: 250 }}>Manual workflow</div>
      <div style={{ position: "absolute", left: 60, top: 612, fontFamily: FONT.ui, fontSize: 30, fontWeight: 600, color: C.gold, width: 250 }}>With Draftly</div>
      {row(manual, 270, 20, false)}
      {frame >= s[1].from ? row(dr, 590, s[1].from + 6, true) : null}
      {frame >= s[2].from ? (
        <div style={{ position: "absolute", left: 0, right: 0, top: 780, textAlign: "center", fontFamily: FONT.display, fontSize: 52, fontWeight: 600, color: C.cream, opacity: interpolate(frame, [s[2].from, s[2].from + 20], [0, 1], clamp) }}>
          The lawyer decides what the evidence means.
        </div>
      ) : null}
    </Fade>
  );
};

// ---------------------------------------------------------------- Section 7 (opening graphic)
export const DifferenceScene: React.FC<{ d: number; spans: Span[] }> = ({ d, spans }) => {
  const frame = useCurrentFrame();
  const a = useIn(10);
  const b = useIn(40);
  const chips = ["An earlier transfer", "Related land", "A different part of the transaction history"];
  const rec = (title: string, ref: string, parcel: string, x: number, e: number, label: string) => (
    <div style={{ position: "absolute", left: x, top: 260, width: 620, opacity: e, transform: `translateY(${(1 - e) * 30}px)`, background: "#FBFAF6", borderRadius: 14, padding: 34, fontFamily: FONT.ui, color: C.ink, boxShadow: "0 24px 50px rgba(0,0,0,0.4)" }}>
      <div style={{ fontSize: 22, fontWeight: 700, color: "#B03A2E", letterSpacing: 1 }}>SYNTHETIC · ILLUSTRATION</div>
      <div style={{ fontFamily: FONT.display, fontSize: 40, fontWeight: 700, margin: "10px 0 20px" }}>{title}</div>
      <div style={{ fontSize: 26, color: "#5B6676" }}>Block no. 09 · Cadastral map no. 900001</div>
      <div style={{ marginTop: 18, display: "inline-block", background: C.gold, borderRadius: 10, padding: "6px 18px", fontFamily: "monospace", fontSize: 28, fontWeight: 700, whiteSpace: "nowrap" }}>
        {label}: {parcel}
      </div>
      <div style={{ marginTop: 18, fontSize: 22, color: "#5B6676" }}>{ref}</div>
    </div>
  );
  return (
    <Fade d={d}>
      <Backdrop />
      <OnScreenDark text="A difference is a question to investigate." />
      {rec("Title certificate", "Registered title for the property", "Parcel no. 0099", 190, a, "Reference A")}
      {rec("Earlier deed", "A prior instrument in the bundle", "Parcel no. 0098", 1110, b, "Reference B")}
      {frame >= spans[1].from ? (
        <div style={{ position: "absolute", left: 0, right: 0, top: 640, textAlign: "center", fontFamily: FONT.display, fontSize: 50, color: C.cream, fontWeight: 600, opacity: interpolate(frame, [spans[1].from, spans[1].from + 18], [0, 1], clamp) }}>
          What does each reference describe?
        </div>
      ) : null}
      {chips.map((c, i) => (frame >= spans[2].from ? <Pill key={c} text={c} gold at={spans[2].from + 10 + i * 50} size={30} style={{ left: 250 + i * 490, top: 760, width: 440 }} /> : null))}
    </Fade>
  );
};

// ---------------------------------------------------------------- Section 10 (retrieval graphic)
const PROV = ["Provision A", "Provision B", "Provision C", "Provision D"];
export const RetrievalGraphic: React.FC<{ d: number; mode: "overview" | "evaluate" }> = ({ d, mode }) => {
  const frame = useCurrentFrame();
  const sc = useIn(8);
  const retrieved = [true, true, true, false]; // illustrative: three found, one missed
  const col = (x: number, title: string, e: number) => (
    <div style={{ position: "absolute", left: x, top: 190, width: 480, fontFamily: FONT.ui, fontSize: 28, fontWeight: 600, color: C.gold, letterSpacing: 2, opacity: e, textAlign: "center" }}>{title.toUpperCase()}</div>
  );
  const compare = mode === "evaluate" ? interpolate(frame, [30, 70], [0, 1], clamp) : 0;
  return (
    <Fade d={d}>
      <Backdrop />
      <OnScreenDark text="Find the provisions behind the question." />
      {col(60, "Scenario", sc)}
      {col(720, "Required provisions", sc)}
      {col(1380, "Retrieved provisions", sc)}
      <div style={{ position: "absolute", left: 60, top: 260, width: 480, opacity: sc, transform: `translateY(${(1 - sc) * 30}px)`, background: "rgba(255,255,255,0.1)", border: "2px solid rgba(255,255,255,0.3)", borderRadius: 18, padding: 28, fontFamily: FONT.ui, fontSize: 30, color: C.white, lineHeight: 1.4 }}>
        A transfer of a registered parcel by sale, between two natural persons.
      </div>
      <div style={{ position: "absolute", left: 550, top: 420, fontSize: 60, color: C.gold, opacity: sc }}>→</div>
      <div style={{ position: "absolute", left: 1210, top: 420, fontSize: 60, color: C.gold, opacity: useIn(100) }}>→</div>
      {PROV.map((p, i) => (
        <Pill key={"r" + p} text={p} at={34 + i * 14} size={30} style={{ left: 720, top: 260 + i * 110, width: 480, background: "rgba(255,255,255,0.1)", border: `2px dashed ${C.cream}` }} />
      ))}
      {PROV.map((p, i) => {
        if (mode === "overview" && frame < 120 + i * 16) return null;
        const ok = retrieved[i];
        const shown = mode === "overview" ? true : true;
        return shown ? (
          <Pill key={"t" + p} text={ok ? p : "— not retrieved —"} at={mode === "overview" ? 120 + i * 16 : 8 + i * 10} gold={ok} size={30}
            style={{ left: 1380, top: 260 + i * 110, width: 480, opacity: ok ? 1 : 0.55, borderStyle: ok ? "solid" : "dashed" }} />
        ) : null;
      })}
      {mode === "evaluate"
        ? PROV.map((p, i) => (
            <div key={"m" + p} style={{ position: "absolute", left: 1230, top: 276 + i * 110, fontSize: 52, fontWeight: 700, opacity: compare, color: retrieved[i] ? "#7BD3A3" : "#F08A7E", fontFamily: FONT.ui }}>
              {retrieved[i] ? "✓" : "✗"}
            </div>
          ))
        : null}
      {mode === "evaluate" ? (
        <div style={{ position: "absolute", left: 0, right: 0, top: 740, textAlign: "center", fontFamily: FONT.display, fontSize: 46, color: C.cream, fontWeight: 600, opacity: compare }}>
          A reviewer compares what was retrieved with what the scenario required.
          <div style={{ fontFamily: FONT.ui, fontSize: 26, color: C.muted, marginTop: 8, fontWeight: 400 }}>Missed authorities become visible, as well as useful matches.</div>
        </div>
      ) : null}
      <div style={{ position: "absolute", left: 0, right: 0, top: 160, textAlign: "center", fontFamily: FONT.ui, fontSize: 20, color: C.muted, opacity: 0 }} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 190, textAlign: "center", fontFamily: FONT.ui, fontSize: 22, color: C.muted }}>
        Illustration of the method. No measured result is shown.
      </div>
    </Fade>
  );
};

// ---------------------------------------------------------------- Section 11 (montage)
const PANELS = [
  { t: "Evidence", lines: ["4 source files", "originals unchanged"] },
  { t: "Reviewed facts", lines: ["46 verified facts", "each with a source"] },
  { t: "Visible issues", lines: ["12 warnings", "1 question still open"], open: true },
  { t: "Working draft", lines: ["Form 8", "fields from facts"] },
  { t: "Supporting research", lines: ["57 statutes", "18 amendments"] },
];

export const MontageScene: React.FC<{ d: number }> = ({ d }) => {
  const frame = useCurrentFrame();
  const s = lineSpans(sec("closing").lines, 0, 46 * 30);
  const e0 = useIn(10);
  const fly = interpolate(frame, [s[1].from, s[1].from + 60], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
  const docs = ["synthetic-identity-card.png", "synthetic-survey-plan.png", "synthetic-title-certificate.png", "synthetic-form8-instrument.png"];
  const xs = [330, 740, 1150, 1560];
  return (
    <Fade d={d}>
      <Backdrop />
      <OnScreenDark text="Follow the evidence. Keep the lawyer in control." />
      {docs.map((f, i) => (
        <Doc key={f} file={f} w={320} dim={e0 * (1 - fly)} style={{ left: xs[i] - 160 + (i % 2) * 20, top: 340 + (1 - e0) * -300, transform: `rotate(${(i % 2 ? 3 : -4) * (1 - fly)}deg)` }} />
      ))}
      {PANELS.map((p, i) => {
        const e = interpolate(fly, [0.2 + i * 0.1, 0.7 + i * 0.1], [0, 1], clamp);
        const glow = frame >= s[2].from && (i === 4) ? 1 : 0;
        return (
          <div key={p.t} style={{ position: "absolute", left: 60 + i * 366, top: 300, width: 340, height: 360, opacity: e, transform: `translateY(${(1 - e) * 40}px)`, background: "rgba(255,255,255,0.09)", border: `2px solid ${glow ? C.gold : "rgba(255,255,255,0.3)"}`, boxShadow: glow ? `0 0 30px ${C.gold}` : "none", borderRadius: 18, padding: 26, fontFamily: FONT.ui }}>
            <div style={{ color: C.gold, fontSize: 28, fontWeight: 700 }}>{p.t}</div>
            {p.lines.map((l) => (
              <div key={l} style={{ color: C.white, fontSize: 28, marginTop: 16 }}>{l}</div>
            ))}
            {p.open ? <div style={{ marginTop: 26, background: C.cream, color: C.navyMid, border: `2px solid ${C.amberBorder}`, borderRadius: 12, padding: "8px 14px", fontSize: 24, fontWeight: 600 }}>Unresolved question stays visible</div> : null}
          </div>
        );
      })}
      {frame >= s[2].from ? (
        <div style={{ position: "absolute", left: 0, right: 0, top: 730, textAlign: "center", fontFamily: FONT.display, fontSize: 48, color: C.cream, fontWeight: 600, opacity: interpolate(frame, [s[2].from, s[2].from + 20], [0, 1], clamp) }}>
          The sources stay open to inspection. The decisions stay with the lawyer.
        </div>
      ) : null}
    </Fade>
  );
};
