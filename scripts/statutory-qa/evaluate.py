"""Score raw rankings against private-gold and write metrics, tables, figures
and an error analysis.

Scoring unit: corpus section. Gold per question = indispensable section ids
(principal metric) plus supporting section ids (graded relevance for nDCG).

Metrics per question, then macro-averaged by matter (questions in a matter are
not independent), with matter-level bootstrap 95% CIs and paired bootstrap
deltas against a reference system:

  recall@k (k=5,10,20)   share of indispensable sections in the top k
  complete@k             1 if every indispensable section is in the top k
  mrr                    1/rank of the first indispensable section
  ndcg@10                gains: indispensable 2, supporting 1
  act_acc@k              every gold Act has >= 1 section in the top k
  act_route_acc          for routed systems: every gold Act retained
  temporal_viol@10       top-10 sections not in force at the matter date
  latency_ms

    uv run python scripts/statutory-qa/evaluate.py --run main-test --reference S5_hybrid_rerank
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sq_common as C  # noqa: E402

KS = (5, 10, 20)
METRIC_VERSION = "statutory-qa-metrics-v1"
BOOT = 2000
SEED = 13


def per_question(row: dict, gold: dict, secs: dict, acts: dict) -> dict:
    ranking = row["ranking"]
    ind = set(gold["indispensable_section_ids"])
    sup = set(gold["supporting_section_ids"])
    pos = {sid: i for i, sid in enumerate(ranking)}
    m: dict = {"query_id": row["query_id"], "matter_id": row["matter_id"], "n_ind": len(ind)}
    for k in KS:
        topk = set(ranking[:k])
        hit = len(ind & topk)
        m[f"recall@{k}"] = hit / len(ind) if ind else float("nan")
        m[f"complete@{k}"] = 1.0 if ind and ind <= topk else 0.0
        gold_acts = set(gold["gold_act_ids"])
        got_acts = {secs[s]["act_id"] for s in topk if s in secs}
        got_acts |= {acts[a].get("amends_act_id") for a in got_acts if acts.get(a, {}).get("amends_act_id")}
        m[f"act_acc@{k}"] = 1.0 if gold_acts <= got_acts else 0.0
    first = min((pos[s] for s in ind if s in pos), default=None)
    m["mrr"] = 1.0 / (first + 1) if first is not None else 0.0
    gains = {s: 2.0 for s in ind}
    gains.update({s: 1.0 for s in sup if s not in ind})
    dcg = sum(gains.get(s, 0.0) / math.log2(i + 2) for i, s in enumerate(ranking[:10]))
    ideal = sorted(gains.values(), reverse=True)[:10]
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    m["ndcg@10"] = dcg / idcg if idcg else float("nan")
    year = int(gold["matter_reference_date"][:4])
    viol = 0
    for s in ranking[:10]:
        sec = secs.get(s)
        if not sec:
            continue
        y = sec.get("in_force_from_year")
        a = acts.get(sec["act_id"], {})
        if (y and y > year) or (a.get("kind") == "amendment" and a.get("year") and a["year"] > year):
            viol += 1
    m["temporal_viol@10"] = viol / max(1, min(10, len(ranking)))
    if "acts_retained" in row:
        retained = set(row["acts_retained"])
        m["act_route_acc"] = 1.0 if set(gold["gold_act_ids"]) <= retained else 0.0
        m["n_acts_retained"] = len(retained)
    m["latency_ms"] = row.get("latency_ms", float("nan"))
    m["missed_ind"] = sorted(ind - set(ranking[:20]))
    m["first_rank"] = None if first is None else first + 1
    return m


def matter_macro(rows: list[dict], metric: str) -> dict[str, float]:
    by_m = collections.defaultdict(list)
    for r in rows:
        v = r.get(metric)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            continue
        by_m[r["matter_id"]].append(v)
    return {m: float(np.mean(v)) for m, v in by_m.items()}


def bootstrap(values_by_matter: dict[str, float], rng: np.random.Generator) -> tuple[float, float, float]:
    mids = sorted(values_by_matter)
    vals = np.array([values_by_matter[m] for m in mids])
    if len(vals) == 0:
        return float("nan"), float("nan"), float("nan")
    idx = rng.integers(0, len(vals), size=(BOOT, len(vals)))
    means = vals[idx].mean(axis=1)
    return float(vals.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired(a: dict[str, float], b: dict[str, float], rng: np.random.Generator) -> dict:
    mids = sorted(set(a) & set(b))
    if not mids:
        return {}
    d = np.array([a[m] - b[m] for m in mids])
    idx = rng.integers(0, len(d), size=(BOOT, len(d)))
    means = d[idx].mean(axis=1)
    return {"delta": float(d.mean()), "ci_low": float(np.percentile(means, 2.5)), "ci_high": float(np.percentile(means, 97.5)),
            "p_le_0": float((means <= 0).mean()), "n_matters": len(mids)}


def error_taxonomy(m: dict, row: dict, gold: dict, secs: dict, acts: dict, edges_in: dict) -> list[str]:
    if not m["missed_ind"]:
        return ["complete@20"]
    tags = []
    top20 = set(row["ranking"][:20])
    got_acts = {secs[s]["act_id"] for s in top20 if s in secs}
    for sid in m["missed_ind"]:
        sec = secs[sid]
        act = sec["act_id"]
        if act not in got_acts and acts[act].get("amends_act_id") not in got_acts:
            tags.append("correct_act_missed")
        elif "acts_retained" in row and act not in set(row["acts_retained"]) and acts[act].get("amends_act_id") not in set(row["acts_retained"]):
            tags.append("act_routing_dropped_gold_act")
        else:
            tags.append("act_found_provision_missed")
        if any(e["relation"] == "defines" for e in edges_in.get(sid, []) if e["src"] in top20):
            tags.append("definition_omitted")
        if any(e["relation"] in ("excepts", "qualifies") for e in edges_in.get(sid, []) if e["src"] in top20):
            tags.append("exception_omitted")
        if any(e["relation"] in ("cross_references", "procedurally_requires") for e in edges_in.get(sid, []) if e["src"] in top20):
            tags.append("cross_reference_not_followed")
        if acts[act]["kind"] == "amendment":
            tags.append("amending_act_missed")
    if len(gold["indispensable_section_ids"]) > 1 and len(m["missed_ind"]) < len(gold["indispensable_section_ids"]):
        tags.append("partial_multi_provision")
    if gold.get("candidate_action") == "enrich":
        tags.append("enriched_scenario")
    return sorted(set(tags))


def fmt(x: float) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True)
    ap.add_argument("--reference", default="S5_hybrid_rerank")
    ap.add_argument("--proposed", default="S7_bundle")
    ap.add_argument("--set", dest="gold_set", choices=["main", "extended"], default="main")
    args = ap.parse_args(argv)

    gold_path = C.BENCHMARK_DIR / ("private-gold.jsonl" if args.gold_set == "main" else "private-gold-extended.jsonl")
    gold = {g["benchmark_question_id"]: g for g in C.read_jsonl(gold_path)}
    secs = {s["section_id"]: s for s in C.read_jsonl(C.CORPUS_DIR / "sections.jsonl")}
    acts = {a["act_id"]: a for a in C.read_jsonl(C.CORPUS_DIR / "acts.jsonl")}
    edges_in = collections.defaultdict(list)
    for e in C.read_jsonl(C.CORPUS_DIR / "edges.jsonl"):
        edges_in[e["dst"]].append(e)
    rank_dir = C.EXPERIMENTS_DIR / "raw-rankings" / args.run
    met_dir = C.EXPERIMENTS_DIR / "metrics" / args.run
    tab_dir = C.EXPERIMENTS_DIR / "tables" / args.run
    err_dir = C.EXPERIMENTS_DIR / "error-analysis" / args.run
    for d in (met_dir, tab_dir, err_dir):
        d.mkdir(parents=True, exist_ok=True)

    metrics_all: dict[str, list[dict]] = {}
    for f in sorted(rank_dir.glob("*.jsonl")):
        rows = C.read_jsonl(f)
        per = [per_question(r, gold[r["query_id"]], secs, acts) for r in rows if r["query_id"] in gold]
        metrics_all[f.stem] = per
    metric_names = [f"recall@{k}" for k in KS] + [f"complete@{k}" for k in KS] + ["mrr", "ndcg@10"] + [f"act_acc@{k}" for k in KS] + ["temporal_viol@10", "latency_ms"]

    summary = {}
    rng = np.random.default_rng(SEED)
    macro_cache: dict[tuple[str, str], dict[str, float]] = {}
    for name, per in metrics_all.items():
        s = {"system": name, "questions": len(per), "matters": len({p["matter_id"] for p in per}), "metrics": {}}
        for mn in metric_names + (["act_route_acc", "n_acts_retained"] if any("act_route_acc" in p for p in per) else []):
            mm = matter_macro(per, mn)
            macro_cache[(name, mn)] = mm
            mean, lo, hi = bootstrap(mm, np.random.default_rng(SEED))
            micro = float(np.nanmean([p[mn] for p in per if p.get(mn) is not None])) if per else float("nan")
            s["metrics"][mn] = {"matter_macro": mean, "ci95": [lo, hi], "question_micro": micro}
        summary[name] = s
    for name in summary:
        comp = {}
        for ref in {args.reference, args.proposed}:
            if ref in summary and ref != name:
                comp[ref] = {mn: paired(macro_cache[(name, mn)], macro_cache[(ref, mn)], np.random.default_rng(SEED))
                             for mn in ("complete@10", "complete@20", "recall@10", "recall@20", "mrr", "ndcg@10")}
        summary[name]["paired_vs"] = comp

    # per-hop / per-action / per-act breakdowns for the main systems
    breakdown = {}
    for name, per in metrics_all.items():
        b = {"by_hop": {}, "by_action": {}, "by_n_ind": {}, "by_act": {}}
        for p in per:
            g = gold[p["query_id"]]
            for key, val in (("by_hop", str(g["legal_hop_count"])), ("by_action", g["candidate_action"]), ("by_n_ind", str(p["n_ind"]))):
                b[key].setdefault(val, []).append(p)
            for a in g["gold_act_ids"]:
                b["by_act"].setdefault(a, []).append(p)
        for key in b:
            b[key] = {k: {"n": len(v), "complete@10": float(np.mean([x["complete@10"] for x in v])), "recall@10": float(np.nanmean([x["recall@10"] for x in v])), "complete@20": float(np.mean([x["complete@20"] for x in v]))}
                      for k, v in sorted(b[key].items())}
        breakdown[name] = b

    C.write_json(met_dir / "summary.json", {"run": args.run, "metric_version": METRIC_VERSION, "bootstrap": BOOT, "seed": SEED,
                                            "gold_set": args.gold_set, "gold_sha256": C.sha256_file(gold_path),
                                            "gold_status": "proposed_gold, lawyer validation pending", "systems": summary, "breakdown": breakdown})
    for name, per in metrics_all.items():
        C.write_jsonl(met_dir / f"{name}.per-question.jsonl", per)

    # error analysis
    err_rows, tax = [], {}
    rank_rows = {f.stem: {r["query_id"]: r for r in C.read_jsonl(f)} for f in rank_dir.glob("*.jsonl")}
    for name, per in metrics_all.items():
        counter = collections.Counter()
        for p in per:
            tags = error_taxonomy(p, rank_rows[name][p["query_id"]], gold[p["query_id"]], secs, acts, edges_in)
            counter.update(tags)
            if p["missed_ind"]:
                err_rows.append({"system": name, "query_id": p["query_id"], "matter_id": p["matter_id"], "tags": tags,
                                 "missed": p["missed_ind"], "missed_citations": [secs[s]["citation"] for s in p["missed_ind"]],
                                 "first_rank": p["first_rank"], "top5": rank_rows[name][p["query_id"]]["ranking"][:5]})
        tax[name] = dict(counter)
    C.write_jsonl(err_dir / "errors.jsonl", err_rows)
    C.write_json(err_dir / "taxonomy.json", tax)

    # tables
    order = [n for n in ("S1_bm25", "S2_bm25f", "S3_dense", "S4_hybrid_rrf", "S5_hybrid_rerank", "S6_hier", "S7_bundle") if n in summary]
    order += sorted(n for n in summary if n not in order)
    cols = ["recall@5", "recall@10", "recall@20", "complete@10", "complete@20", "mrr", "ndcg@10", "act_acc@10", "temporal_viol@10", "latency_ms"]
    md = ["| system | n | " + " | ".join(cols) + " |", "| --- | ---: | " + " | ".join("---:" for _ in cols) + " |"]
    for n in order:
        s = summary[n]
        cells = []
        for c in cols:
            v = s["metrics"][c]
            if c == "latency_ms":
                cells.append(f"{v['matter_macro']:.0f}")
            else:
                cells.append(f"{v['matter_macro']:.3f} [{v['ci95'][0]:.2f}, {v['ci95'][1]:.2f}]")
        md.append(f"| {n} | {s['questions']} | " + " | ".join(cells) + " |")
    C.write_text(tab_dir / "main.md", "\n".join(md) + "\n")

    # LaTeX main table (compact)
    tex_cols = ["recall@10", "recall@20", "complete@10", "complete@20", "mrr", "ndcg@10", "act_acc@10"]
    tex = ["\\begin{tabular}{l" + "c" * len(tex_cols) + "}", "\\toprule",
           "System & R@10 & R@20 & C@10 & C@20 & MRR & nDCG@10 & Act@10 \\\\", "\\midrule"]
    pretty = {"S1_bm25": "BM25", "S2_bm25f": "Field-weighted BM25", "S3_dense": "Dense (bge-base)", "S4_hybrid_rrf": "BM25F + dense (RRF)",
              "S5_hybrid_rerank": "Hybrid + cross-encoder", "S6_hier": "Hierarchical Act$\\rightarrow$section", "S7_bundle": "Hierarchical + bundle (ours)"}
    for n in order:
        if n.startswith("A") and "_no_" in n:
            continue
        s = summary[n]
        cells = [f"{s['metrics'][c]['matter_macro']:.3f}" for c in tex_cols]
        tex.append(f"{pretty.get(n, n)} & " + " & ".join(cells) + " \\\\")
    tex += ["\\bottomrule", "\\end{tabular}"]
    C.write_text(tab_dir / "main.tex", "\n".join(tex) + "\n")
    abl = [n for n in order if n.startswith("A")]
    if abl and args.proposed in summary:
        tex = ["\\begin{tabular}{lccc}", "\\toprule", "Variant & C@10 & C@20 & R@20 \\\\", "\\midrule"]
        s = summary[args.proposed]
        tex.append(f"Full system & {s['metrics']['complete@10']['matter_macro']:.3f} & {s['metrics']['complete@20']['matter_macro']:.3f} & {s['metrics']['recall@20']['matter_macro']:.3f} \\\\")
        for n in abl:
            s = summary[n]
            label = n.split("_", 1)[1].replace("_", " ")
            if label.startswith("no "):
                label = label[3:]
            tex.append(f"\\quad without {label} & {s['metrics']['complete@10']['matter_macro']:.3f} & {s['metrics']['complete@20']['matter_macro']:.3f} & {s['metrics']['recall@20']['matter_macro']:.3f} \\\\")
        tex += ["\\bottomrule", "\\end{tabular}"]
        C.write_text(tab_dir / "ablations.tex", "\n".join(tex) + "\n")

    # figures
    try:
        make_figures(summary, metrics_all, order, args)
    except Exception as exc:  # noqa: BLE001
        print("figure generation failed:", exc)
    print("\n".join(md))
    return 0


def make_figures(summary, metrics_all, order, args) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_dir = C.EXPERIMENTS_DIR / "figures" / args.run
    fig_dir.mkdir(parents=True, exist_ok=True)
    main_sys = [n for n in order if n.startswith("S")]
    labels = {"S1_bm25": "BM25", "S2_bm25f": "BM25F", "S3_dense": "Dense", "S4_hybrid_rrf": "Hybrid RRF",
              "S5_hybrid_rerank": "Hybrid+CE", "S6_hier": "Hier.", "S7_bundle": "Hier.+bundle"}
    # complete@k curves for k in 1..20
    ks = list(range(1, 21))
    fig, ax = plt.subplots(figsize=(4.6, 2.5), dpi=200)
    for n in main_sys:
        per = metrics_all[n]
        rows = C.read_jsonl(C.EXPERIMENTS_DIR / "raw-rankings" / args.run / f"{n}.jsonl")
        gold = {g["benchmark_question_id"]: g for g in C.read_jsonl(C.BENCHMARK_DIR / ("private-gold.jsonl" if args.gold_set == "main" else "private-gold-extended.jsonl"))}
        by_m = collections.defaultdict(list)
        for r in rows:
            g = gold.get(r["query_id"])
            if not g:
                continue
            ind = set(g["indispensable_section_ids"])
            by_m[r["matter_id"]].append([1.0 if ind <= set(r["ranking"][:k]) else 0.0 for k in ks])
        curve = np.mean([np.mean(v, axis=0) for v in by_m.values()], axis=0)
        ax.plot(ks, curve, label=labels.get(n, n), lw=1.6 if n == "S7_bundle" else 1.1)
    ax.set_xlabel("k")
    ax.set_ylabel("complete-indispensable recall@k")
    ax.set_xlim(1, 20)
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=6.5, ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(fig_dir / "complete_at_k.pdf")
    fig.savefig(fig_dir / "complete_at_k.png")
    plt.close(fig)

    abl = [n for n in order if n.startswith("A")]
    if abl and args.proposed in summary:
        fig, ax = plt.subplots(figsize=(4.6, 3.0), dpi=200)
        names = [args.proposed] + abl
        vals = [summary[n]["metrics"]["complete@20"]["matter_macro"] for n in names]
        los = [summary[n]["metrics"]["complete@20"]["ci95"][0] for n in names]
        his = [summary[n]["metrics"]["complete@20"]["ci95"][1] for n in names]
        y = np.arange(len(names))
        ax.barh(y, vals, xerr=[np.array(vals) - np.array(los), np.array(his) - np.array(vals)], color=["#1f77b4"] + ["#9ecae1"] * len(abl), ecolor="#444", capsize=2)
        ax.set_yticks(y)
        ax.set_yticklabels(["full"] + [n.split("_", 1)[1].replace("_", " ").replace("no ", "without ", 1) for n in abl], fontsize=7)
        ax.invert_yaxis()
        ax.set_xlabel("complete-indispensable recall@20 (matter macro, 95% CI)")
        ax.set_xlim(0, 1)
        ax.grid(axis="x", alpha=0.3)
        fig.tight_layout()
        fig.savefig(fig_dir / "ablations.pdf")
        fig.savefig(fig_dir / "ablations.png")
        plt.close(fig)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
