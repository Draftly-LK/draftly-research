"""Split the benchmark by matter into development and test sets.

Questions sharing a matter always land in the same split. Matters are sorted
into strata (hop-count bucket x keep/enrich) and every stratum is shuffled with
a fixed seed; roughly `--dev-fraction` of the matters in each stratum go to
development, the rest to test. With few matters the development set is small;
the limitation is recorded in the output.

    uv run python scripts/statutory-qa/split_dataset.py [--dev-fraction 0.17] [--seed 13]
"""

from __future__ import annotations

import argparse
import collections
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sq_common as C  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dev-fraction", type=float, default=0.17)
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args(argv)
    gold = C.read_jsonl(C.BENCHMARK_DIR / "private-gold.jsonl")
    by_m = collections.defaultdict(list)
    for g in gold:
        by_m[g["benchmark_matter_id"]].append(g)

    def stratum(rows):
        hop = max(r["legal_hop_count"] for r in rows)
        hop_b = "1" if hop == 1 else ("2" if hop == 2 else "3+")
        act = "enrich" if any(r["candidate_action"] == "enrich" for r in rows) else "keep"
        return f"hop{hop_b}-{act}"

    strata = collections.defaultdict(list)
    for mid, rows in sorted(by_m.items()):
        strata[stratum(rows)].append(mid)
    rng = random.Random(args.seed)
    dev, test = [], []
    for name in sorted(strata):
        mids = sorted(strata[name])
        rng.shuffle(mids)
        n_dev = int(round(len(mids) * args.dev_fraction))
        if len(mids) >= 3 and n_dev == 0:
            n_dev = 1
        dev += mids[:n_dev]
        test += mids[n_dev:]
    dev, test = sorted(dev), sorted(test)
    dev_q = sorted(g["benchmark_question_id"] for g in gold if g["benchmark_matter_id"] in set(dev))
    test_q = sorted(g["benchmark_question_id"] for g in gold if g["benchmark_matter_id"] in set(test))
    meta = {"seed": args.seed, "dev_fraction": args.dev_fraction, "strata": {k: len(v) for k, v in sorted(strata.items())},
            "gold_sha256": C.sha256_file(C.BENCHMARK_DIR / "private-gold.jsonl"),
            "limitation": "small development set; parameters tuned on it are reported but their variance is not estimated"}
    C.write_json(C.BENCHMARK_DIR / "development-ids.json", {"matters": dev, "questions": dev_q, **meta})
    C.write_json(C.BENCHMARK_DIR / "test-ids.json", {"matters": test, "questions": test_q, **meta})
    print({"dev_matters": len(dev), "dev_questions": len(dev_q), "test_matters": len(test), "test_questions": len(test_q), "strata": meta["strata"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
