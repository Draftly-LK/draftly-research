// Spoken lines share a section's time in proportion to their length. The
// captions and the scene animations both use this, so a graphic can change on
// exactly the line it illustrates.
export interface Span {
  from: number;
  to: number;
}

export function lineSpans(lines: string[], startFrame: number, endFrame: number): Span[] {
  const total = lines.reduce((s, l) => s + l.length, 0);
  const span = endFrame - startFrame;
  let acc = startFrame;
  return lines.map((text) => {
    const len = Math.round((text.length / total) * span);
    const s = { from: acc, to: acc + len };
    acc += len;
    return s;
  });
}

// Which line is current at `frame` (the last line once past the end).
export function lineAt(spans: Span[], frame: number): number {
  const i = spans.findIndex((s) => frame >= s.from && frame < s.to);
  return i === -1 ? (frame < spans[0].from ? 0 : spans.length - 1) : i;
}
