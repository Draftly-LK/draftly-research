"""Generate research-paper/figures/architecture.svg (+ .pdf, preview .png).

Two-panel figure: (A) benchmark construction funnel, (B) complete-bundle
statutory retrieval. Pure SVG: no gradients, shadows or icons.

The canvas is 820 units wide so that, printed at the NeurIPS text width
(13.97 cm), 1 unit is 0.17 mm and the smallest type (9 units) is about 4.4 pt.

Run from the repo root:
    uv run python research-paper/figures/make_architecture.py
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------- palette
BLUE = "#1F3A5F"
BLUE_MID = "#3E5C8A"
BLUE_FILL = "#EEF2F7"
GOLD = "#B8963E"
GOLD_FILL = "#F6EFDD"
GREY = "#8A8F98"
GREY_LIGHT = "#D9DCE1"
TEXT = "#1B1F24"
WHITE = "#FFFFFF"
FONT = "Helvetica, Arial, sans-serif"

W = 820
out: list[str] = []


def emit(s: str) -> None:
    out.append(s)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=9.5, weight="normal", fill=TEXT, anchor="middle", style="normal"):
    extra = f' font-style="{style}"' if style != "normal" else ""
    emit(
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>{esc(s)}</text>'
    )


def lines(x, y, rows, size=9.5, lh=None, weight="normal", fill=TEXT, anchor="middle", style="normal"):
    lh = lh or size * 1.3
    for i, r in enumerate(rows):
        text(x, y + i * lh, r, size, weight, fill, anchor, style)


def rect(x, y, w, h, fill=WHITE, stroke=BLUE, sw=0.8, r=3, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    emit(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'
    )


def line(x1, y1, x2, y2, stroke=BLUE, sw=0.8, dash=None, marker=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    emit(
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{sw}"{d}{m}/>'
    )


def path(d, stroke=BLUE, sw=0.8, dash=None, marker=None, fill="none"):
    dd = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    emit(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dd}{m}/>')


def circle(cx, cy, r, fill=WHITE, stroke=BLUE, sw=0.8):
    emit(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def arrow(x1, y1, x2, y2, stroke=BLUE, sw=0.8, dash=None, marker="arrow"):
    line(x1, y1, x2, y2, stroke, sw, dash, marker)


def box(x, y, w, h, title, sub=(), fill=WHITE, stroke=BLUE, dash=None, title_fill=TEXT, sub_fill=None,
        title_size=11, sub_size=9, sw=0.8):
    rect(x, y, w, h, fill, stroke, sw, 4, dash)
    n_sub = len(sub)
    block = title_size + (n_sub * sub_size * 1.3 if n_sub else 0)
    ty = y + h / 2 - block / 2 + title_size * 0.85
    text(x + w / 2, ty, title, title_size, "bold", title_fill)
    if sub:
        lines(x + w / 2, ty + title_size * 1.3, sub, sub_size, None, "normal", sub_fill or GREY, "middle", "italic")


def carriage_return(x_from, y_from, y_mid, x_to, y_to, stroke=BLUE):
    """Connector from the right end of one row to the left start of the next."""
    path(
        f"M {x_from:.1f} {y_from:.1f} H {x_from + 8:.1f} V {y_mid:.1f} H {x_to:.1f} V {y_to - 2:.1f}",
        stroke, 0.8, None, "arrow",
    )


# ================================================================ PANEL A
PA_Y = 30
text(W / 2, 17, "Benchmark Construction and Complete-Bundle Statutory Retrieval", 13, "bold", BLUE)
text(20, PA_Y + 15, "A", 14, "bold", BLUE, "start")
text(38, PA_Y + 15, "Benchmark construction", 11, "bold", TEXT, "start")

bw, gap, x0, bh = 180, 20, 20, 60
row1_y = PA_Y + 26
stages_a = [
    ("667 atomic examination questions", ["from 16 Law College conveyancing", "papers, 2018 to 2026"]),
    ("210 keep or enrich candidates", ["background-boundary problems", "quarantined"]),
    ("144 clean and confident questions", ["Tier A; OCR-poor or low-confidence", "items sent to manual review"]),
    ("Statute-only authority filtering", ["mixed, case-law and unclear", "questions reserved, not forced"]),
    ("Independent research agent", ["verbatim excerpts from the frozen", "corpus; roles and hop counts"]),
    ("Independent verification agent", ["blind to the research; verified,", "partial, rejected or unresolved"]),
    ("50 proposed-gold questions", ["in 40 legal matters", "eligible after verification"]),
    ("Lawyer validation: pending", ["0 approvals to date", "review packets and forms shipped"]),
]
ax, ay = [], []
for i, (t, sub) in enumerate(stages_a):
    col = i % 4
    x = x0 + col * (bw + gap)
    y = row1_y if i < 4 else row1_y + bh + 44
    ax.append(x)
    ay.append(y)
    if i == 6:
        box(x, y, bw, bh, t, sub, fill=BLUE, stroke=BLUE, title_fill=WHITE, sub_fill="#C9D3E3")
    elif i == 7:
        box(x, y, bw, bh, t, sub, fill=WHITE, stroke=GREY, dash="4,3", title_fill=GREY, sub_fill=GREY)
    elif i in (4, 5):
        box(x, y, bw, bh, t, sub)
        line(x + 3, y + 5, x + 3, y + bh - 5, GOLD, 2.4)
    else:
        box(x, y, bw, bh, t, sub, fill=BLUE_FILL)
    if col < 3:
        arrow(x + bw + 1.5, y + bh / 2, x + bw + gap - 2.5, y + bh / 2)

# data-state strips
sh = 15


def strip(xa, xb, y, label, fill, stroke, dash=None, tfill=TEXT):
    rect(xa, y, xb - xa, sh, fill, stroke, 0.7, 2, dash)
    text((xa + xb) / 2, y + 10.5, label, 8.5, "normal", tfill)


s1_y = row1_y + bh + 5
strip(ax[0], ax[3] + bw, s1_y, "data state: original facts, as set in the examination paper", BLUE_FILL, BLUE)
row2_y = ay[4]
s2_y = row2_y + bh + 5
strip(ax[4], ax[5] + bw, s2_y, "original facts + labelled enriched facts (synthetic, marked as such)", GOLD_FILL, GOLD)
strip(ax[6], ax[6] + bw, s2_y, "proposed gold", BLUE, BLUE, None, WHITE)
strip(ax[7], ax[7] + bw, s2_y, "lawyer-approved gold: none yet", WHITE, GREY, "3,2", GREY)

# carriage return from stage 4 to stage 5
carriage_return(ax[3] + bw, row1_y + bh / 2, s1_y + sh + 10, ax[4] + bw / 2, row2_y)

# gold fields, bracketed to the annotation stages 5-7
gf_y = s2_y + sh + 30
gf_h = 28
br_y = gf_y - 12
path(f"M {ax[4]:.1f} {s2_y + sh + 4:.1f} V {br_y:.1f} H {ax[6] + bw:.1f} V {s2_y + sh + 4:.1f}", GREY, 0.7)
mid = (ax[4] + ax[6] + bw) / 2
line(mid, br_y, mid, gf_y - 1.5, GREY, 0.7, None, "arrowGrey")
text(mid + 6, br_y - 3, "gold fields per question (annotation output; proposed gold). Indispensable sections define success in Panel B.",
     8.5, "normal", GREY, "start", "italic")

fields = [
    ("legal issue",), ("governing Act",), ("indispensable", "sections"), ("supporting", "sections"),
    ("legal-hop", "count"), ("temporal", "applicability"), ("claim-level", "provenance"),
]
fgap = 8
fw = (W - 40 - 6 * fgap) / 7
for i, f in enumerate(fields):
    fx = 20 + i * (fw + fgap)
    gold = f[0] == "indispensable"
    rect(fx, gf_y, fw, gf_h, GOLD_FILL if gold else WHITE, GOLD if gold else BLUE_MID, 1.0 if gold else 0.7, 3)
    if len(f) == 1:
        text(fx + fw / 2, gf_y + gf_h / 2 + 3.5, f[0], 9, "bold" if gold else "normal")
    else:
        text(fx + fw / 2, gf_y + gf_h / 2 - 2, f[0], 9, "bold" if gold else "normal")
        text(fx + fw / 2, gf_y + gf_h / 2 + 9, f[1], 9, "bold" if gold else "normal")

# legend
lg_y = gf_y + gf_h + 18
leg = [
    (BLUE_FILL, BLUE, None, "original facts"),
    (GOLD_FILL, GOLD, None, "labelled enriched facts"),
    (BLUE, BLUE, None, "proposed gold (agent-produced, agent-verified)"),
    (WHITE, GREY, "3,2", "lawyer-approved gold (pending; none exists yet)"),
]
lx = 20
for f, s, d, lab in leg:
    rect(lx, lg_y - 8, 16, 9, f, s, 0.7, 1.5, d)
    text(lx + 21, lg_y, lab, 8.5, "normal", TEXT, "start")
    lx += 21 + len(lab) * 4.4 + 22

PA_END = lg_y + 10
rect(10, PA_Y, W - 20, PA_END - PA_Y, "none", GREY_LIGHT, 0.7, 5)

# ================================================================ PANEL B
PB_Y = PA_END + 10
text(20, PB_Y + 15, "B", 14, "bold", BLUE, "start")
text(38, PB_Y + 15, "Complete-bundle statutory retrieval", 11, "bold", TEXT, "start")

bw2, gap2, bh2 = 148, 10, 56
r1_y = PB_Y + 26
r2_y = r1_y + bh2 + 26
stages_b = [
    ("Scenario background", ["+ legal question", "one query string"]),
    ("Act-level router", ["sum of top fused section", "scores per Act"]),
    ("Candidate Acts", ["top Acts kept; amending", "Acts fold into principal"]),
    ("Hybrid section retrieval", ["BM25F + dense (bge-base),", "fused by reciprocal rank"]),
    ("Seed sections", ["top routed sections"]),
    ("Typed-edge expansion", ["out-edges of every seed;", "support accumulates"]),
    ("Temporal filtering", ["drop sections not in force", "at the reference date"]),
    ("Reranking", ["cross-encoder + fused score", "+ graph support"]),
    ("Top-k statutory sections", ["the retrieved bundle"]),
]
bx, by = [], []
for i, (t, sub) in enumerate(stages_b):
    if i < 5:
        x, y, col = 20 + i * (bw2 + gap2), r1_y, i
    else:
        x, y, col = 20 + (i - 5) * (bw2 + gap2), r2_y, i - 5
    bx.append(x)
    by.append(y)
    if i == 0:
        box(x, y, bw2, bh2, t, sub, fill=BLUE_FILL)
    elif i == 8:
        box(x, y, bw2, bh2, t, sub, fill=BLUE, stroke=BLUE, title_fill=WHITE, sub_fill="#C9D3E3")
    else:
        box(x, y, bw2, bh2, t, sub)
    last_in_row = (i == 4) or (i == 8)
    if not last_in_row:
        arrow(x + bw2 + 1.5, y + bh2 / 2, x + bw2 + gap2 - 2.5, y + bh2 / 2)

carriage_return(bx[4] + bw2, r1_y + bh2 / 2, r1_y + bh2 + 13, bx[5] + bw2 / 2, r2_y)

# ---- lower row: statutory graph (left) and scoring (right)
low_y = r2_y + bh2 + 24
g_x0, g_x1 = 20, 500
e_x0, e_x1 = 512, W - 20

# arrow from top-k into scoring
line(bx[8] + bw2 / 2, r2_y + bh2 + 1.5, bx[8] + bw2 / 2, low_y - 2, BLUE, 0.8, None, "arrow")
text(bx[8] + bw2 / 2 + 5, low_y - 7, "retrieved bundle", 8, "normal", GREY, "start", "italic")
# dotted links from router / seeds / expansion into the graph
for i, lab in ((2, "Acts"), (4, "seeds")):
    cx = bx[i] + bw2 / 2
    line(cx, r1_y + bh2 + 1.5, cx, r2_y - 2, GREY, 0.7, "2,2", "arrowGrey")
text(bx[5] + bw2 / 2 + 5, low_y - 7, "expands over the graph below", 8, "normal", GREY, "start", "italic")
line(bx[5] + bw2 / 2, r2_y + bh2 + 1.5, bx[5] + bw2 / 2, low_y - 2, GREY, 0.7, "2,2", "arrowGrey")

# graph box
act_y = low_y + 24
act_h = 112
A_x, A_w = 30, 205
B_x, B_w = 252, 112
C_x, C_w = 381, 100


def act(x, w, title, sub, stroke=BLUE):
    rect(x, act_y, w, act_h, WHITE, stroke, 0.8, 4)
    rect(x, act_y, w, 16, stroke, stroke, 0.8, 4)
    text(x + w / 2, act_y + 11.5, title, 8.5, "bold", WHITE)
    text(x + w / 2, act_y + 27, sub, 7.5, "normal", GREY, "middle", "italic")


text(g_x0 + 8, low_y + 13, "Statutory corpus: Act and section nodes joined by typed edges", 9.5, "bold", TEXT, "start")
act(A_x, A_w, "Act A (principal enactment)", "sections dated by the Act or inserting amendment")
act(B_x, B_w, "Act B (principal)", "another enactment")
act(C_x, C_w, "Act C (amending Act)", "kept as its own document", GOLD)

R = 10
y1, y2 = act_y + 52, act_y + 92
S = {
    "A2": (A_x + 32, y1), "A5": (A_x + 102, y1), "A9": (A_x + 172, y1),
    "A14": (A_x + 67, y2), "A21": (A_x + 145, y2),
    "B3": (B_x + 30, y1), "B7": (B_x + 78, y2), "C1": (C_x + C_w / 2, y1 + 22),
}
labels = {"A2": "s.2", "A5": "s.5", "A9": "s.9", "A14": "s.14", "A21": "s.21", "B3": "s.3", "B7": "s.7", "C1": "s.1"}
seeds = {"A5", "A9"}
expanded = {"A2", "A14", "B7", "C1"}

EDGE_STYLES = {
    "DEFINES": (BLUE, None),
    "EXCEPTS": (BLUE, "4,3"),
    "QUALIFIES": (BLUE, "1.5,2"),
    "PROCEDURALLY_REQUIRES": (BLUE, "6,2,1.5,2"),
    "CROSS_REFERENCES": (GREY, "3,3"),
    "AMENDS": (GOLD, None),
}


def marker_for(col):
    return "arrowGold" if col == GOLD else ("arrowGrey" if col == GREY else "arrow")


def edge(a, b, typ, bend=0.0):
    (x1, y1_), (x2, y2_) = S[a], S[b]
    dx, dy = x2 - x1, y2_ - y1_
    L = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / L, dy / L
    sx, sy = x1 + ux * (R + 1), y1_ + uy * (R + 1)
    ex, ey = x2 - ux * (R + 1.5), y2_ - uy * (R + 1.5)
    col, dash = EDGE_STYLES[typ]
    if bend:
        mx, my = (sx + ex) / 2 - uy * bend, (sy + ey) / 2 + ux * bend
        path(f"M {sx:.1f} {sy:.1f} Q {mx:.1f} {my:.1f} {ex:.1f} {ey:.1f}", col, 0.9, dash, marker_for(col))
    else:
        line(sx, sy, ex, ey, col, 0.9, dash, marker_for(col))


edge("A9", "A2", "DEFINES", bend=-16)
edge("A5", "A2", "DEFINES")
edge("A14", "A5", "EXCEPTS")
edge("A5", "A9", "QUALIFIES", bend=14)
edge("A9", "B7", "PROCEDURALLY_REQUIRES")
edge("A21", "B3", "CROSS_REFERENCES")
edge("C1", "A5", "AMENDS", bend=-34)

for k, (cx, cy) in S.items():
    if k in seeds:
        circle(cx, cy, R, GOLD_FILL, GOLD, 1.2)
        text(cx, cy + 3, labels[k], 7.5, "bold")
    elif k in expanded:
        circle(cx, cy, R, BLUE_FILL, BLUE, 0.9)
        text(cx, cy + 3, labels[k], 7.5)
    else:
        circle(cx, cy, R, WHITE, GREY, 0.8)
        text(cx, cy + 3, labels[k], 7.5, "normal", GREY)

# node legend
nl_y = act_y + act_h + 14
for dx_, (f, s, sw, lab) in enumerate((
    (GOLD_FILL, GOLD, 1.1, "seed section (hybrid retrieval)"),
    (BLUE_FILL, BLUE, 0.9, "reached by typed-edge expansion"),
    (WHITE, GREY, 0.8, "not retrieved"),
)):
    xx = A_x + (0, 150, 305)[dx_]
    circle(xx + 5, nl_y - 3, 4.5, f, s, sw)
    text(xx + 14, nl_y, lab, 8, "normal", TEXT, "start")
text(g_x1 - 8, low_y + 13, "edges run from source to target section", 7.5, "normal", GREY, "end", "italic")

# edge-type legend: two columns of three
el_y = nl_y + 18
cues = {
    "DEFINES": "“within the meaning of”; defined-term use",
    "EXCEPTS": "“notwithstanding”; “shall not apply”",
    "QUALIFIES": "“subject to”",
    "PROCEDURALLY_REQUIRES": "“in the manner prescribed”; “under section”",
    "CROSS_REFERENCES": "any other section reference",
    "AMENDS": "amending-Act section to principal section",
}
for i, (typ, (col, dash)) in enumerate(EDGE_STYLES.items()):
    colx = A_x + (i // 3) * 235
    yy = el_y + (i % 3) * 24
    line(colx, yy, colx + 30, yy, col, 1.1, dash, marker_for(col))
    text(colx + 38, yy + 3, typ, 8.5, "bold", TEXT, "start")
    text(colx + 38, yy + 13, cues[typ], 7.5, "normal", GREY, "start", "italic")

g_end = el_y + 2 * 24 + 22
rect(g_x0, low_y, g_x1 - g_x0, g_end - low_y, "none", GREY_LIGHT, 0.7, 5)

# ---- scoring box
text(e_x0 + 8, low_y + 13, "Scoring: complete-indispensable recall", 9.5, "bold", TEXT, "start")
ey = low_y + 32
text(e_x0 + 8, ey, "Indispensable gold sections (from Panel A):", 8.5, "normal", TEXT, "start")
for j, lab in enumerate(("s.5", "s.9", "s.14")):
    gx = e_x0 + 188 + j * 30
    rect(gx, ey - 9, 26, 13, GOLD_FILL, GOLD, 0.9, 2)
    text(gx + 13, ey + 1, lab, 8, "bold")
text(e_x0 + 8, ey + 12, "supporting sections are reported separately and never required", 7.5, "normal", GREY, "start", "italic")


def case(y, title, retrieved, missing, ok):
    rect(e_x0 + 8, y, e_x1 - e_x0 - 16, 50, WHITE, GREY_LIGHT, 0.7, 3)
    text(e_x0 + 15, y + 13, title, 8.5, "bold", TEXT, "start")
    text(e_x0 + 15, y + 31, "retrieved top-k:", 8, "normal", GREY, "start")
    for j, lab in enumerate(retrieved):
        gx = e_x0 + 78 + j * 28
        gold = lab in ("s.5", "s.9", "s.14")
        rect(gx, y + 21, 26, 13, GOLD_FILL if gold else WHITE, GOLD if gold else BLUE_MID, 0.8, 2)
        text(gx + 13, y + 31, lab, 8, "bold" if gold else "normal")
    if missing:
        gx = e_x0 + 78 + len(retrieved) * 28
        rect(gx, y + 21, 26, 13, WHITE, GREY, 0.7, 2, "2,1.5")
        text(gx + 13, y + 31, missing, 8, "normal", GREY)
        text(gx + 13, y + 44, "missing", 6.5, "normal", GREY)
    vx = e_x1 - 72
    if ok:
        circle(vx, y + 27, 9, WHITE, GOLD, 1.2)
        path(f"M {vx - 4.5:.1f} {y + 27:.1f} L {vx - 1:.1f} {y + 30.5:.1f} L {vx + 5:.1f} {y + 23:.1f}", GOLD, 1.6)
        text(vx + 14, y + 25, "complete", 8.5, "bold", TEXT, "start")
        text(vx + 14, y + 35, "score 1", 7.5, "normal", GREY, "start")
    else:
        circle(vx, y + 27, 9, WHITE, GREY, 1.0)
        path(f"M {vx - 4:.1f} {y + 23:.1f} L {vx + 4:.1f} {y + 31:.1f}", GREY, 1.5)
        path(f"M {vx + 4:.1f} {y + 23:.1f} L {vx - 4:.1f} {y + 31:.1f}", GREY, 1.5)
        text(vx + 14, y + 25, "incomplete", 8.5, "bold", GREY, "start")
        text(vx + 14, y + 35, "score 0", 7.5, "normal", GREY, "start")


case(ey + 22, "Every indispensable section retrieved", ["s.5", "s.9", "s.14", "s.2"], None, True)
case(ey + 80, "One indispensable section missing", ["s.5", "s.9", "s.2"], "s.14", False)

note_y = ey + 148
lines(e_x0 + 8, note_y, [
    "A question succeeds only when every indispensable section is",
    "in the top-k. Two of three earns no partial credit: the metric is",
    "binary per question and averaged over questions.",
], 8.5, 11.5, "normal", TEXT, "start")
lines(e_x0 + 8, note_y + 40, [
    "Gold is proposed and pending lawyer validation; every score is a",
    "measurement against proposed gold.",
], 7.5, 10, "normal", GREY, "start", "italic")

e_end = max(g_end, note_y + 56)
rect(e_x0, low_y, e_x1 - e_x0, e_end - low_y, "none", BLUE, 0.8, 5)
PB_END = max(g_end, e_end) + 10
rect(10, PB_Y, W - 20, PB_END - PB_Y, "none", GREY_LIGHT, 0.7, 5)

H = PB_END + 8

# ---------------------------------------------------------------- write
svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
    "<defs>\n"
    + "".join(
        f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
        f'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{col}"/></marker>\n'
        for name, col in (("arrow", BLUE), ("arrowGold", GOLD), ("arrowGrey", GREY))
    )
    + "</defs>\n"
    + f'<rect width="{W}" height="{H}" fill="{WHITE}"/>\n'
    + "\n".join(out)
    + "\n</svg>\n"
)

here = Path(__file__).resolve().parent
svg_path = here / "architecture.svg"
svg_path.write_text(svg, encoding="utf-8")
try:
    import cairosvg

    cairosvg.svg2pdf(url=str(svg_path), write_to=str(here / "architecture.pdf"))
    cairosvg.svg2png(url=str(svg_path), write_to=str(here / "architecture-preview.png"), output_width=3280)
    print(f"wrote architecture.svg ({W}x{H}), architecture.pdf, architecture-preview.png")
except ImportError:
    print("wrote architecture.svg (cairosvg not installed; PDF skipped)")
