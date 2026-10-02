"""Create a checked vector version of the PaperBanana retrieval diagram.

PaperBanana supplied the visual draft; this redraw fixes arrow directions and
keeps labels editable for the paper. Outputs SVG, PDF, and high-resolution PNG.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


HERE = Path(__file__).resolve().parent
NAVY = "#183A69"
INK = "#21364F"
MUTED = "#5C6E81"
PALE_BLUE = "#EAF2FA"
PALE_GOLD = "#FFF7E4"
GOLD = "#B78D37"


def box(ax, x, y, w, h, *, face="white", edge=NAVY, radius=18,
        lw=2.0, dashed=False):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=face, edgecolor=edge, linewidth=lw,
        linestyle=(0, (5, 4)) if dashed else "solid", zorder=2,
    )
    ax.add_patch(patch)
    return patch


def txt(ax, x, y, value, size, *, bold=False, color=INK,
        ha="left", va="center"):
    ax.text(x, y, value, fontsize=size * 0.4,
            fontweight="bold" if bold else "normal",
            color=color, ha=ha, va=va, linespacing=1.15, zorder=5)


def line(ax, points, *, color=NAVY, lw=3, head=True, head_size=18):
    xs, ys = zip(*points)
    ax.plot(xs[:-1] if head else xs, ys[:-1] if head else ys,
            color=color, lw=lw, solid_capstyle="round", zorder=3)
    if head:
        ax.add_patch(FancyArrowPatch(points[-2], points[-1],
                                    arrowstyle="-|>", mutation_scale=head_size,
                                    linewidth=lw, color=color, zorder=4))


def build():
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42,
                         "svg.fonttype": "none"})
    fig = plt.figure(figsize=(8, 4.5), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1600)
    ax.set_ylim(900, 0)
    ax.axis("off")

    txt(ax, 50, 75, "SHARED INPUTS", 26, bold=True, color=NAVY)
    txt(ax, 390, 75, "SEVEN TESTED RETRIEVERS", 26, bold=True, color=NAVY)
    txt(ax, 1190, 75, "OUTPUT + SCORE", 26, bold=True, color=NAVY)

    # Shared inputs. The graph is separate because only S7 uses its edges.
    box(ax, 50, 130, 265, 375, face="#F7FAFD")
    txt(ax, 75, 169, "Same for S1–S7", 23, bold=True)
    box(ax, 75, 210, 215, 118, face=PALE_BLUE, edge="#9DB7D6", lw=1.7)
    txt(ax, 183, 247, "Scenario query", 22, bold=True, ha="center")
    txt(ax, 183, 289, "Facts + legal issue", 18, color=MUTED, ha="center")
    box(ax, 75, 348, 215, 112, face=PALE_BLUE, edge="#9DB7D6", lw=1.7)
    txt(ax, 183, 384, "Section index", 22, bold=True, ha="center")
    txt(ax, 183, 426, "Title · heading · text", 18, color=MUTED, ha="center")

    box(ax, 50, 575, 265, 120, face=PALE_GOLD, edge=GOLD, lw=2.2)
    txt(ax, 183, 617, "Typed graph", 22, bold=True, ha="center")
    txt(ax, 183, 661, "S7 expansion input only", 18, color="#756539", ha="center")

    # The three method families share the same scenario and section index.
    box(ax, 380, 130, 720, 610, face="#FBFCFE", edge="#C7D3DF", lw=1.7)
    box(ax, 420, 160, 640, 195, face=PALE_BLUE, edge="#A5BDD7", lw=1.9)
    txt(ax, 450, 198, "S1–S5  Flat baselines", 26, bold=True, color=NAVY)
    txt(ax, 452, 245, "S1  BM25", 20)
    txt(ax, 452, 289, "S2  Field-weighted BM25", 20)
    txt(ax, 452, 333, "S3  Dense retrieval", 20)
    txt(ax, 770, 245, "S4  Hybrid RRF", 20)
    txt(ax, 770, 289, "S5  Hybrid +", 20)
    txt(ax, 818, 326, "cross-encoder", 20)

    box(ax, 420, 385, 640, 110, face=PALE_BLUE, edge="#A5BDD7", lw=1.9)
    txt(ax, 450, 421, "S6  Hierarchical retrieval", 25, bold=True, color=NAVY)
    txt(ax, 450, 462, "Route to Acts, then search sections", 20)

    box(ax, 420, 520, 640, 185, face="#F2F6FC", edge=NAVY, lw=2.2)
    txt(ax, 450, 551, "S7  Structure-aware retrieval", 25, bold=True, color=NAVY)
    stages = [
        (442, "Hybrid\nranking"),
        (562, "Act\nrouting"),
        (682, "Search +\nseeds"),
        (802, "Edge\nexpansion"),
        (922, "Date +\nrerank"),
    ]
    for x, name in stages:
        box(ax, x, 586, 102, 82, face="white", edge="#6F90BA", radius=11,
            lw=1.7)
        txt(ax, x + 51, 627, name, 14, bold=True, ha="center")
    for left, _ in stages[:-1]:
        line(ax, [(left + 103, 627), (left + 118, 627)], lw=1.1, head_size=6)

    # Shared-input bus to each method family. The gold graph route goes only
    # to the typed-edge expansion stage, below all navy paths.
    line(ax, [(315, 375), (350, 375)], head=False)
    line(ax, [(350, 255), (350, 625)], head=False)
    line(ax, [(350, 255), (415, 255)])
    line(ax, [(350, 440), (415, 440)])
    line(ax, [(350, 625), (415, 625)])
    line(ax, [(315, 635), (332, 635), (332, 785), (853, 785),
              (853, 670)], color=GOLD, lw=3)

    # All systems independently return the same kind of top-k output.
    line(ax, [(1060, 255), (1137, 255)], head=False)
    line(ax, [(1060, 440), (1137, 440)], head=False)
    line(ax, [(1060, 625), (1137, 625)], head=False)
    line(ax, [(1137, 255), (1137, 625)], head=False)
    line(ax, [(1137, 355), (1182, 355)])

    box(ax, 1190, 190, 350, 215, face=PALE_BLUE, edge="#A5BDD7")
    txt(ax, 1217, 230, "Top-k sections", 24, bold=True, color=NAVY)
    for i, y in enumerate((282, 326, 370), start=1):
        box(ax, 1220, y - 16, 280, 32, face="white", edge="#B1C2D2",
            radius=8, lw=1.2)
        txt(ax, 1240, y, f"{i}   section", 18)

    box(ax, 1190, 455, 350, 150, face=PALE_GOLD, edge=GOLD, lw=2.0)
    txt(ax, 1217, 493, "Proposed gold", 24, bold=True, color=NAVY)
    txt(ax, 1217, 534, "Lawyer validation pending", 18, color="#776B4D")
    for x in (1220, 1313, 1406):
        box(ax, x, 554, 75, 32, face="white", edge=GOLD, radius=8, lw=1.2)

    box(ax, 1190, 665, 350, 140, face="#EFF5EF", edge="#81A18A")
    txt(ax, 1217, 705, "Complete recall C@k", 24, bold=True, color=NAVY)
    txt(ax, 1217, 754, "1 only when all required\nsections appear in top k", 19)

    # Retrieved output and reference bundle are separate inputs to the metric.
    line(ax, [(1540, 355), (1570, 355), (1570, 735), (1538, 735)], lw=2.8)
    line(ax, [(1365, 605), (1365, 663)], color=GOLD, lw=2.8)

    txt(ax, 50, 850,
        "Offline comparison on the frozen corpus. Proposed indispensable labels await attorney review.",
        19, color=MUTED)

    out = HERE / "retrieval-evaluation-paper-ready"
    fig.savefig(out.with_suffix(".svg"), facecolor="white")
    fig.savefig(out.with_suffix(".pdf"), facecolor="white")
    fig.savefig(out.with_suffix(".png"), dpi=200, facecolor="white")
    plt.close(fig)
    print(f"Saved {out}.svg/.pdf/.png")


if __name__ == "__main__":
    build()
