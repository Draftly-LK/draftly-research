"""Generate research-paper/figures/benchmark-construction.svg (+ .pdf, preview).

Three-panel pipeline: (A) question selection, (B) agent annotation,
(C) human legal validation (planned; drawn dashed). Pure SVG, flat vector,
editable text. Palette and typography match make_architecture.py.

Run from the repo root:
    uv run python research-paper/figures/make_benchmark_construction.py
"""

from __future__ import annotations

from pathlib import Path

NAVY = "#1F3A5F"
GOLD = "#B8963E"
GOLD_FILL = "#F6EFDD"
PALE = "#EAF0F7"
SEP = "#E3E6EA"
GREY = "#8A8F98"
TEXT = "#1B1F24"
WHITE = "#FFFFFF"
FONT = "Helvetica, Arial, sans-serif"

W, H = 880, 392
out: list[str] = []
defs: list[str] = []


def emit(s: str) -> None:
    out.append(s)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=10.5, weight="normal", fill=TEXT, anchor="middle", style="normal", opacity=1.0):
    extra = f' font-style="{style}"' if style != "normal" else ""
    op = f' opacity="{opacity}"' if opacity < 1 else ""
    emit(
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}"{extra}{op}>{esc(s)}</text>'
    )


def rect(x, y, w, h, fill=WHITE, stroke=NAVY, sw=0.9, r=4, dash=None, opacity=1.0):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    op = f' fill-opacity="{opacity}"' if opacity < 1 else ""
    emit(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{op}/>'
    )


def path(d, stroke=NAVY, sw=0.9, dash=None, marker=None, fill="none", sw_cap="round"):
    dd = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    emit(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="{sw_cap}"{dd}{m}/>')


def arrow(x1, y1, x2, y2, dashed=False, stroke=NAVY):
    dash = "4,3" if dashed else None
    marker = "arrowNavy"
    path(f"M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}", stroke, 0.9, dash, marker)


def elbow(points, dashed=False, stroke=NAVY, marker=True):
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points)
    path(d, stroke, 0.9, "4,3" if dashed else None, "arrowNavy" if marker else None)


def circle(cx, cy, r, fill=WHITE, stroke=NAVY, sw=0.9, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    emit(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def card(x, y, w, h, rows, fill=PALE, stroke=NAVY, sizes=(10.5, 9.5), weights=("bold", "normal"),
         fills=(TEXT, GREY), dash=None, opacity=1.0):
    rect(x, y, w, h, fill, stroke, 0.9, 5, dash, opacity)
    n = len(rows)
    lh = 12.5
    y0 = y + h / 2 - (n - 1) * lh / 2 + 3.8
    for i, r in enumerate(rows):
        text(x + w / 2, y0 + i * lh, r, sizes[min(i, len(sizes) - 1)], weights[min(i, len(weights) - 1)],
             fills[min(i, len(fills) - 1)])


_avatar_n = 0


def avatar(cx, cy, r, ring, skin, hair, shirt, hair_style="short", dashed=False):
    """Flat head-and-shoulders portrait clipped to a circle with a coloured ring."""
    global _avatar_n
    _avatar_n += 1
    cid = f"clip{_avatar_n}"
    defs.append(f'<clipPath id="{cid}"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r - 1.2:.1f}"/></clipPath>')
    circle(cx, cy, r, PALE, ring, 1.6, "3,2" if dashed else None)
    emit(f'<g clip-path="url(#{cid})">')
    # shoulders
    sy = cy + r * 0.55
    emit(
        f'<path d="M {cx - r:.1f} {cy + r + 2:.1f} L {cx - r:.1f} {sy + r * 0.35:.1f} '
        f'Q {cx - r:.1f} {sy:.1f} {cx - r * 0.55:.1f} {sy:.1f} L {cx + r * 0.55:.1f} {sy:.1f} '
        f'Q {cx + r:.1f} {sy:.1f} {cx + r:.1f} {sy + r * 0.35:.1f} L {cx + r:.1f} {cy + r + 2:.1f} Z" fill="{shirt}"/>'
    )
    # collar
    emit(f'<path d="M {cx - r * 0.18:.1f} {sy:.1f} L {cx:.1f} {sy + r * 0.28:.1f} L {cx + r * 0.18:.1f} {sy:.1f} Z" fill="{WHITE}"/>')
    # neck
    emit(f'<rect x="{cx - r * 0.16:.1f}" y="{cy + r * 0.12:.1f}" width="{r * 0.32:.1f}" height="{r * 0.5:.1f}" fill="{skin}"/>')
    # head
    hr = r * 0.42
    hy = cy - r * 0.12
    emit(f'<ellipse cx="{cx:.1f}" cy="{hy:.1f}" rx="{hr * 0.92:.1f}" ry="{hr:.1f}" fill="{skin}"/>')
    # hair
    if hair_style == "short":
        emit(f'<path d="M {cx - hr * 0.95:.1f} {hy - hr * 0.1:.1f} A {hr:.1f} {hr:.1f} 0 0 1 {cx + hr * 0.95:.1f} {hy - hr * 0.1:.1f} '
             f'L {cx + hr * 0.95:.1f} {hy - hr * 0.35:.1f} A {hr:.1f} {hr:.1f} 0 0 0 {cx - hr * 0.95:.1f} {hy - hr * 0.35:.1f} Z" fill="{hair}"/>')
    elif hair_style == "long":
        emit(f'<path d="M {cx - hr * 1.05:.1f} {hy + hr * 0.9:.1f} L {cx - hr * 1.05:.1f} {hy - hr * 0.1:.1f} '
             f'A {hr * 1.05:.1f} {hr * 1.05:.1f} 0 0 1 {cx + hr * 1.05:.1f} {hy - hr * 0.1:.1f} L {cx + hr * 1.05:.1f} {hy + hr * 0.9:.1f} '
             f'L {cx + hr * 0.75:.1f} {hy + hr * 0.9:.1f} L {cx + hr * 0.75:.1f} {hy - hr * 0.05:.1f} '
             f'A {hr * 0.78:.1f} {hr * 0.78:.1f} 0 0 0 {cx - hr * 0.75:.1f} {hy - hr * 0.05:.1f} L {cx - hr * 0.75:.1f} {hy + hr * 0.9:.1f} Z" fill="{hair}"/>')
    elif hair_style == "bun":
        emit(f'<circle cx="{cx:.1f}" cy="{hy - hr * 1.05:.1f}" r="{hr * 0.32:.1f}" fill="{hair}"/>')
        emit(f'<path d="M {cx - hr * 0.95:.1f} {hy - hr * 0.05:.1f} A {hr:.1f} {hr:.1f} 0 0 1 {cx + hr * 0.95:.1f} {hy - hr * 0.05:.1f} '
             f'L {cx + hr * 0.95:.1f} {hy - hr * 0.3:.1f} A {hr:.1f} {hr:.1f} 0 0 0 {cx - hr * 0.95:.1f} {hy - hr * 0.3:.1f} Z" fill="{hair}"/>')
    elif hair_style == "curly":
        for k in range(-3, 4):
            emit(f'<circle cx="{cx + k * hr * 0.32:.1f}" cy="{hy - hr * (0.78 if k % 2 else 0.9):.1f}" r="{hr * 0.3:.1f}" fill="{hair}"/>')
    # glasses for one variant
    if hair_style == "curly":
        for sgn in (-1, 1):
            emit(f'<circle cx="{cx + sgn * hr * 0.4:.1f}" cy="{hy + hr * 0.05:.1f}" r="{hr * 0.25:.1f}" fill="none" stroke="{NAVY}" stroke-width="0.7"/>')
    emit("</g>")


def cylinder(cx, top, w, h, fill=PALE, stroke=NAVY):
    rx, ry = w / 2, w / 9
    rect_y = top + ry
    emit(f'<path d="M {cx - rx:.1f} {rect_y:.1f} V {rect_y + h:.1f} A {rx:.1f} {ry:.1f} 0 0 0 {cx + rx:.1f} {rect_y + h:.1f} '
         f'V {rect_y:.1f} Z" fill="{fill}" stroke="{stroke}" stroke-width="0.9"/>')
    emit(f'<ellipse cx="{cx:.1f}" cy="{rect_y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{WHITE}" stroke="{stroke}" stroke-width="0.9"/>')
    emit(f'<path d="M {cx - rx:.1f} {rect_y + h * 0.45:.1f} A {rx:.1f} {ry:.1f} 0 0 0 {cx + rx:.1f} {rect_y + h * 0.45:.1f}" fill="none" stroke="{stroke}" stroke-width="0.6"/>')
    return rect_y + h + ry


def panel_label(x, y, letter, title):
    circle(x + 8, y, 8, NAVY, NAVY, 0)
    text(x + 8, y + 3.6, letter, 10, "bold", WHITE)
    text(x + 22, y + 4, title, 12, "bold", TEXT, "start")


def doc_check(x, y, s=12):
    """Small document with a check mark, s = height."""
    w = s * 0.78
    emit(f'<path d="M {x:.1f} {y:.1f} H {x + w * 0.68:.1f} L {x + w:.1f} {y + s * 0.26:.1f} V {y + s:.1f} H {x:.1f} Z" '
         f'fill="{WHITE}" stroke="{GOLD}" stroke-width="0.9" stroke-linejoin="round"/>')
    emit(f'<path d="M {x + w * 0.68:.1f} {y:.1f} V {y + s * 0.26:.1f} H {x + w:.1f}" fill="none" stroke="{GOLD}" stroke-width="0.9"/>')
    emit(f'<path d="M {x + w * 0.22:.1f} {y + s * 0.6:.1f} L {x + w * 0.45:.1f} {y + s * 0.8:.1f} L {x + w * 0.82:.1f} {y + s * 0.42:.1f}" '
         f'fill="none" stroke="{GOLD}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>')


# ================================================================ frame
text(W / 2, 19, "Construction of the Complete-Bundle Statutory QA Benchmark", 14, "bold", NAVY)
PT, PB = 36, H - 10
AX0, AX1 = 12, 232
BX0, BX1 = 246, 616
CX0, CX1 = 630, 868
rect(AX0, PT, AX1 - AX0, PB - PT, WHITE, SEP, 0.9, 6)
rect(BX0, PT, BX1 - BX0, PB - PT, WHITE, SEP, 0.9, 6)
rect(CX0, PT, CX1 - CX0, PB - PT, WHITE, GREY, 0.9, 6, "5,4")
panel_label(AX0 + 10, PT + 16, "A", "Question Selection")
panel_label(BX0 + 10, PT + 16, "B", "Agent Annotation")
panel_label(CX0 + 10, PT + 16, "C", "Human Legal Validation")
text(CX1 - 10, PB - 8, "PLANNED — VALIDATION PENDING", 8, "bold", GOLD, "end")

# ================================================================ Panel A
acx = (AX0 + AX1) / 2
# stack of papers
for i, off in enumerate((8, 4, 0)):
    rect(acx - 30 + off, 66 + (8 - off), 60, 42, PALE if i == 2 else WHITE, NAVY, 0.9, 2)
for k in range(4):
    yy = 66 + 8 + 9 + k * 7
    path(f"M {acx - 22:.1f} {yy:.1f} H {acx + 14 if k < 3 else acx - 2:.1f}", GREY, 0.8)
text(acx, 128, "16 Conveyancing Papers", 10.5, "bold")
text(acx, 140, "2018–2026", 9.5, "normal", GREY)
arrow(acx, 146, acx, 160)
card(acx - 62, 162, 124, 26, ["667 Atomic Questions"], PALE, NAVY, (10.5,), ("bold",), (TEXT,))
arrow(acx, 190, acx, 204)
# funnel
ftop, fbot = 206, 252
emit(f'<path d="M {acx - 74:.1f} {ftop:.1f} H {acx + 74:.1f} L {acx + 22:.1f} {fbot - 10:.1f} V {fbot:.1f} H {acx - 22:.1f} '
     f'V {fbot - 10:.1f} Z" fill="{WHITE}" stroke="{NAVY}" stroke-width="0.9" stroke-linejoin="round"/>')
text(acx, ftop + 16, "Scenario Selection", 9.5, "bold")
text(acx, ftop + 28, "and Matter Grouping", 9.5, "bold")
arrow(acx, fbot + 2, acx, 268)
card(acx - 62, 270, 124, 36, ["144 Questions", "92 Legal Matters"], PALE, NAVY)
# A -> B
elbow([(acx + 64, 288), (BX0 + 22, 288), (BX0 + 22, 180), (BX0 + 58, 180)])

# ================================================================ Panel B
bcx = (BX0 + BX1) / 2
cyl_bottom = cylinder(bcx, 60, 56, 26)
text(bcx + 40, 76, "Frozen Statutory Corpus", 10.5, "bold", TEXT, "start")
text(bcx + 40, 88, "4,557 Sections", 9.5, "normal", GREY, "start")
RX, VX = BX0 + 92, BX1 - 92
AY = 180
# corpus feeds both agents
elbow([(bcx - 14, cyl_bottom - 3), (bcx - 14, 122), (RX, 122), (RX, AY - 28)])
elbow([(bcx + 14, cyl_bottom - 3), (bcx + 14, 122), (VX, 122), (VX, AY - 28)])

avatar(RX, AY, 26, GOLD, "#C99A76", NAVY, "#3E5C8A", "short")
text(RX, AY + 40, "Research Agent", 10.5, "bold")
avatar(VX, AY, 26, GOLD, "#8D5A3B", "#2B2B2B", "#4A6A94", "bun")
text(VX, AY + 40, "Independent Verification Agent", 10, "bold")
# hand-off
arrow(RX + 30, AY, VX - 30, AY)
text((RX + VX) / 2, AY - 6, "Structured Hand-off", 9, "normal", GREY)


def tags(cx, y, labels, w=134):
    for i, lab in enumerate(labels):
        yy = y + i * 20
        rect(cx - w / 2, yy, w, 16, WHITE, NAVY, 0.7, 8)
        text(cx, yy + 11, lab, 9)
    return y + len(labels) * 20 - 4


t_end = tags(RX, AY + 48, ["Legal Issues", "Indispensable Provisions", "Evidence-Linked Answers"])
tags(VX, AY + 48, ["Citation Check", "Temporal Check", "Omission Check"])

# dataset card
cy0 = t_end + 14
cw, ch = 176, 38
cx0 = VX - cw / 2 - 10
arrow(VX, t_end + 2, VX, cy0 - 2)
rect(cx0, cy0, cw, ch, GOLD_FILL, GOLD, 1.0, 5)
doc_check(cx0 + 10, cy0 + 12, 14)
text(cx0 + 28 + (cw - 28) / 2, cy0 + 16, "Proposed-Gold Benchmark", 10.5, "bold", TEXT)
text(cx0 + 28 + (cw - 28) / 2, cy0 + 29, "50 Questions · 40 Matters", 9.5, "normal", GREY)

# ================================================================ Panel C (planned, dashed)
ccx = (CX0 + CX1) / 2
A1, A2 = ccx - 46, ccx + 46
HY = 118
# B -> C: card right edge to both annotators
card_mid_y = cy0 + ch / 2
elbow([(cx0 + cw, card_mid_y), (CX0 + 12, card_mid_y), (CX0 + 12, 78), (A1, 78), (A1, HY - 26)], dashed=True)
elbow([(CX0 + 12, 78), (A2, 78), (A2, HY - 26)], dashed=True)

avatar(A1, HY, 22, NAVY, "#E8C9A8", "#6B4A2B", "#8FA3BF", "long", dashed=True)
avatar(A2, HY, 22, NAVY, "#B07D5A", "#1F1F1F", "#7B90B0", "curly", dashed=True)
text(A1, HY + 34, "Legal Annotator 1", 9.5, "bold")
text(A2, HY + 34, "Legal Annotator 2", 9.5, "bold")

# decision diamond
DY = 206
elbow([(A1, HY + 38), (A1, DY - 6), (ccx - 32, DY - 6)], dashed=True, marker=False)
elbow([(A2, HY + 38), (A2, DY - 6), (ccx + 32, DY - 6)], dashed=True, marker=False)
emit(f'<path d="M {ccx:.1f} {DY - 22:.1f} L {ccx + 40:.1f} {DY:.1f} L {ccx:.1f} {DY + 22:.1f} L {ccx - 40:.1f} {DY:.1f} Z" '
     f'fill="{WHITE}" stroke="{NAVY}" stroke-width="0.9" stroke-dasharray="4,3"/>')
text(ccx, DY + 3.5, "Agreement?", 9.5, "bold")

# final card
FY = 318
fw, fh = 176, 38
fx = ccx - fw / 2
# agreement path (straight down)
arrow(ccx, DY + 24, ccx, FY - 2, dashed=True)
text(ccx - 6, (DY + 24 + FY) / 2 + 3, "yes", 8, "normal", GREY, "end", "italic")
# disagreement path to annotator 3
A3X, A3Y = CX1 - 50, 258
elbow([(ccx + 42, DY), (A3X, DY), (A3X, A3Y - 22)], dashed=True)
text(ccx + 48, DY - 5, "no", 8, "normal", GREY, "start", "italic")
avatar(A3X, A3Y, 20, NAVY, "#D9B99B", "#8A8F98", "#6E85A8", "short", dashed=True)
text(A3X, A3Y + 30, "Legal Annotator 3", 9.5, "bold")
text(A3X, A3Y + 40, "Adjudication", 9, "normal", GREY)
arrow(A3X, A3Y + 44, A3X, FY - 2, dashed=True)

rect(fx, FY, fw, fh, PALE, GREY, 0.9, 5, "4,3", 0.5)
text(ccx, FY + 23, "Final Lawyer-Validated Benchmark", 10, "bold", NAVY, "middle", "normal", 0.75)

# ================================================================ write
svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n<defs>\n'
    f'<marker id="arrowNavy" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
    f'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{NAVY}"/></marker>\n'
    + "\n".join(defs)
    + f'\n</defs>\n<rect width="{W}" height="{H}" fill="{WHITE}"/>\n'
    + "\n".join(out)
    + "\n</svg>\n"
)
here = Path(__file__).resolve().parent
p = here / "benchmark-construction.svg"
p.write_text(svg, encoding="utf-8")
try:
    import cairosvg

    cairosvg.svg2pdf(url=str(p), write_to=str(here / "benchmark-construction.pdf"))
    cairosvg.svg2png(url=str(p), write_to=str(here / "benchmark-construction-preview.png"), output_width=3520)
    print(f"wrote benchmark-construction.svg ({W}x{H}), .pdf, -preview.png")
except ImportError:
    print("wrote benchmark-construction.svg (cairosvg missing; PDF skipped)")
