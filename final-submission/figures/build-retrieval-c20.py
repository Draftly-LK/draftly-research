"""Draw a pastel research-results diagram from Table 4 of final-report.tex.

The report PDF, preview PNG, slide PNG, and editable slide SVG share one layout.
All scores are read from the LaTeX table to prevent divergence from the report.
"""

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures"
PRESENTATION = ROOT / "presentation"
SOURCE = ROOT / "final-report.tex"

# Table name, displayed name, card fill, darker bar fill.
METHODS = [
    ("Hierarchical", "Hierarchical", "#E2ECF9", "#587CB5"),
    ("Hybrid rank fusion", "Hybrid fusion", "#DEF3EA", "#499B88"),
    ("Hierarchical plus typed expansion", "Typed expansion", "#EDE8F5", "#937DB1"),
    ("BM25", "BM25 (hosted method)", "#FCE9DB", "#CA855B"),
]

INK = "#243348"
MUTED = "#5C6C7C"
STROKE = "#BFC5C8"


def read_results():
    source = SOURCE.read_text(encoding="utf-8")
    table = source.split("Main-test retrieval results (matter-macro means; proposed labels).", 1)[1]
    table = table.split(r"\end{table}", 1)[0]
    rows = {}
    for line in table.splitlines():
        cells = [cell.strip().rstrip("\\").strip() for cell in line.split("&")]
        if len(cells) == 6:
            try:
                rows[cells[0]] = float(cells[3])
            except ValueError:
                pass
    missing = [name for name, _, _, _ in METHODS if name not in rows]
    if missing:
        raise ValueError(f"Table 4 is missing methods: {missing}")
    if not re.search(r"no system completed any of the 20 test questions requiring four or more", source):
        raise ValueError("Hard-question finding changed; review the callout")
    return [rows[name] for name, _, _, _ in METHODS]


def rounded(ax, xy, width, height, fill, *, radius=24, edge=STROKE,
            linewidth=1.3, shadow=False, z=2):
    x, y = xy
    if shadow:
        ax.add_patch(FancyBboxPatch((x + 4, y + 6), width, height,
                                    boxstyle=f"round,pad=0,rounding_size={radius}",
                                    facecolor="#D5D9DC", alpha=0.25,
                                    linewidth=0, zorder=z - 1))
    patch = FancyBboxPatch((x, y), width, height,
                           boxstyle=f"round,pad=0,rounding_size={radius}",
                           facecolor=fill, edgecolor=edge, linewidth=linewidth,
                           zorder=z)
    ax.add_patch(patch)
    return patch


def label(ax, x, y, text, size, *, weight="normal", color=INK, ha="left", va="center"):
    ax.text(x, y, text, fontsize=size, weight=weight, color=color,
            ha=ha, va=va, linespacing=1.13, zorder=8)


def arrow(ax, start, end, *, color="#849097", linewidth=2.1):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>",
                                 mutation_scale=16, color=color,
                                 linewidth=linewidth, zorder=5))


def draw(values, output, *, slide=False):
    scale = 1.77 if slide else 1.0
    size = (12.8, 7.2) if slide else (7.05, 3.97)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })
    fig = plt.figure(figsize=size, facecolor="#FFFDF8")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1600)
    ax.set_ylim(900, 0)
    ax.axis("off")

    # A short process strip explains why C@20 is an all-or-nothing measure.
    rounded(ax, (38, 34), 454, 130, "#FFE8DA", shadow=True)
    label(ax, 65, 77, "1  SCENARIO", 9.5 * scale, weight="bold")
    label(ax, 65, 120, "Question + required provisions", 7.8 * scale)
    rounded(ax, (572, 34), 454, 130, "#E2EDF9", shadow=True)
    label(ax, 599, 77, "2  RETRIEVE TOP 20", 9.5 * scale, weight="bold")
    label(ax, 599, 120, "Ranked statutory sections", 7.8 * scale)
    rounded(ax, (1106, 34), 454, 130, "#DCF0E2", shadow=True)
    label(ax, 1133, 77, "3  COMPLETE?", 9.5 * scale, weight="bold")
    label(ax, 1133, 120, "Every required section found", 7.8 * scale)
    arrow(ax, (497, 99), (562, 99))
    arrow(ax, (1031, 99), (1096, 99))

    rounded(ax, (38, 200), 1010, 574, "#FFFFFF", radius=28, edge="#D0D5D8", shadow=True)
    label(ax, 68, 241, "Complete-indispensable recall at 20", 12.5 * scale, weight="bold")
    label(ax, 68, 277, "C@20  ·  matter-macro mean", 8.5 * scale, color=MUTED)

    row_ys = (326, 432, 538, 644)
    for (name, displayed, pale, saturated), value, y in zip(METHODS, values, row_ys):
        rounded(ax, (68, y), 948, 82, pale, radius=18, edge="#E0E2E2", linewidth=0.8)
        label(ax, 90, y + 41, displayed, 9 * scale, weight="bold")
        rounded(ax, (510, y + 19), 350, 43, "#FFFFFF", radius=11,
                edge="#CFD6D9", linewidth=0.6, z=3)
        rounded(ax, (510, y + 19), 350 * value / 0.42, 43, saturated,
                radius=11, edge=saturated, linewidth=0, z=4)
        label(ax, 1002, y + 41, f"{value:.3f}", 11 * scale,
              weight="bold", ha="right")
    label(ax, 510, 754, "0", 8 * scale, color=MUTED)
    label(ax, 673, 754, "0.2", 8 * scale, color=MUTED)
    label(ax, 839, 754, "0.4", 8 * scale, color=MUTED)

    # Two speech-note cards echo the reference figures' annotated style.
    rounded(ax, (1080, 200), 480, 252, "#FFF5CD", radius=28, shadow=True)
    label(ax, 1113, 261, "0 / 20", 18 * scale, weight="bold", color="#A25B3E")
    label(ax, 1113, 329, "Four-plus-provision\nquestions completed\nby any tested system", 9.8 * scale, va="top")
    rounded(ax, (1080, 476), 480, 298, "#E5F0EA", radius=28, shadow=True)
    label(ax, 1113, 535, "UNCERTAIN LEAD", 10.5 * scale, weight="bold", color="#3B745F")
    label(ax, 1113, 590, "Paired 95% intervals\nfor leading C@20\ndifferences include zero.", 9.8 * scale, va="top")

    rounded(ax, (38, 789), 1522, 83, "#EFF3F4", radius=18,
            edge="#D5DADB", linewidth=0.8)
    label(ax, 64, 818,
          "Offline benchmark: 40 questions / 32 matters  ·  Provisional labels await attorney review",
          8 * scale, color="#425669")
    label(ax, 64, 848, "All scores are offline; hosted search uses BM25.",
          8 * scale, color="#425669")

    output.parent.mkdir(exist_ok=True)
    if slide:
        fig.savefig(output.with_suffix(".png"), dpi=180, facecolor=fig.get_facecolor())
        fig.savefig(output.with_suffix(".svg"), facecolor=fig.get_facecolor())
    else:
        fig.savefig(output.with_suffix(".pdf"), facecolor=fig.get_facecolor())
        fig.savefig(output.with_suffix(".png"), dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    scores = read_results()
    draw(scores, FIGURES / "report-fig-13-retrieval-c20-comparison")
    draw(scores, PRESENTATION / "retrieval-c20-results-slide", slide=True)
    print(dict(zip((name for name, _, _, _ in METHODS), scores)))
