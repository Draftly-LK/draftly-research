"""Generate research-paper/figures/corpus-retrieval.svg (+ .pdf, preview).

Two panels: (A) structured statutory corpus -> section index + typed graph,
(B) baseline and structure-aware retrieval -> top-k -> evaluation against the
gold indispensable bundle. Pure flat SVG with editable text.

Run from the repo root:
    uv run python research-paper/figures/make_corpus_retrieval.py
"""

from __future__ import annotations

from pathlib import Path

NAVY = "#1F3A5F"
GOLD = "#B8963E"
PALE = "#EAF0F7"
PALE_GOLD = "#FFF8E7"
LGREY = "#F4F5F7"
TEXT = "#263238"
GREY = "#8A8F98"
SEP = "#C9CED6"
WHITE = "#FFFFFF"
FONT = "Helvetica, Arial, sans-serif"

W, H = 900, 440
out: list[str] = []


def emit(s: str) -> None:
    out.append(s)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=9, weight="normal", fill=TEXT, anchor="middle", style="normal"):
    extra = f' font-style="{style}"' if style != "normal" else ""
    emit(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
         f'fill="{fill}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def rect(x, y, w, h, fill=WHITE, stroke=NAVY, sw=1.0, r=4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    emit(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}" '
         f'stroke="{stroke}" stroke-width="{sw}"{d}/>')


def path(d, stroke=NAVY, sw=1.0, dash=None, marker=None, fill="none"):
    dd = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    emit(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" '
         f'stroke-linejoin="round"{dd}{m}/>')


def poly(points, stroke=NAVY, sw=1.0, dash=None, marker="arrowNavy"):
    path("M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points), stroke, sw, dash, marker)


def circle(cx, cy, r, fill=WHITE, stroke=NAVY, sw=1.0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    emit(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def panel_letter(x, y, letter):
    circle(x, y, 8.5, NAVY, NAVY, 0)
    text(x, y + 3.8, letter, 10.5, "bold", WHITE)


def doc_stack(cx, top, w=44, h=34, n=3):
    for i in range(n):
        off = (n - 1 - i) * 4
        rect(cx - w / 2 + off, top + (n - 1 - i) * -4 + 8, w, h, PALE if i == n - 1 else WHITE, NAVY, 0.9, 2)
    for k in range(4):
        yy = top + 8 + 8 + k * 6
        path(f"M {cx - w / 2 + 7:.1f} {yy:.1f} H {cx + w / 2 - (7 if k < 3 else 18):.1f}", GREY, 0.8)


def doc_card(x, y, w, h, fill=PALE):
    fold = 9
    emit(f'<path d="M {x:.1f} {y:.1f} H {x + w - fold:.1f} L {x + w:.1f} {y + fold:.1f} V {y + h:.1f} H {x:.1f} Z" '
         f'fill="{fill}" stroke="{NAVY}" stroke-width="1" stroke-linejoin="round"/>')
    emit(f'<path d="M {x + w - fold:.1f} {y:.1f} V {y + fold:.1f} H {x + w:.1f}" fill="none" stroke="{NAVY}" stroke-width="1"/>')


# ================================================================ frame
text(W / 2, 20, "Structured Statutory Corpus and Complete-Bundle Retrieval Benchmark", 14, "bold", NAVY)
PT, PB = 36, H - 10
AX0, AX1 = 12, 372
BX0, BX1 = 384, 888
rect(AX0, PT, AX1 - AX0, PB - PT, WHITE, SEP, 0.9, 6, "5,4")
rect(BX0, PT, BX1 - BX0, PB - PT, WHITE, SEP, 0.9, 6, "5,4")
panel_letter(AX0 + 16, PT + 16, "A")
text(AX0 + 30, PT + 20, "Structured Statutory Corpus", 12, "bold", TEXT, "start")
panel_letter(BX0 + 16, PT + 16, "B")
text(BX0 + 30, PT + 20, "Retrieval and Evaluation", 12, "bold", TEXT, "start")

# ================================================================ Panel A
# source documents
SX = 62
doc_stack(SX, 78)
text(SX, 132, "Sri Lankan Statutes", 9.5, "bold")
text(SX, 143, "Principal and amending enactments", 7.5, "normal", GREY)
poly([(SX + 26, 108), (118, 108)])

# canonical corpus card
CX0, CY0, CW, CH = 120, 72, 140, 76
rect(CX0, CY0, CW, CH, NAVY, NAVY, 1, 5)
text(CX0 + CW / 2, CY0 + 15, "Canonical Statutory Corpus", 9.5, "bold", WHITE)
for i, s in enumerate(("52 principal enactments", "60 amending Acts", "4,557 sections", "17,854 provisions")):
    text(CX0 + CW / 2, CY0 + 30 + i * 11.5, s, 8.5, "normal", "#DCE4F0")

# branch 1: section index (upper right)
IX0, IY0, IW = 282, 82, 84
poly([(CX0 + CW, 96), (IX0 - 2, 96)])
rect(IX0, IY0, IW, 20, PALE, NAVY, 1, 4)
text(IX0 + IW / 2, IY0 + 13.5, "Section Index", 9, "bold")
for i, s in enumerate(("Act title", "Section heading", "Section text")):
    yy = IY0 + 26 + i * 14
    rect(IX0 + 6, yy, IW - 12, 11, WHITE, NAVY, 0.7, 5)
    text(IX0 + IW / 2, yy + 8, s, 7, "normal")
idx_bottom = IY0 + 26 + 2 * 14 + 11

# branch 2: typed statutory graph (below corpus)
GX0, GY0, GX1, GY1 = 26, 170, 358, 318
poly([(CX0 + CW / 2, CY0 + CH), (CX0 + CW / 2, GY0 - 2)])
rect(GX0, GY0, GX1 - GX0, GY1 - GY0, LGREY, SEP, 0.8, 5)
text(GX0 + 10, GY0 + 14, "Typed Statutory Graph", 9.5, "bold", TEXT, "start")

R = 10
N = {"s2": (58, 218), "s5": (118, 218), "s9": (178, 218), "s14": (98, 270), "s3": (178, 278)}
LAB = {"s2": "§2", "s5": "§5", "s9": "§9", "s14": "§14", "s3": "§3"}
STYLE = {
    "DEFINES": (NAVY, None), "EXCEPTS": (NAVY, "4,3"), "QUALIFIES": (NAVY, "1.5,2"),
    "PROCEDURALLY_REQUIRES": (NAVY, "6,2,1.5,2"), "CROSS_REFERENCES": (NAVY, "3,3"), "AMENDS": (GOLD, None),
}


def edge(a, b, typ, bend=0.0):
    (x1, y1), (x2, y2) = N[a], N[b]
    dx, dy = x2 - x1, y2 - y1
    L = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / L, dy / L
    sx, sy = x1 + ux * (R + 1), y1 + uy * (R + 1)
    ex, ey = x2 - ux * (R + 1.5), y2 - uy * (R + 1.5)
    col, dash = STYLE[typ]
    mk = "arrowGold" if col == GOLD else "arrowNavy"
    if bend:
        mx, my = (sx + ex) / 2 - uy * bend, (sy + ey) / 2 + ux * bend
        path(f"M {sx:.1f} {sy:.1f} Q {mx:.1f} {my:.1f} {ex:.1f} {ey:.1f}", col, 1.0, dash, mk)
    else:
        path(f"M {sx:.1f} {sy:.1f} L {ex:.1f} {ey:.1f}", col, 1.0, dash, mk)


edge("s9", "s2", "DEFINES", bend=-18)
edge("s5", "s2", "EXCEPTS")
edge("s5", "s9", "QUALIFIES", bend=14)
edge("s9", "s14", "PROCEDURALLY_REQUIRES")
edge("s14", "s2", "CROSS_REFERENCES")
edge("s3", "s5", "AMENDS", bend=-14)
for k, (cx, cy) in N.items():
    gold = k == "s3"
    circle(cx, cy, R, PALE_GOLD if gold else WHITE, GOLD if gold else NAVY, 1.1)
    text(cx, cy + 2.8, LAB[k], 7.5, "bold", TEXT)
text(178, 296, "amending Act", 6.5, "normal", GOLD)

# edge legend
LX, LY = 212, GY0 + 26
for i, (typ, (col, dash)) in enumerate(STYLE.items()):
    yy = LY + i * 15
    path(f"M {LX:.1f} {yy:.1f} H {LX + 26:.1f}", col, 1.1, dash, "arrowGold" if col == GOLD else "arrowNavy")
    text(LX + 33, yy + 2.8, typ, 7.5, "bold", TEXT, "start")
text(GX0 + 10, GY1 - 7, "Heuristically typed and deterministically validated", 7.5, "normal", GREY, "start", "italic")

# ================================================================ Panel B
# scenario question (document card)
QX, QY, QW, QH = 398, 96, 80, 60
doc_card(QX, QY, QW, QH)
text(QX + QW / 2, QY + 20, "Scenario Question", 8.5, "bold")
text(QX + QW / 2, QY + 36, "Factual background", 7.5, "normal", GREY)
text(QX + QW / 2, QY + 48, "Legal question", 7.5, "normal", GREY)

# baselines card
BLX, BLY, BLW, BLH = 520, 66, 176, 88
rect(BLX, BLY, BLW, BLH, PALE, NAVY, 1, 5)
text(BLX + BLW / 2, BLY + 14, "Retrieval Baselines", 9.5, "bold")
for i, s in enumerate(("BM25", "Field-weighted BM25", "Dense retrieval", "Hybrid RRF", "Cross-encoder reranking")):
    text(BLX + BLW / 2, BLY + 28 + i * 13, s, 8, "normal")

# structure-aware retriever container
SRX, SRY, SRW, SRH = 500, 176, 290, 94
rect(SRX, SRY, SRW, SRH, NAVY, NAVY, 1, 6)
text(SRX + 10, SRY + 14, "Structure-Aware Retriever", 9.5, "bold", WHITE, "start")
stages = [("Act", "routing"), ("Hybrid section", "retrieval"), ("Typed-edge", "expansion"), ("Temporal", "filtering"), ("Reranking", "")]
stw, stg = 50, 8
stx0 = SRX + (SRW - (5 * stw + 4 * stg)) / 2
sty, sth = SRY + 26, 50
scx = []
for i, (l1, l2) in enumerate(stages):
    x = stx0 + i * (stw + stg)
    scx.append(x + stw / 2)
    rect(x, sty, stw, sth, "#2E4D78", "#9FB3CF", 0.8, 4)
    if l2:
        text(x + stw / 2, sty + sth / 2 - 1, l1, 7.5, "bold", WHITE)
        text(x + stw / 2, sty + sth / 2 + 9, l2, 7.5, "bold", WHITE)
    else:
        text(x + stw / 2, sty + sth / 2 + 3, l1, 7.5, "bold", WHITE)
    if i < 4:
        poly([(x + stw + 1, sty + sth / 2), (x + stw + stg - 2, sty + sth / 2)], "#DCE4F0", 0.9, None, "arrowPale")
sub_y = SRY + SRH + 11
text(scx[0], sub_y, "Aggregate section evidence", 7, "normal", GREY, "middle", "italic")
text(scx[3], sub_y, "Reference-date constraints", 7, "normal", GREY, "middle", "italic")

# feeds: section index -> baselines (with branch to hybrid stage)
poly([(IX0 + IW, 92), (BLX - 2, 92)])
circle(506, 92, 2, NAVY, NAVY, 0)
poly([(506, 92), (506, 166), (scx[1], 166), (scx[1], SRY - 2)])
text(512, 160, "section index", 6.5, "normal", GREY, "start", "italic")
# scenario -> both tracks
TRX = 490
path(f"M {QX + QW:.1f} {QY + QH / 2:.1f} H {TRX:.1f}", NAVY, 1)
poly([(TRX, QY + QH / 2), (TRX, 112), (BLX - 2, 112)])
poly([(TRX, QY + QH / 2), (TRX, sty + sth / 2), (SRX - 2, sty + sth / 2)])
# typed graph -> typed-edge expansion (enters from below)
poly([(GX1, 288), (scx[2], 288), (scx[2], SRY + SRH + 2)])
text(GX1 + 8, 284, "typed graph", 6.5, "normal", GREY, "start", "italic")

# output: top-k statutory sections
OX, OY, OW, OH = 804, 88, 76, 118
rect(OX, OY, OW, OH, PALE, NAVY, 1, 5)
text(OX + OW / 2, OY + 14, "Top-k Statutory", 8.5, "bold")
text(OX + OW / 2, OY + 25, "Sections", 8.5, "bold")
for i, s in enumerate(("1  Act A §5", "2  Act B §9", "3  Act A §14")):
    yy = OY + 36 + i * 22
    rect(OX + 7, yy, OW - 14, 17, WHITE, NAVY, 0.8, 3)
    text(OX + OW / 2, yy + 11.5, s, 7.5, "normal")
poly([(BLX + BLW, 110), (OX - 2, 110)])
poly([(SRX + SRW, sty + sth / 2), (796, sty + sth / 2), (796, OY + OH - 20), (OX - 2, OY + OH - 20)])

# gold indispensable bundle
GBX, GBY, GBW, GBH = 398, 330, 150, 52
rect(GBX, GBY, GBW, GBH, PALE_GOLD, GOLD, 1.1, 5)
text(GBX + GBW / 2, GBY + 14, "Gold Indispensable Bundle", 8.5, "bold")
for i, s in enumerate(("Act A §5", "Act B §9", "Act A §14")):
    xx = GBX + 8 + i * 46
    rect(xx, GBY + 24, 42, 16, WHITE, GOLD, 1, 3)
    text(xx + 21, GBY + 35, s, 7.5, "bold")

# evaluation card
EX, EY, EW, EH = 566, 300, 314, 106
rect(EX, EY, EW, EH, WHITE, NAVY, 1, 5)
text(EX + 10, EY + 15, "Retrieval Evaluation", 9.5, "bold", TEXT, "start")
for i, s in enumerate(("Recall@5, @10, @20", "MRR", "nDCG@10", "Statute accuracy")):
    text(EX + 12, EY + 31 + i * 12, s, 8, "normal", TEXT, "start")
rect(EX + 8, EY + 82, 132, 16, PALE_GOLD, GOLD, 1.2, 3)
text(EX + 74, EY + 93, "Complete-Bundle Recall", 8, "bold")
# mini illustration
MX = EX + 160
for row, (chips, ok) in enumerate((((True, True, True), True), ((True, False, True), False))):
    yy = EY + 78 + row * 18
    for j, present in enumerate(chips):
        xx = MX + j * 22
        lab = ("§5", "§9", "§14")[j]
        if present:
            rect(xx, yy - 6, 19, 12, PALE_GOLD, GOLD, 0.9, 2)
            text(xx + 9.5, yy + 2.5, lab, 6.5, "bold")
        else:
            rect(xx, yy - 6, 19, 12, WHITE, GREY, 0.8, 2, "2,1.5")
    vx = MX + 3 * 22 + 12
    if ok:
        circle(vx, yy, 6, WHITE, GOLD, 1.1)
        path(f"M {vx - 3:.1f} {yy:.1f} L {vx - 0.8:.1f} {yy + 2.4:.1f} L {vx + 3.4:.1f} {yy - 2.6:.1f}", GOLD, 1.3)
        text(vx + 11, yy + 2.5, "Complete = 1", 7.5, "bold", TEXT, "start")
    else:
        circle(vx, yy, 6, WHITE, GREY, 1.0)
        path(f"M {vx - 2.6:.1f} {yy - 2.6:.1f} L {vx + 2.6:.1f} {yy + 2.6:.1f} M {vx + 2.6:.1f} {yy - 2.6:.1f} L {vx - 2.6:.1f} {yy + 2.6:.1f}", GREY, 1.2)
        text(vx + 11, yy + 2.5, "Complete = 0", 7.5, "bold", GREY, "start")
text(MX, EY + 60, "gold sections in top-k", 6.5, "normal", GREY, "start", "italic")

# connectors into evaluation
poly([(OX + OW / 2, OY + OH), (OX + OW / 2, EY - 2)])
text(OX + OW / 2 + 5, (OY + OH + EY) / 2 + 2, "retrieved", 6.5, "normal", GREY, "start", "italic")
poly([(GBX + GBW, GBY + GBH / 2), (EX - 2, GBY + GBH / 2)], GOLD, 1.0, None, "arrowGold")
text(EX + EW / 2, EY + EH + 15, "A question succeeds only when every indispensable section appears in the top-k results.",
     8, "normal", TEXT, "middle", "italic")

# ================================================================ write
svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n<defs>\n'
    + "".join(
        f'<marker id="{n}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
        f'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{c}"/></marker>\n'
        for n, c in (("arrowNavy", NAVY), ("arrowGold", GOLD), ("arrowPale", "#DCE4F0"))
    )
    + f'</defs>\n<rect width="{W}" height="{H}" fill="{WHITE}"/>\n' + "\n".join(out) + "\n</svg>\n"
)
here = Path(__file__).resolve().parent
p = here / "corpus-retrieval.svg"
p.write_text(svg, encoding="utf-8")
try:
    import cairosvg

    cairosvg.svg2pdf(url=str(p), write_to=str(here / "corpus-retrieval.pdf"))
    cairosvg.svg2png(url=str(p), write_to=str(here / "corpus-retrieval-preview.png"), output_width=3600)
    print(f"wrote corpus-retrieval.svg ({W}x{H}), .pdf, -preview.png")
except ImportError:
    print("wrote corpus-retrieval.svg (cairosvg missing; PDF skipped)")
