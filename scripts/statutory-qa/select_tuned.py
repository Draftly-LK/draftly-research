"""Pick retrieval hyper-parameters from a tuning run on the development split.

Reads experiments/metrics/<tune-run>/summary.json, picks the best
field-weight / RRF-k / acts-retained / seeds / graph-weight setting by
complete@20 (ties broken by recall@20, then complete@10) and writes the chosen
overrides to experiments/configs/<tune-run>.selected.json.

    uv run python scripts/statutory-qa/select_tuned.py --tune-run tune-dev
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sq_common as C  # noqa: E402


def score(s: dict) -> tuple:
    m = s["metrics"]
    return (round(m["complete@20"]["matter_macro"], 4), round(m["recall@20"]["matter_macro"], 4), round(m["complete@10"]["matter_macro"], 4))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune-run", required=True)
    args = ap.parse_args(argv)
    summ = C.read_json(C.EXPERIMENTS_DIR / "metrics" / args.tune_run / "summary.json")["systems"]

    def best(prefix: str, pattern: str):
        cands = [(score(s), n) for n, s in summ.items() if n.startswith(prefix) and re.search(pattern, n)]
        cands.sort(reverse=True)
        return cands

    bundle = best("tune_bundle_h", r"_a\d")
    hybrid = best("tune_hybrid_", r"_k\d+")
    seeds = best("tune_bundle_seeds", r"\d")
    gsw = best("tune_bundle_gsw", r"\d")
    top = bundle[0][1]
    m = re.match(r"tune_bundle_h([\d.]+)_t([\d.]+)_k(\d+)_a(\d+)", top)
    hw, tw, kk, aa = float(m.group(1)), float(m.group(2)), int(m.group(3)), int(m.group(4))
    seed_n = int(re.search(r"seeds(\d+)", seeds[0][1]).group(1)) if seeds else 15
    gw = float(re.search(r"gsw([\d.]+)", gsw[0][1]).group(1)) if gsw else 0.15
    selected = {
        "field_weights": {"heading": hw, "act_title": tw},
        "rrf_k": kk,
        "acts_retained": aa,
        "seeds": seed_n,
        "graph_support_weight": gw,
    }
    report = {
        "tune_run": args.tune_run,
        "criterion": "complete@20, then recall@20, then complete@10 (matter macro on the development split)",
        "selected": selected,
        "best_bundle_configs": [{"name": n, "complete@20": sc[0], "recall@20": sc[1], "complete@10": sc[2]} for sc, n in bundle[:8]],
        "best_hybrid_configs": [{"name": n, "complete@20": sc[0], "recall@20": sc[1], "complete@10": sc[2]} for sc, n in hybrid[:5]],
        "seeds": [{"name": n, "complete@20": sc[0], "recall@20": sc[1]} for sc, n in seeds],
        "graph_support_weight": [{"name": n, "complete@20": sc[0], "recall@20": sc[1]} for sc, n in gsw],
        "dev_size_warning": "the development split is small; differences between neighbouring settings are within noise",
    }
    C.write_json(C.EXPERIMENTS_DIR / "configs" / f"{args.tune_run}.selected.json", report)
    print(selected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
