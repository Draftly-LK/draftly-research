"""Charts for the benchmark notebook.

Design rules applied here, so the notebook cells stay short:

  * Form follows the data's job. Magnitude jobs get ONE sequential hue; identity
    jobs get the fixed categorical order; state gets the reserved status palette.
  * The categorical set is capped at FOUR hues. Five failed the all-pairs
    normal-vision separation check (magenta vs orange, dE 12.9), so a fifth series
    folds into "other" or becomes a small multiple rather than a generated hue.
  * Never a dual axis. Two measures of different scale become two charts.
  * A legend whenever there are two or more series, plus direct labels at four or
    fewer, so identity is never carried by colour alone.
  * Aqua sits below 3:1 against the surface, so every chart using it also carries
    visible labels or a table view.
  * Recessive grid, thin marks, 2px gaps between stacked segments.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

# ── palette (validated; see module docstring) ────────────────────────────────
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"]  # blue, orange, aqua, violet
SEQ_HUE = "#2a78d6"
SEQ_STEPS = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#1c5cab", "#104281"]
STATUS = {
    "correct": "#0ca30c",
    "wrong": "#d03b3b",
    "missing": "#fab219",
    "no_label": "#c3c2b7",
    "unlabelled_extra": "#ec835a",
    "ambiguous": "#898781",
}
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"


def use_style() -> None:
    """Recessive chrome, so the data is the only thing that shouts."""
    mpl.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": BASELINE,
            "axes.labelcolor": INK_2,
            "axes.titlecolor": INK,
            "axes.titlesize": 12,
            "axes.titleweight": "600",
            "axes.titlelocation": "left",
            "axes.titlepad": 12,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.frameon": False,
            "legend.fontsize": 9,
            "lines.linewidth": 2.0,
            "lines.markersize": 8,
            "font.size": 10,
        }
    )


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.0%}"


def _note(ax: plt.Axes, text: str) -> None:
    """State an absence honestly instead of drawing an empty chart."""
    ax.text(0.5, 0.5, text, ha="center", va="center", color=MUTED, fontsize=10,
            transform=ax.transAxes, wrap=True)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)


# ── V1 dataset overview ──────────────────────────────────────────────────────
def dataset_pages(ax: plt.Axes, docs: Sequence[tuple[str, int, str]]) -> None:
    """Pages per document, coloured by language group. Identity job, <=4 hues."""
    if not docs:
        _note(ax, "no documents found")
        return
    langs = sorted({d[2] for d in docs})[:4]
    colours = {lang: SERIES[i] for i, lang in enumerate(langs)}
    names = [d[0] for d in docs]
    y = np.arange(len(docs))
    for i, (name, pages, lang) in enumerate(docs):
        ax.barh(y[i], pages, color=colours.get(lang, MUTED), height=0.62)
        ax.text(pages + 0.2, y[i], str(pages), va="center", color=INK_2, fontsize=9)
    ax.set_yticks(y, names, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("pages")
    ax.set_title(f"Benchmark bundle — {sum(d[1] for d in docs)} pages across {len(docs)} documents")
    handles = [mpl.patches.Patch(color=colours[l], label=l) for l in langs]
    ax.legend(handles=handles, loc="lower right", title="language")
    ax.grid(axis="y", visible=False)


# ── V2 headline accuracy ─────────────────────────────────────────────────────
def critical_accuracy(ax: plt.Axes, metrics: Mapping[str, dict]) -> None:
    """The headline. Magnitude job, so ONE hue, sorted, with Wilson error bars."""
    rows = []
    for variant, m in metrics.items():
        crit = m.get("criticalFieldAccuracy", {})
        rows.append((variant, crit.get("exactMatch"), crit.get("correct", 0),
                     crit.get("scored", 0), crit.get("wilson95"), m.get("status")))
    rows.sort(key=lambda r: (-1 if r[1] is None else r[1]))
    y = np.arange(len(rows))
    for i, (variant, value, correct, scored, wilson, status) in enumerate(rows):
        if value is None:
            ax.barh(y[i], 0.0, color=MUTED, height=0.6)
            ax.text(0.01, y[i], f"  not run — {status}", va="center",
                    color=MUTED, fontsize=9)
            continue
        ax.barh(y[i], value, color=SEQ_HUE, height=0.6)
        if wilson:
            ax.plot([wilson[0], wilson[1]], [y[i], y[i]], color=INK_2, linewidth=1.4)
        ax.text(min(value + 0.02, 1.02), y[i], f"{value:.0%}  ({correct}/{scored})",
                va="center", color=INK_2, fontsize=9)
    ax.set_yticks(y, [r[0] for r in rows])
    ax.set_xlim(0, 1.18)
    ax.set_xticks(np.linspace(0, 1, 6), [f"{v:.0%}" for v in np.linspace(0, 1, 6)])
    ax.set_xlabel("critical-field exact match (95% Wilson interval)")
    ax.set_title("Critical-field exact-match accuracy — the primary metric")
    ax.grid(axis="y", visible=False)


# ── V3 field x run status heatmap ────────────────────────────────────────────
def field_status_heatmap(ax: plt.Axes, rows: Sequence[Mapping[str, Any]]) -> None:
    """Which fields fail where. State job, so the reserved status palette + legend."""
    if not rows:
        _note(ax, "no scored fields yet")
        return
    variants = sorted({r["variant_id"] for r in rows})
    keys = sorted({r["key"] for r in rows})
    order = list(STATUS)
    index = {name: i for i, name in enumerate(order)}
    grid = np.full((len(keys), len(variants)), np.nan)
    for row in rows:
        outcome = row["outcome"]
        if outcome in index:
            grid[keys.index(row["key"]), variants.index(row["variant_id"])] = index[outcome]

    cmap = mpl.colors.ListedColormap([STATUS[name] for name in order])
    cmap.set_bad(SURFACE)
    ax.imshow(grid, cmap=cmap, vmin=-0.5, vmax=len(order) - 0.5, aspect="auto",
              interpolation="nearest")
    ax.set_xticks(range(len(variants)), variants, rotation=45, ha="right")
    ax.set_yticks(range(len(keys)), keys, fontsize=7)
    # 2px surface gaps between cells.
    ax.set_xticks(np.arange(-0.5, len(variants), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(keys), 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="minor", length=0)
    ax.set_title("Per-field outcome by run")
    handles = [mpl.patches.Patch(color=STATUS[name], label=name.replace("_", " "))
               for name in order]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0))


# ── V4 CER/WER by language and text type ─────────────────────────────────────
def text_error_rates(ax: plt.Axes, metrics: Mapping[str, dict]) -> None:
    """CER/WER by bucket. Reports the absence of labels rather than faking a number."""
    buckets: dict[str, dict[str, float]] = {}
    for variant, m in metrics.items():
        text = m.get("textMetrics", {})
        if text.get("status") != "ok":
            continue
        for label, values in (text.get("byBucket") or {}).items():
            buckets.setdefault(label, {})[variant] = values["cer"]
    if not buckets:
        _note(
            ax,
            "No OCR ground truth yet.\n\n"
            "CER and WER by language and text type need human region transcripts.\n"
            "Drop annotation files under ocr-benchmark/labels/ocr-region/ and re-run\n"
            "score.py. Three hand-typed pages (Sinhala, English, Sinhala/Tamil) are\n"
            "enough to make this chart real.",
        )
        ax.set_title("Character error rate by language and text type — not yet measurable")
        return

    labels = sorted(buckets)
    variants = sorted({v for b in buckets.values() for v in b})[:4]
    width = 0.8 / max(1, len(variants))
    x = np.arange(len(labels))
    for i, variant in enumerate(variants):
        values = [buckets[l].get(variant, np.nan) for l in labels]
        ax.bar(x + i * width, values, width * 0.9, label=variant, color=SERIES[i])
    ax.set_xticks(x + width * (len(variants) - 1) / 2, labels, rotation=30, ha="right")
    ax.set_ylabel("CER (lower is better)")
    ax.set_title("Character error rate by language and text type")
    ax.legend()


# ── V5 DPI ablation ──────────────────────────────────────────────────────────
def dpi_ablation(ax: plt.Axes, metrics: Mapping[str, dict], baseline_dpi: int = 200) -> None:
    """One line per run family, single y-axis, direct-labelled ends."""
    families: dict[str, list[tuple[int, float]]] = {}
    for variant, m in metrics.items():
        if "@dpi=" not in variant:
            continue
        family, _, value = variant.partition("@dpi=")
        accuracy = m.get("criticalFieldAccuracy", {}).get("exactMatch")
        if accuracy is not None:
            families.setdefault(family, []).append((int(value), accuracy))
    # Fold in the un-ablated run at the baseline DPI so the grid has an anchor.
    for variant, m in metrics.items():
        if "@" in variant:
            continue
        accuracy = m.get("criticalFieldAccuracy", {}).get("exactMatch")
        if accuracy is not None and variant in families:
            families[variant].append((baseline_dpi, accuracy))
    if not families:
        _note(ax, "no DPI ablation runs yet\n\nrunner.py A --ablation dpi")
        ax.set_title("Render DPI vs critical-field accuracy")
        return

    for i, (family, points) in enumerate(sorted(families.items())[:4]):
        points.sort()
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax.plot(xs, ys, marker="o", color=SERIES[i], label=family)
        ax.text(xs[-1] + 6, ys[-1], family, color=SERIES[i], fontsize=9, va="center")
    ax.axvline(baseline_dpi, color=BASELINE, linewidth=1.2, linestyle="--")
    ax.text(baseline_dpi + 4, ax.get_ylim()[0], " production", color=MUTED, fontsize=8)
    ax.set_xlabel("render DPI")
    ax.set_ylabel("critical-field exact match")
    ax.set_title("Render DPI vs accuracy — 200 DPI is what production ships")
    ax.legend(loc="lower right")


# ── V6 preprocessing ablation ────────────────────────────────────────────────
def preprocessing_ablation(ax: plt.Axes, metrics: Mapping[str, dict]) -> None:
    """Ordered stages, so one hue stepped light to dark rather than four colours."""
    order = ["original", "rotated", "deskew", "full"]
    points: list[tuple[str, float]] = []
    for variant, m in metrics.items():
        if "@variant=" not in variant:
            continue
        _, _, name = variant.partition("@variant=")
        accuracy = m.get("criticalFieldAccuracy", {}).get("exactMatch")
        if accuracy is not None:
            points.append((name, accuracy))
    if not points:
        _note(ax, "no preprocessing ablation yet\n\nrunner.py B --ablation variant")
        ax.set_title("Preprocessing stage vs accuracy")
        return
    points.sort(key=lambda p: order.index(p[0]) if p[0] in order else 99)
    steps = [SEQ_STEPS[1], SEQ_STEPS[3], SEQ_STEPS[4], SEQ_STEPS[6]]
    x = np.arange(len(points))
    for i, (name, value) in enumerate(points):
        ax.bar(x[i], value, 0.6, color=steps[min(i, len(steps) - 1)])
        ax.text(x[i], value + 0.01, f"{value:.0%}", ha="center", color=INK_2, fontsize=9)
    ax.set_xticks(x, [p[0] for p in points])
    ax.set_ylabel("critical-field exact match")
    ax.set_title("Does preprocessing actually help?")


# ── V7 cross-run agreement ───────────────────────────────────────────────────
def agreement_matrix(ax: plt.Axes, matrix: Mapping[str, Mapping[str, Any]]) -> None:
    """Works with zero ground truth. Magnitude job, so one sequential hue."""
    variants = sorted(matrix)
    if len(variants) < 2:
        _note(ax, "needs at least two completed runs to compare")
        ax.set_title("Cross-run field agreement")
        return
    grid = np.full((len(variants), len(variants)), np.nan)
    for i, left in enumerate(variants):
        for j, right in enumerate(variants):
            cell = matrix[left].get(right)
            if isinstance(cell, dict):
                grid[i, j] = cell["agreement"]
    cmap = mpl.colors.LinearSegmentedColormap.from_list("seq", [SEQ_STEPS[0], SEQ_STEPS[6]])
    cmap.set_bad(SURFACE)
    ax.imshow(grid, cmap=cmap, vmin=0, vmax=1, aspect="auto", interpolation="nearest")
    for i in range(len(variants)):
        for j in range(len(variants)):
            if not np.isnan(grid[i, j]):
                ax.text(j, i, f"{grid[i, j]:.0%}", ha="center", va="center",
                        fontsize=8, color=INK if grid[i, j] < 0.6 else SURFACE)
    ax.set_xticks(range(len(variants)), variants, rotation=45, ha="right")
    ax.set_yticks(range(len(variants)), variants)
    ax.set_xticks(np.arange(-0.5, len(variants), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(variants), 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="minor", length=0)
    ax.set_title("Cross-run agreement — the signal available with no ground truth")


def agreement_vs_truth(ax: plt.Axes, tally: Mapping[str, int]) -> None:
    """Is agreement a usable proxy for correctness? Part-to-whole, so stacked."""
    if not tally:
        _note(ax, "needs at least two runs over labelled fields")
        ax.set_title("Is agreement a usable proxy for correctness?")
        return
    order = ["all_correct", "disagree_some_correct", "agree_but_split", "all_wrong"]
    colours = {"all_correct": STATUS["correct"], "disagree_some_correct": SERIES[0],
               "agree_but_split": STATUS["missing"], "all_wrong": STATUS["wrong"]}
    left = 0.0
    total = sum(tally.values()) or 1
    for name in order:
        value = tally.get(name, 0)
        if not value:
            continue
        ax.barh(0, value, left=left, color=colours[name], height=0.5,
                label=name.replace("_", " "))
        if value / total > 0.06:
            ax.text(left + value / 2, 0, str(value), ha="center", va="center",
                    color=SURFACE, fontsize=9)
        left += value
    ax.set_yticks([])
    ax.set_xlabel("labelled fields compared across runs")
    ax.set_title("Is agreement a usable proxy for correctness?")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.35), ncol=4)
    ax.grid(axis="y", visible=False)


# ── V8 invented and omitted ──────────────────────────────────────────────────
def risk_rates(ax: plt.Axes, metrics: Mapping[str, dict]) -> None:
    """Invented vs omitted. Two measures on one 0-1 scale, so grouped not dual-axis."""
    rows = [
        (v, m.get("inventedValueRate"), m.get("omissionRate"))
        for v, m in metrics.items()
        if m.get("inventedValueRate") is not None or m.get("omissionRate") is not None
    ]
    if not rows:
        _note(ax, "no completed runs yet")
        ax.set_title("Invented-value and omission rates")
        return
    rows.sort(key=lambda r: (r[1] or 0))
    x = np.arange(len(rows))
    ax.bar(x - 0.2, [r[1] or 0 for r in rows], 0.36, color=STATUS["wrong"],
           label="invented value")
    ax.bar(x + 0.2, [r[2] or 0 for r in rows], 0.36, color=STATUS["missing"],
           label="omitted")
    ax.set_xticks(x, [r[0] for r in rows], rotation=45, ha="right")
    ax.set_ylabel("rate")
    ax.set_title("Invented values are worse than omissions — a lawyer can see a gap")
    ax.legend()


# ── V9 provenance ────────────────────────────────────────────────────────────
def provenance_mix(ax: plt.Axes, metrics: Mapping[str, dict]) -> None:
    """Part-to-whole over ordered levels, so one hue stepped, 2px gaps."""
    levels = ["region", "page", "none"]
    steps = {"region": SEQ_STEPS[6], "page": SEQ_STEPS[3], "none": SEQ_STEPS[0]}
    rows = [(v, m.get("provenance", {})) for v, m in metrics.items() if m.get("provenance")]
    if not rows:
        _note(ax, "no provenance recorded yet")
        ax.set_title("Where did each value come from?")
        return
    y = np.arange(len(rows))
    for i, (variant, mix) in enumerate(rows):
        total = sum(mix.values()) or 1
        left = 0.0
        for level in levels:
            share = mix.get(level, 0) / total
            if share <= 0:
                continue
            ax.barh(y[i], share, left=left, height=0.6, color=steps[level],
                    edgecolor=SURFACE, linewidth=2)
            if share > 0.08:
                ax.text(left + share / 2, y[i], f"{share:.0%}", ha="center", va="center",
                        fontsize=8, color=SURFACE if level == "region" else INK)
            left += share
    ax.set_yticks(y, [r[0] for r in rows])
    ax.set_xlim(0, 1)
    ax.set_xlabel("share of extracted values")
    ax.set_title("Provenance level — region beats page, page beats nothing")
    handles = [mpl.patches.Patch(color=steps[l], label=l) for l in levels]
    ax.legend(handles=handles, loc="lower right")
    ax.grid(axis="y", visible=False)


# ── V10 cost vs accuracy ─────────────────────────────────────────────────────
def cost_vs_accuracy(ax: plt.Axes, metrics: Mapping[str, dict]) -> None:
    """Scatter caps at one hue plus direct labels, per the all-pairs limit."""
    points = []
    for variant, m in metrics.items():
        accuracy = m.get("criticalFieldAccuracy", {}).get("exactMatch")
        cost = m.get("cost", {})
        pages = m.get("pages") or 1
        if accuracy is None or not cost.get("estimatedUsd"):
            continue
        points.append((variant, cost["estimatedUsd"] / pages, accuracy,
                       cost.get("latencyMsTotal", 0) / pages))
    if not points:
        _note(ax, "no cost recorded yet — needs a run against a live provider")
        ax.set_title("Cost per page vs accuracy")
        return
    sizes = [max(60, min(600, p[3] / 8)) for p in points]
    ax.scatter([p[1] for p in points], [p[2] for p in points], s=sizes,
               color=SEQ_HUE, alpha=0.85, edgecolor=SURFACE, linewidth=2)
    for variant, cost, accuracy, _latency in points:
        ax.annotate(variant, (cost, accuracy), textcoords="offset points",
                    xytext=(10, 4), fontsize=9, color=INK_2)
    ax.set_xlabel("estimated USD per page")
    ax.set_ylabel("critical-field exact match")
    ax.set_title("Cost per page vs accuracy — bubble size is latency per page")


# ── V11 latency by stage ─────────────────────────────────────────────────────
def latency_by_run(ax: plt.Axes, metrics: Mapping[str, dict]) -> None:
    rows = [
        (v, (m.get("cost", {}).get("latencyMsTotal", 0) or 0) / (m.get("pages") or 1))
        for v, m in metrics.items()
        if m.get("cost", {}).get("latencyMsTotal")
    ]
    if not rows:
        _note(ax, "no latency recorded yet")
        ax.set_title("Latency per page")
        return
    rows.sort(key=lambda r: r[1])
    y = np.arange(len(rows))
    for i, (variant, ms) in enumerate(rows):
        ax.barh(y[i], ms / 1000, height=0.6, color=SEQ_HUE)
        ax.text(ms / 1000 + 0.1, y[i], f"{ms/1000:.1f}s", va="center",
                color=INK_2, fontsize=9)
    ax.set_yticks(y, [r[0] for r in rows])
    ax.set_xlabel("seconds per page")
    ax.set_title("Latency per page")
    ax.grid(axis="y", visible=False)


# ── V12 provenance overlay preview ───────────────────────────────────────────
def overlay_boxes(ax: plt.Axes, image, fields: Iterable[Mapping[str, Any]],
                  title: str = "") -> None:
    """Draw predicted field boxes on a rendered page.

    Renders CLIENT CONTENT. Only ever run locally, and clear notebook outputs
    before committing.
    """
    ax.imshow(image, cmap="gray")
    width, height = image.size
    for field in fields:
        bbox = field.get("bbox")
        if not bbox:
            continue
        x0, y0, x1, y1 = (bbox[0] * width, bbox[1] * height, bbox[2] * width, bbox[3] * height)
        good = field.get("box_contains_value") is True
        ax.add_patch(
            mpl.patches.Rectangle(
                (x0, y0), x1 - x0, y1 - y0, fill=False, linewidth=2,
                edgecolor=STATUS["correct"] if good else STATUS["wrong"],
            )
        )
        ax.text(x0, y0 - 6, field.get("key", ""), fontsize=7,
                color=STATUS["correct"] if good else STATUS["wrong"])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.set_title(title or "predicted field boxes (green = box contains the value)")
