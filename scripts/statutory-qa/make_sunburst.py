"""Sunburst of the gold set: inner ring = statutes carrying an indispensable
provision, outer ring = the sections themselves. Wedge size = number of gold
questions whose indispensable set contains that section (a question with two
sections in one Act counts twice in that Act, once per section).

Reads benchmark/private-gold.jsonl and corpus/sections.jsonl; writes
experiments/figures/gold-sunburst.{pdf,png} and copies the PDF to
research-paper/figures/.

    uv run python scripts/statutory-qa/make_sunburst.py [--top-acts 8] [--set main|extended]
"""

from __future__ import annotations

import argparse
import collections
import colorsys
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import to_rgb  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sq_common as C  # noqa: E402

# Validated categorical palette (light surface), fixed order.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
OTHER = "#9a9891"
SHORT = {
    "Notaries Ordinance": "Notaries Ord.",
    "Matrimonial Rights and Inheritance Ordinance": "Matrimonial Rights & Inheritance Ord.",
    "Prevention of Frauds Ordinance": "Prevention of Frauds Ord.",
    "Registration of Documents Ordinance": "Registration of Documents Ord.",
    "Land (Restrictions on Alienation) Act": "Land (Restrictions on Alienation) Act",
    "Registration of Title Act": "Registration of Title Act",
    "Western Province Financial Statute": "WP Financial Statute",
    "Powers of Attorney Ordinance": "Powers of Attorney Ord.",
}


def tint(hex_color: str, i: int, n: int) -> tuple:
    """Lighter steps of one hue for the outer ring (sequential within an Act)."""
    r, g, b = to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    lo, hi = 0.42, 0.78
    lum = lo + (hi - lo) * (i / max(1, n - 1)) if n > 1 else 0.55
    return colorsys.hls_to_rgb(h, lum, max(0.35, s * 0.9))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-acts", type=int, default=8)
    ap.add_argument("--set", dest="gold_set", choices=["main", "extended"], default="main")
    args = ap.parse_args(argv)

    gold = C.read_jsonl(C.BENCHMARK_DIR / ("private-gold.jsonl" if args.gold_set == "main" else "private-gold-extended.jsonl"))
    secs = {s["section_id"]: s for s in C.read_jsonl(C.CORPUS_DIR / "sections.jsonl")}
    acts = {a["act_id"]: a for a in C.read_jsonl(C.CORPUS_DIR / "acts.jsonl")}

    sec_count: collections.Counter[str] = collections.Counter()
    for g in gold:
        for sid in g["indispensable_section_ids"]:
            sec_count[sid] += 1
    act_of = lambda sid: acts[secs[sid]["act_id"]].get("amends_act_id") or secs[sid]["act_id"]  # noqa: E731
    act_count: collections.Counter[str] = collections.Counter()
    for sid, n in sec_count.items():
        act_count[act_of(sid)] += n
    ranked = [a for a, _ in act_count.most_common()]
    top = ranked[: args.top_acts - 1] if len(ranked) > args.top_acts else ranked
    rest = [a for a in ranked if a not in top]

    inner_labels, inner_sizes, inner_colors = [], [], []
    outer_labels, outer_sizes, outer_colors = [], [], []
    for i, a in enumerate(top):
        title = acts[a]["title"] if a in acts else a
        inner_labels.append(SHORT.get(title, title))
        inner_sizes.append(act_count[a])
        inner_colors.append(PALETTE[i % len(PALETTE)])
        members = sorted(((sid, n) for sid, n in sec_count.items() if act_of(sid) == a), key=lambda kv: (-kv[1], kv[0]))
        for j, (sid, n) in enumerate(members):
            s = secs[sid]
            label = f"s.{s['section_number']}" if s["act_kind"] == "principal" else f"{acts[s['act_id']]['number']}/{acts[s['act_id']]['year']} s.{s['section_number']}"
            outer_labels.append(label if n >= 2 else "")
            outer_sizes.append(n)
            outer_colors.append(tint(PALETTE[i % len(PALETTE)], j, len(members)))
    if rest:
        inner_labels.append(f"{len(rest)} other statutes")
        inner_sizes.append(sum(act_count[a] for a in rest))
        inner_colors.append(OTHER)
        members = sorted(((sid, n) for sid, n in sec_count.items() if act_of(sid) in rest), key=lambda kv: (-kv[1], kv[0]))
        for j, (sid, n) in enumerate(members):
            outer_labels.append("")
            outer_sizes.append(n)
            outer_colors.append(tint(OTHER, j, len(members)))

    fig, ax = plt.subplots(figsize=(7.2, 7.2), dpi=220)
    ax.set_aspect("equal")
    w1, _ = ax.pie(inner_sizes, radius=0.62, colors=inner_colors, startangle=90, counterclock=False,
                   wedgeprops=dict(width=0.30, edgecolor="white", linewidth=1.2))
    w2, _ = ax.pie(outer_sizes, radius=1.0, colors=outer_colors, startangle=90, counterclock=False,
                   wedgeprops=dict(width=0.36, edgecolor="white", linewidth=0.8))

    import numpy as np
    # inner labels: rotate along wedge, white text on the darker ring
    for wedge, label, size in zip(w1, inner_labels, inner_sizes):
        ang = (wedge.theta2 + wedge.theta1) / 2
        r = 0.47
        x, y = r * np.cos(np.deg2rad(ang)), r * np.sin(np.deg2rad(ang))
        rot = ang - 90 if -90 <= ((ang + 90) % 360) - 90 <= 90 else ang + 90
        rot = ang if np.cos(np.deg2rad(ang)) >= 0 else ang + 180
        share = size / sum(inner_sizes)
        txt = f"{label}\n({size})" if share > 0.06 else ""
        ax.text(x, y, txt, ha="center", va="center", rotation=rot, rotation_mode="anchor",
                fontsize=6.2 if share > 0.12 else 5.2, color="white", fontweight="bold")
    # outer labels: radial, dark text
    for wedge, label in zip(w2, outer_labels):
        if not label:
            continue
        ang = (wedge.theta2 + wedge.theta1) / 2
        x, y = 0.83 * np.cos(np.deg2rad(ang)), 0.83 * np.sin(np.deg2rad(ang))
        rot = ang if np.cos(np.deg2rad(ang)) >= 0 else ang + 180
        ax.text(x, y, label, ha="center", va="center", rotation=rot, rotation_mode="anchor", fontsize=5.6, color="#0b0b0b")
    ax.text(0, 0, f"statutory-qa-v1\n{len(gold)} questions\n{len(sec_count)} sections", ha="center", va="center", fontsize=7.5, color="#0b0b0b")
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.axis("off")
    fig.tight_layout(pad=0.1)
    out = C.EXPERIMENTS_DIR / "figures"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"gold-sunburst-{args.gold_set}.pdf")
    fig.savefig(out / f"gold-sunburst-{args.gold_set}.png")
    if args.gold_set == "main":
        (C.ROOT / "research-paper" / "figures").mkdir(exist_ok=True)
        shutil.copy(out / "gold-sunburst-main.pdf", C.ROOT / "research-paper" / "figures" / "gold-sunburst.pdf")
    print({"acts_shown": inner_labels, "act_counts": inner_sizes, "sections": len(sec_count)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
