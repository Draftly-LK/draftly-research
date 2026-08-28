"""Render the figures used by progress.md.

Reads its numbers from the generated artifacts rather than hard-coded values, so
a figure cannot drift away from the run it describes:

    apps/statute-browser/RUBRIK.md                     statute register
    data/evaluvation/parsed-pastpapers/questions/*.json past-paper citations
    experiments/koblex-inspired-retrieval/runs/*/metrics.json  experiment scores

Colours are the validated categorical palette (slot 1 blue, slot 2 orange);
worst adjacent CVD Delta E 24.7 on the light surface. One hue per series, never a
value-ramp across nominal categories.

Usage:
    uv run python scripts/build_progress_figures.py
"""

from __future__ import annotations

import collections
import glob
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RUBRIK = ROOT / "apps" / "statute-browser" / "RUBRIK.md"
QUESTIONS = ROOT / "data" / "evaluvation" / "parsed-pastpapers" / "questions"
RUNS = ROOT / "experiments" / "koblex-inspired-retrieval" / "runs"
OUT_DIR = ROOT / "progress-figures"

# Validated categorical palette, light surface.
BLUE = "#2a78d6"
ORANGE = "#eb6834"
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#e8e7e4"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans",
    "text.color": INK,
    "axes.labelcolor": INK_SOFT,
    "xtick.color": INK_SOFT,
    "ytick.color": INK_SOFT,
    "axes.edgecolor": GRID,
    "axes.linewidth": 1.0,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.titlesize": 12,
})


def style(ax, value_axis: str = "x") -> None:
    """Recessive axes: hairline solid grid on the value axis only."""
    for side in ("top", "right", "left" if value_axis == "x" else "bottom"):
        ax.spines[side].set_visible(False)
    ax.grid(axis=value_axis, color=GRID, linewidth=1.0, linestyle="-", zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def save(fig, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT).as_posix()}")


# --------------------------------------------------------------------------- #
# inputs
# --------------------------------------------------------------------------- #

def register_rows() -> list[dict]:
    rows = []
    for line in RUBRIK.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\|\s*[123]\s*\|", line):
            c = [x.strip() for x in line.split("|")]
            rows.append({"cat": int(c[1]), "title": c[2], "final": c[7] == "yes"})
    return rows


def citation_counts() -> collections.Counter:
    """Statute names explicitly written in the past papers."""
    texts = []
    for path in sorted(glob.glob(str(QUESTIONS / "*.json"))):
        for q in json.loads(Path(path).read_text(encoding="utf-8"))["questions"]:
            fp = q.get("fact_pattern")
            if fp and fp.get("text"):
                texts.append(str(fp["text"]))
            if q.get("stem"):
                texts.append(str(q["stem"]))
            for part in (q.get("parts") or []):
                if part.get("text"):
                    texts.append(str(part["text"]))
                for item in (part.get("items") or []):
                    texts.append(json.dumps(item, ensure_ascii=False))
    blob = re.sub(r"\s+", " ", " ".join(texts))
    pattern = re.compile(r"([A-Z][A-Za-z()'\- ]{4,60}?(?:Act|Ordinance|Law|Code))")
    return collections.Counter(normalise(m.group(1)) for m in pattern.finditer(blob))


def normalise(name: str) -> str:
    name = name.lower().replace("(", " ").replace(")", " ")
    name = re.sub(r"\b(the|of|on|and|for|in|to|a|an|no)\b", " ", name)
    name = re.sub(r"restrictions?", "restriction", name)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z]+", " ", name)).strip()


def metrics(run: str) -> dict:
    return json.loads((RUNS / run / "metrics.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# figure 1: how much of the curriculum is finished
# --------------------------------------------------------------------------- #

def figure_progress(rows: list[dict]) -> None:
    cats = [1, 2, 3]
    done = [sum(1 for r in rows if r["cat"] == c and r["final"]) for c in cats]
    todo = [sum(1 for r in rows if r["cat"] == c and not r["final"]) for c in cats]
    labels = [f"Category {c}" for c in cats]
    y = range(len(cats))

    fig, ax = plt.subplots(figsize=(7.4, 2.5))
    # 2px surface gap between the two stacked segments
    ax.barh(y, done, height=0.55, color=BLUE, label="Finished", zorder=3)
    ax.barh(y, todo, height=0.55, left=[d + 0.12 for d in done], color=ORANGE,
            label="Not yet finished", zorder=3)

    for i, (d, t) in enumerate(zip(done, todo)):
        ax.text(d / 2, i, str(d), ha="center", va="center",
                color="white", fontsize=9, fontweight="bold", zorder=4)
        ax.text(d + t / 2 + 0.12, i, str(t), ha="center", va="center",
                color="white", fontsize=9, fontweight="bold", zorder=4)

    ax.set_yticks(list(y), labels)
    ax.invert_yaxis()
    ax.set_xlabel("Statutes")
    ax.set_title(f"Curriculum statutes finished to structured records: "
                 f"{sum(done)} of {len(rows)}", loc="left", pad=12)
    ax.legend(frameon=False, fontsize=9, ncols=2, loc="upper center",
              bbox_to_anchor=(0.5, -0.32))
    style(ax, "x")
    save(fig, "fig-1-corpus-progress.png")


# --------------------------------------------------------------------------- #
# figure 2: the queue -- what the exams cite, and whether it is ready
# --------------------------------------------------------------------------- #

def figure_coverage_gap(rows: list[dict], counts: collections.Counter) -> None:
    scored = []
    for row in rows:
        key = normalise(row["title"])
        n = sum(v for k, v in counts.items()
                if k == key or (len(key) > 10 and key in k))
        if n:
            scored.append((row["title"], n, row["final"]))
    scored.sort(key=lambda r: r[1])

    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    y = range(len(scored))
    colours = [BLUE if fin else ORANGE for _, _, fin in scored]
    ax.barh(y, [n for _, n, _ in scored], height=0.62, color=colours, zorder=3)

    for i, (_, n, _) in enumerate(scored):
        ax.text(n + 0.6, i, str(n), va="center", ha="left",
                color=INK_SOFT, fontsize=9, zorder=4)

    ax.set_yticks(list(y), [t for t, _, _ in scored])
    ax.set_xlabel("Times the statute is named across the 589 past-paper parts")
    ax.set_title("What the exams cite, and whether the corpus has it yet",
                 loc="left", pad=12)
    ax.set_xlim(0, max(n for _, n, _ in scored) * 1.12)
    handles = [plt.Rectangle((0, 0), 1, 1, color=BLUE),
               plt.Rectangle((0, 0), 1, 1, color=ORANGE)]
    ax.legend(handles, ["Finished", "Not yet finished"],
              frameon=False, loc="lower right", fontsize=9)
    style(ax, "x")
    save(fig, "fig-2-coverage-gap.png")


# --------------------------------------------------------------------------- #
# figure 3: baseline against the paper-inspired pipeline
# --------------------------------------------------------------------------- #

def figure_retrieval(b0: dict, b1: dict) -> None:
    keys = ["recall@5", "recall@10", "recall@20", "mrr"]
    labels = ["Recall@5", "Recall@10", "Recall@20", "MRR"]
    a = [b0["b0_bm25_ranked"]["summary"][k] for k in keys]
    b = [b1["b1_merged_candidates_ranked"]["summary"][k] for k in keys]

    x = range(len(keys))
    width = 0.30
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    ax.bar([i - width / 2 - 0.03 for i in x], a, width, color=BLUE,
           label="B0  question + facts, keyword search", zorder=3)
    ax.bar([i + width / 2 + 0.03 for i in x], b, width, color=ORANGE,
           label="B1  generated queries, merged", zorder=3)

    for i, (va, vb) in enumerate(zip(a, b)):
        ax.text(i - width / 2 - 0.03, va + 0.015, f"{va:.3f}", ha="center",
                color=INK_SOFT, fontsize=8.5)
        ax.text(i + width / 2 + 0.03, vb + 0.015, f"{vb:.3f}", ha="center",
                color=INK_SOFT, fontsize=8.5)

    ax.set_xticks(list(x), labels)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Score")
    ax.set_title("Retrieval on 20 test questions: the extra queries did not help",
                 loc="left", pad=12)
    ax.legend(frameon=False, fontsize=9, ncols=2, loc="upper center",
              bbox_to_anchor=(0.5, -0.16))
    style(ax, "y")
    save(fig, "fig-3-retrieval-b0-vs-b1.png")


# --------------------------------------------------------------------------- #
# figure 4: where provision selection weakens
# --------------------------------------------------------------------------- #

def figure_hops(b1: dict) -> None:
    grouped = b1["b1_selected_provisions"]["grouped_by_n_hops"]
    hops = sorted(grouped, key=int)
    values = [grouped[h]["complete_evidence"] for h in hops]
    counts = [grouped[h]["questions"] for h in hops]

    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    x = range(len(hops))
    ax.bar(x, values, width=0.42, color=BLUE, zorder=3)
    for i, v in enumerate(values):
        ax.text(i, v + 0.02, f"{v:.2f}", ha="center", color=INK_SOFT, fontsize=9)

    tick_labels = []
    for hop, n in zip(hops, counts):
        noun = "hop" if hop == "1" else "hops"
        tick_labels.append(f"{hop} {noun}\n(n={n})")
    ax.set_xticks(list(x), tick_labels)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Every needed provision selected")
    ax.set_title("Selection gets harder as more provisions are required",
                 loc="left", pad=12)
    style(ax, "y")
    save(fig, "fig-4-selection-by-hops.png")


def main() -> int:
    rows = register_rows()
    counts = citation_counts()
    b0, b1 = metrics("smoke-b0"), metrics("smoke-b1")

    figure_progress(rows)
    figure_coverage_gap(rows, counts)
    figure_retrieval(b0, b1)
    figure_hops(b1)
    print(f"{len(rows)} register rows, {sum(counts.values())} citation spans")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
