"""EDA figures for document classification over the CommonLII judgment corpus.

Two label sets live in this corpus and both are "classification" in a different
sense, so both are plotted:

  * layout class -- `category` / `bucket` on the parsed judgments (which HTML
    layout family a case belongs to; drives which parser branch runs).
  * conveyancing gate verdict -- `verdict` in
    evaluation/runs/conveyancing-gate-v2/conveyancing_labels.csv
    (required / review / not-required, the in-scope decision).

Everything here is read-only: it reads the parsed CSVs plus the gate labels and
writes PNGs next to this script with the numbers behind each figure in
`tables/`. No model calls, no spend, nothing written back into data/.

Usage:
    uv run python scripts/classify-figures/make_classify_figures.py
    uv run python scripts/classify-figures/make_classify_figures.py --out /tmp/figs

Every label in these figures is status=unverified -- the gate is a deterministic
scorer, not a lawyer sign-off.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[2]
COURTS = ["LKCA", "LKSC"]
COURT_LABEL = {"LKCA": "Court of Appeal (LKCA)", "LKSC": "Supreme Court (LKSC)"}
GATE_LABELS = ROOT / "evaluation" / "runs" / "conveyancing-gate-v2" / "conveyancing_labels.csv"
OUT_DIR = Path(__file__).resolve().parent

# Categorical slots 1-4 of the validated default palette, in fixed order.
# Validated light-mode, adjacent pairlist: worst CVD dE 9.1, normal-vision 22.9.
# Two slots sit below 3:1 on the surface, so every bar carries a visible value
# label and every figure ships a CSV table -- the documented relief rule.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#8a8981"
GRID = "#e4e3dd"
SURFACE = "#fcfcfb"
SEQ = LinearSegmentedColormap.from_list("seq_blue", ["#f2f6fc", "#2a78d6", "#123a6b"])

# Fixed display order so a colour never moves between figures.
LAYOUT_ORDER = ["dense_br_nlr", "paragraph_nlr", "structured_slr", "late_slr_font"]
LAYOUT_COLOR = dict(zip(LAYOUT_ORDER, SERIES))
VERDICT_ORDER = ["required", "review", "not-required"]
VERDICT_COLOR = {"required": SERIES[0], "review": SERIES[3], "not-required": MUTED}

# A decade with fewer than this many judgments is too thin to plot as a share.
MIN_DECADE_N = 25


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------


def load_judgments() -> pd.DataFrame:
    frames = []
    for court in COURTS:
        path = ROOT / "data" / "commonlii" / "parsed" / court / "judgments.csv"
        if not path.exists():
            raise SystemExit(f"missing parsed judgments: {path}")
        frame = pd.read_csv(path, low_memory=False)
        frame["court"] = court
        frames.append(frame)
    judgments = pd.concat(frames, ignore_index=True)
    judgments["reported_year"] = pd.to_numeric(judgments["reported_year"], errors="coerce")
    judgments["decade"] = (judgments["reported_year"] // 10 * 10).astype("Int64")
    return judgments


def load_gate() -> pd.DataFrame | None:
    if not GATE_LABELS.exists():
        return None
    gate = pd.read_csv(GATE_LABELS, low_memory=False)
    gate["reported_year"] = pd.to_numeric(gate["reported_year"], errors="coerce")
    gate["decade"] = (gate["reported_year"] // 10 * 10).astype("Int64")
    return gate


# --------------------------------------------------------------------------
# shared chart furniture
# --------------------------------------------------------------------------


def new_fig(width: float, height: float):
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    return fig, ax


def dress(ax, title: str, subtitle: str = "", xlabel: str = "", ylabel: str = "") -> None:
    ax.set_title(title, loc="left", fontsize=13, color=INK, pad=18 if subtitle else 10)
    if subtitle:
        ax.text(
            0.0,
            1.02,
            subtitle,
            transform=ax.transAxes,
            fontsize=9.5,
            color=INK_2,
            va="bottom",
        )
    ax.set_xlabel(xlabel, fontsize=10, color=INK_2)
    ax.set_ylabel(ylabel, fontsize=10, color=INK_2)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=9, length=3, color=GRID)


def save(fig, out_dir: Path, name: str, table: pd.DataFrame | None = None) -> None:
    fig.tight_layout()
    png = out_dir / f"{name}.png"
    fig.savefig(png, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    line = f"  wrote {png.name}"
    if table is not None:
        tables = out_dir / "tables"
        tables.mkdir(exist_ok=True)
        table.to_csv(tables / f"{name}.csv", index=False)
        line += f" + tables/{name}.csv"
    print(line)


def pretty(label: str) -> str:
    return str(label).replace("_", " ")


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------


def fig_class_balance(judgments: pd.DataFrame, out: Path) -> None:
    """How lopsided the layout classes are, per court."""
    counts = (
        judgments.pivot_table(index="category", columns="court", values="case_id", aggfunc="count")
        .reindex(LAYOUT_ORDER)
        .fillna(0)
    )
    fig, ax = new_fig(9, 5)
    y = np.arange(len(counts.index))
    height = 0.36
    for offset, (court, colour) in zip((height / 2, -height / 2), zip(COURTS, (SERIES[0], SERIES[2]))):
        values = counts[court].to_numpy()
        ax.barh(y + offset, values, height=height - 0.02, color=colour, label=COURT_LABEL[court])
        for yi, value in zip(y + offset, values):
            ax.text(value + 40, yi, f"{int(value):,}", va="center", fontsize=8.5, color=INK_2)
    ax.set_yticks(y, [pretty(c) for c in counts.index])
    ax.invert_yaxis()
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    total = int(counts.to_numpy().sum())
    share = counts.sum(axis=1) / total * 100
    dress(
        ax,
        "One layout class holds most of the corpus",
        f"{total:,} parsed judgments; {share.iloc[0]:.0f}% fall in {pretty(counts.index[0])} alone",
        xlabel="judgments",
    )
    ax.legend(frameon=False, fontsize=9, labelcolor=INK_2, loc="lower right")
    save(fig, out, "01-layout-class-balance", counts.reset_index())


def fig_class_over_time(judgments: pd.DataFrame, out: Path) -> None:
    """Layout class is largely a function of report era -- the leakage risk."""
    frame = judgments.dropna(subset=["reported_year"])
    shares = (
        frame.pivot_table(index="decade", columns="category", values="case_id", aggfunc="count")
        .reindex(columns=LAYOUT_ORDER)
        .fillna(0)
    )
    volume = shares.sum(axis=1)
    # The 1870s hold only a handful of cases; a share on n<MIN_DECADE_N is noise.
    keep = volume >= MIN_DECADE_N
    dropped = volume[~keep]
    if len(dropped):
        print(
            "  note: dropped thin decades from the share panel: "
            + ", ".join(f"{int(d)}s (n={int(v)})" for d, v in dropped.items())
        )
    shares, volume = shares[keep], volume[keep]
    pct = shares.div(volume, axis=0) * 100

    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(10, 6.4), height_ratios=[3, 1], sharex=True
    )
    fig.patch.set_facecolor(SURFACE)
    for axis in (ax, ax2):
        axis.set_facecolor(SURFACE)
    x = pct.index.astype(int)
    ax.stackplot(
        x,
        [pct[c].to_numpy() for c in LAYOUT_ORDER],
        colors=[LAYOUT_COLOR[c] for c in LAYOUT_ORDER],
        edgecolor=SURFACE,
        linewidth=2,
    )
    ax.set_ylim(0, 100)
    ax.set_xlim(x.min(), x.max())
    dress(
        ax,
        "Layout class tracks the reporting era, not the case",
        "share of judgments per decade -- a year feature would leak the label",
        ylabel="% of decade",
    )
    ax.legend(
        handles=[Patch(facecolor=LAYOUT_COLOR[c], label=pretty(c)) for c in LAYOUT_ORDER],
        frameon=False,
        fontsize=9,
        labelcolor=INK_2,
        ncol=4,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.06),
    )
    ax2.bar(x, volume.to_numpy(), width=7, color=MUTED)
    ax2.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax2.set_axisbelow(True)
    dress(ax2, "", "", xlabel="decade reported", ylabel="judgments")
    save(fig, out, "02-layout-class-over-time", pct.round(2).reset_index())


def fig_confidence(judgments: pd.DataFrame, out: Path) -> None:
    """Where the layout scorer is unsure -- the review queue if you thresholded it."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharex=True)
    fig.patch.set_facecolor(SURFACE)
    # Almost all mass sits above 0.84, so the plotted window starts there and
    # everything below is folded into the leftmost bin (counted in the label).
    floor = 0.84
    bins = np.linspace(floor, float(judgments["confidence"].max()), 30)
    rows = []
    for axis, category in zip(axes.ravel(), LAYOUT_ORDER):
        subset = judgments.loc[judgments["category"] == category, "confidence"].dropna()
        axis.set_facecolor(SURFACE)
        axis.hist(
            subset.clip(lower=floor),
            bins=bins,
            color=LAYOUT_COLOR[category],
            edgecolor=SURFACE,
            linewidth=0.4,
        )
        axis.axvline(0.90, color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
        axis.set_yscale("log")
        axis.set_xlim(bins[0] - 0.002, bins[-1] + 0.002)
        low = float((subset < 0.90).mean() * 100)
        below_floor = int((subset < floor).sum())
        axis.text(
            0.02,
            0.94,
            f"{pretty(category)}  n={len(subset):,}\n"
            f"{low:.0f}% below 0.90 · {below_floor} below {floor:g} (folded left)",
            transform=axis.transAxes,
            fontsize=9,
            color=INK,
            va="top",
        )
        axis.yaxis.grid(True, color=GRID, linewidth=0.8)
        axis.set_axisbelow(True)
        dress(axis, "", "", xlabel="", ylabel="judgments")
        rows.append(
            {
                "category": category,
                "n": len(subset),
                "median_confidence": round(float(subset.median()), 4),
                "p05_confidence": round(float(subset.quantile(0.05)), 4),
                "pct_below_0.90": round(low, 2),
            }
        )
    for axis in axes[1]:
        axis.set_xlabel("layout classifier confidence", fontsize=10, color=INK_2)
    fig.suptitle(
        "Only paragraph nlr carries a real low-confidence tail",
        x=0.008,
        ha="left",
        fontsize=13,
        color=INK,
    )
    fig.text(
        0.008,
        0.925,
        "log counts; dashed line = 0.90 -- the mass left of it is what a review threshold would catch",
        fontsize=9.5,
        color=INK_2,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    save(fig, out, "03-layout-confidence", pd.DataFrame(rows))


def fig_field_completeness(judgments: pd.DataFrame, out: Path) -> None:
    """Which extracted fields are actually available as features, per class."""
    fields = [
        "case_name",
        "neutral_citation",
        "decision_date",
        "hearing_dates",
        "proceeding_type",
        "case_numbers",
        "originating_court",
        "parties",
        "bench",
        "opinion_author",
        "catchwords",
        "disposition",
        "costs_order",
    ]
    fields = [f for f in fields if f in judgments.columns]
    matrix = pd.DataFrame(
        {
            category: judgments.loc[judgments["category"] == category, fields].notna().mean() * 100
            for category in LAYOUT_ORDER
        }
    )
    matrix["all classes"] = judgments[fields].notna().mean() * 100

    fig, ax = new_fig(8.6, 6.2)
    data = matrix.to_numpy()
    ax.imshow(data, cmap=SEQ, vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(matrix.shape[1]), [pretty(c) for c in matrix.columns], rotation=20, ha="right")
    ax.set_yticks(range(len(fields)), [pretty(f) for f in fields])
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            value = data[i, j]
            ax.text(
                j,
                i,
                f"{value:.0f}",
                ha="center",
                va="center",
                fontsize=8.5,
                color="#ffffff" if value > 42 else INK,
            )
    ax.set_xticks(np.arange(-0.5, data.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, data.shape[0], 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)
    dress(
        ax,
        "Field availability differs sharply by layout class",
        "% of judgments with the field populated -- darker is more available",
    )
    for side in ("left", "bottom"):
        ax.spines[side].set_visible(False)
    save(fig, out, "04-field-completeness", matrix.round(1).rename_axis("field").reset_index())


def fig_length(judgments: pd.DataFrame, out: Path) -> None:
    """Document size: the cheapest feature, and how separable it is by class."""
    fig, ax = new_fig(9, 5)
    rows = []
    for i, category in enumerate(LAYOUT_ORDER):
        values = judgments.loc[judgments["category"] == category, "char_count"].dropna()
        values = values[values > 0]
        box = ax.boxplot(
            [values],
            positions=[i],
            widths=0.5,
            orientation="horizontal",
            patch_artist=True,
            showfliers=False,
            medianprops=dict(color=SURFACE, linewidth=2),
            whiskerprops=dict(color=MUTED, linewidth=1.2),
            capprops=dict(color=MUTED, linewidth=1.2),
        )
        box["boxes"][0].set(facecolor=LAYOUT_COLOR[category], edgecolor=SURFACE, linewidth=2)
        median = float(values.median())
        ax.text(median * 1.06, i - 0.32, f"median {median:,.0f} chars", fontsize=8.5, color=INK_2)
        rows.append(
            {
                "category": category,
                "n": len(values),
                "p25": int(values.quantile(0.25)),
                "median": int(median),
                "p75": int(values.quantile(0.75)),
                "p95": int(values.quantile(0.95)),
            }
        )
    ax.set_xscale("log")
    ax.set_yticks(range(len(LAYOUT_ORDER)), [pretty(c) for c in LAYOUT_ORDER])
    ax.invert_yaxis()
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    dress(
        ax,
        "SLR classes run ~1.6x longer, but the distributions overlap",
        "characters of extracted text, log scale, outliers hidden",
        xlabel="characters",
    )
    save(fig, out, "05-document-length", pd.DataFrame(rows))


def fig_damage(judgments: pd.DataFrame, out: Path) -> None:
    """Parser damage -- the label noise floor for anything read off body text."""
    flags = [
        ("has_encoding_errors", "encoding errors"),
        ("has_malformed_tags", "malformed tags"),
        ("has_page_missed", "page missed"),
    ]
    flags = [(c, label) for c, label in flags if c in judgments.columns]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.8), width_ratios=[1, 1.3])
    fig.patch.set_facecolor(SURFACE)
    for axis in (ax, ax2):
        axis.set_facecolor(SURFACE)

    x = np.arange(len(LAYOUT_ORDER))
    width = 0.26
    by_class = {}
    for i, (column, label) in enumerate(flags):
        rates = [
            judgments.loc[judgments["category"] == c, column].fillna(False).astype(bool).mean() * 100
            for c in LAYOUT_ORDER
        ]
        by_class[label] = rates
        offset = (i - (len(flags) - 1) / 2) * width
        ax.bar(x + offset, rates, width=width - 0.02, color=SERIES[i], label=label)
        for xi, value in zip(x + offset, rates):
            ax.text(xi, value + 1.2, f"{value:.0f}", ha="center", fontsize=8, color=INK_2)
    ax.set_xticks(x, [pretty(c) for c in LAYOUT_ORDER], rotation=18, ha="right")
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    dress(ax, "Damage rate by layout class", "% of judgments carrying each parser flag", ylabel="% of class")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK_2)

    frame = judgments.dropna(subset=["reported_year"])
    per_decade = frame["decade"].value_counts()
    frame = frame[frame["decade"].map(per_decade) >= MIN_DECADE_N]
    trend = frame.groupby("decade").apply(
        lambda g: pd.Series(
            {
                label: g[column].fillna(False).astype(bool).mean() * 100
                for column, label in flags
            }
        ),
        include_groups=False,
    )
    # Series identity comes from the shared legend on the left panel -- end labels
    # collide here because two flags sit on top of each other near 0%.
    for i, (_, label) in enumerate(flags):
        ax2.plot(trend.index.astype(int), trend[label], color=SERIES[i], linewidth=2, label=label)
        ax2.scatter([trend.index.astype(int)[-1]], [trend[label].iloc[-1]], s=28, color=SERIES[i], zorder=3)
    ax2.set_xlim(int(trend.index.min()), int(trend.index.max()) + 4)
    ax2.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax2.set_axisbelow(True)
    dress(
        ax2,
        "and by decade (same colours)",
        "no clean trend -- damage spikes in the 1940s and again in the 1990s",
        xlabel="decade reported",
        ylabel="% of decade",
    )

    table = pd.DataFrame(by_class, index=LAYOUT_ORDER).round(1).rename_axis("category").reset_index()
    save(fig, out, "06-parser-damage", table)


def fig_gate_verdicts(gate: pd.DataFrame, out: Path) -> None:
    """The gate's own class balance, and what actually decided each verdict."""
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 5), width_ratios=[1, 1.5])
    fig.patch.set_facecolor(SURFACE)
    for axis in (ax, ax2):
        axis.set_facecolor(SURFACE)

    counts = gate["verdict"].value_counts().reindex(VERDICT_ORDER).fillna(0)
    total = int(counts.sum())
    ax.bar(
        range(len(counts)),
        counts.to_numpy(),
        width=0.6,
        color=[VERDICT_COLOR[v] for v in counts.index],
    )
    for i, value in enumerate(counts.to_numpy()):
        ax.text(
            i,
            value + total * 0.012,
            f"{int(value):,}\n{value / total * 100:.0f}%",
            ha="center",
            fontsize=9,
            color=INK_2,
        )
    ax.set_xticks(range(len(counts)), list(counts.index))
    ax.set_ylim(0, counts.max() * 1.2)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    dress(ax, "Conveyancing gate verdicts", f"{total:,} judgments, all status=unverified", ylabel="judgments")

    # A blank decisive_signal means no rule fired at all; every such case is
    # not-required, so name it rather than showing an unexplained "(none)".
    signals = gate["decisive_signal"].fillna("(no rule fired)").value_counts().head(10).iloc[::-1]
    ax2.barh(range(len(signals)), signals.to_numpy(), height=0.62, color=SERIES[0])
    for i, value in enumerate(signals.to_numpy()):
        ax2.text(value + total * 0.004, i, f"{int(value):,}", va="center", fontsize=8.5, color=INK_2)
    ax2.set_yticks(range(len(signals)), [pretty(s) for s in signals.index])
    ax2.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax2.set_axisbelow(True)
    dress(
        ax2,
        "What decided the verdict",
        "top 10 signals; every '(no rule fired)' case is not-required",
        xlabel="judgments",
    )

    table = counts.rename("judgments").rename_axis("verdict").reset_index()
    save(fig, out, "07-gate-verdicts", table)


def fig_gate_scores(gate: pd.DataFrame, out: Path) -> None:
    """Score distribution per verdict -- how much of the corpus sits near a band edge."""
    fig, ax = new_fig(10, 5)
    bins = np.arange(gate["score"].min() - 0.5, gate["score"].max() + 1.5, 1)
    bottom = np.zeros(len(bins) - 1)
    rows = []
    for verdict in VERDICT_ORDER:
        values = gate.loc[gate["verdict"] == verdict, "score"].dropna()
        hist, _ = np.histogram(values, bins=bins)
        ax.bar(
            bins[:-1] + 0.5,
            hist,
            bottom=bottom,
            width=0.86,
            color=VERDICT_COLOR[verdict],
            label=verdict,
            edgecolor=SURFACE,
            linewidth=0.5,
        )
        bottom += hist
        rows.append(
            {
                "verdict": verdict,
                "n": len(values),
                "min": float(values.min()),
                "median": float(values.median()),
                "max": float(values.max()),
            }
        )
    ax.set_yscale("log")
    ax.set_xlim(bins[0], bins[-1])
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    dress(
        ax,
        "Most of the corpus scores zero; the informative cases are a long right tail",
        "deterministic gate score, judgments per integer score, log count",
        xlabel="gate score",
        ylabel="judgments (log)",
    )
    ax.legend(frameon=False, fontsize=9, labelcolor=INK_2, title=None)
    save(fig, out, "08-gate-score-distribution", pd.DataFrame(rows))


def fig_gate_features(gate: pd.DataFrame, out: Path) -> None:
    """Two structured features against the verdict: how separable the label is."""
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.4), width_ratios=[1.1, 1])
    fig.patch.set_facecolor(SURFACE)
    for axis in (ax, ax2):
        axis.set_facecolor(SURFACE)

    top = gate["proceeding_type"].fillna("(missing)").value_counts().head(9).index
    frame = gate.assign(pt=gate["proceeding_type"].fillna("(missing)"))
    frame = frame[frame["pt"].isin(top)]
    share = (
        frame.pivot_table(index="pt", columns="verdict", values="case_id", aggfunc="count")
        .reindex(columns=VERDICT_ORDER)
        .fillna(0)
    )
    n = share.sum(axis=1)
    pct = share.div(n, axis=0) * 100
    pct = pct.loc[pct["required"].sort_values().index]
    y = np.arange(len(pct))
    left = np.zeros(len(pct))
    for verdict in VERDICT_ORDER:
        values = pct[verdict].to_numpy()
        ax.barh(y, values, left=left, height=0.62, color=VERDICT_COLOR[verdict], edgecolor=SURFACE, linewidth=2)
        left += values
    ax.set_yticks(y, [f"{pretty(i)}  (n={int(n[i]):,})" for i in pct.index])
    ax.set_xlim(0, 100)
    dress(
        ax,
        "Proceeding type is a strong prior on the verdict",
        "verdict mix within each of the 9 most common proceeding types",
        xlabel="% of proceeding type",
    )
    ax.legend(
        handles=[Patch(facecolor=VERDICT_COLOR[v], label=v) for v in VERDICT_ORDER],
        frameon=False,
        fontsize=9,
        labelcolor=INK_2,
        ncol=3,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.13),
    )

    flags = gate.assign(
        catchwords=np.where(gate["has_catchwords"].fillna(False).astype(bool), "has catchwords", "no catchwords"),
        damaged=np.where(gate["text_damaged"].fillna(False).astype(bool), "text damaged", "text clean"),
    )
    flags["group"] = flags["catchwords"] + "\n" + flags["damaged"]
    groups = flags["group"].value_counts().index.tolist()
    grid = (
        flags.pivot_table(index="group", columns="verdict", values="case_id", aggfunc="count")
        .reindex(index=groups, columns=VERDICT_ORDER)
        .fillna(0)
    )
    grid_pct = grid.div(grid.sum(axis=1), axis=0) * 100
    ax2.imshow(grid_pct.to_numpy(), cmap=SEQ, vmin=0, vmax=100, aspect="auto")
    ax2.set_xticks(range(len(VERDICT_ORDER)), VERDICT_ORDER)
    ax2.set_yticks(range(len(groups)), groups, fontsize=8.5)
    for i in range(grid_pct.shape[0]):
        for j in range(grid_pct.shape[1]):
            value = grid_pct.to_numpy()[i, j]
            ax2.text(
                j,
                i,
                f"{value:.0f}%\nn={int(grid.to_numpy()[i, j]):,}",
                ha="center",
                va="center",
                fontsize=8,
                color="#ffffff" if value > 42 else INK,
            )
    ax2.set_xticks(np.arange(-0.5, len(VERDICT_ORDER), 1), minor=True)
    ax2.set_yticks(np.arange(-0.5, len(groups), 1), minor=True)
    ax2.grid(which="minor", color=SURFACE, linewidth=2)
    ax2.tick_params(which="minor", length=0)
    dress(
        ax2,
        "Damaged text doubles the review rate",
        "verdict mix per headnote/damage combination",
    )
    for side in ("left", "bottom"):
        ax2.spines[side].set_visible(False)

    table = pct.round(1).rename_axis("proceeding_type").reset_index()
    save(fig, out, "09-gate-feature-separability", table)


def fig_gate_over_time(gate: pd.DataFrame, out: Path) -> None:
    """Where the in-scope cases actually live in time -- sampling guidance."""
    frame = gate.dropna(subset=["reported_year"])
    counts = (
        frame.pivot_table(index="decade", columns="verdict", values="case_id", aggfunc="count")
        .reindex(columns=VERDICT_ORDER)
        .fillna(0)
    )
    # Drop the 1870s and 2010s stubs: a handful of cases each, invisible as bars,
    # and they only stretch the axis into empty gutters.
    volume = counts.sum(axis=1)
    dropped = volume[volume < MIN_DECADE_N]
    if len(dropped):
        print(
            "  note: dropped thin decades from the verdict timeline: "
            + ", ".join(f"{int(d)}s (n={int(v)})" for d, v in dropped.items())
        )
    counts = counts[volume >= MIN_DECADE_N]
    fig, ax = new_fig(10, 5)
    x = counts.index.astype(int)
    bottom = np.zeros(len(counts))
    for verdict in VERDICT_ORDER:
        values = counts[verdict].to_numpy()
        ax.bar(x, values, bottom=bottom, width=7, color=VERDICT_COLOR[verdict], label=verdict, edgecolor=SURFACE, linewidth=1.5)
        bottom += values
    rate = counts["required"] / counts.sum(axis=1) * 100
    # Thin decades (the 1870s and 2010s stubs) can win on rate off a handful of
    # cases, so the callout only considers decades with real volume.
    peak = rate.idxmax()
    # Tight to the decades that actually carry data, one tick per decade.
    ax.set_xlim(int(x.min()) - 6, int(x.max()) + 6)
    ax.set_xticks(np.arange(int(x.min()), int(x.max()) + 1, 10))
    ax.tick_params(axis="x", labelrotation=45, labelsize=8.5)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    dress(
        ax,
        "Conveyancing-relevant cases are spread across the whole century",
        f"verdict counts per decade reported; the required share peaks at "
        f"{rate.max():.0f}% in the {int(peak)}s",
        xlabel="decade reported",
        ylabel="judgments",
    )
    ax.legend(frameon=False, fontsize=9, labelcolor=INK_2, ncol=3)
    table = counts.astype(int).rename_axis("decade").reset_index()
    table["required_pct"] = rate.round(1).to_numpy()
    save(fig, out, "10-gate-verdicts-over-time", table)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="directory for the PNGs")
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update({"font.size": 10, "axes.titleweight": "regular"})

    judgments = load_judgments()
    print(f"loaded {len(judgments):,} parsed judgments from {', '.join(COURTS)}")
    fig_class_balance(judgments, out)
    fig_class_over_time(judgments, out)
    fig_confidence(judgments, out)
    fig_field_completeness(judgments, out)
    fig_length(judgments, out)
    fig_damage(judgments, out)

    gate = load_gate()
    if gate is None:
        print(f"skipped gate figures 07-10: {GATE_LABELS} not found")
        return
    print(f"loaded {len(gate):,} conveyancing gate labels (status=unverified)")
    fig_gate_verdicts(gate, out)
    fig_gate_scores(gate, out)
    fig_gate_features(gate, out)
    fig_gate_over_time(gate, out)


if __name__ == "__main__":
    main()
