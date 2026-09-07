"""Run retrieval systems over the benchmark and write raw rankings.

Reads benchmark/public-input.jsonl (never the gold file) and a split file,
runs each named system/ablation, and writes:

  experiments/raw-rankings/<run>/<system>.jsonl   one row per query
  experiments/configs/<run>.json                  configs, hashes, env, seeds

    uv run python scripts/statutory-qa/run_retrieval.py --run main-test --split test --systems all
    uv run python scripts/statutory-qa/run_retrieval.py --run tune-dev --split dev --tune
"""

from __future__ import annotations

import argparse
import itertools
import json
import platform
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sq_common as C  # noqa: E402
import sq_retrieval as R  # noqa: E402


def load_queries(split: str, gold_set: str = "main") -> list[R.Query]:
    name = "public-input.jsonl" if gold_set == "main" else "public-input-extended.jsonl"
    public = C.read_jsonl(C.BENCHMARK_DIR / name)
    if split != "all":
        ids = set(C.read_json(C.BENCHMARK_DIR / f"{'development' if split == 'dev' else 'test'}-ids.json")["questions"])
        public = [p for p in public if p["benchmark_question_id"] in ids]
    out = []
    for p in public:
        year = int(p["matter_reference_date"][:4]) if p.get("matter_reference_date") else None
        out.append(R.Query(p["benchmark_question_id"], p["benchmark_matter_id"],
                           C.normalize_ws(f"{p['background']} {p['question']}"), year,
                           question=C.normalize_ws(p["question"]), background=C.normalize_ws(p["background"])))
    return out


def run_system(ret: R.Retriever, name: str, cfg: R.Config, queries: list[R.Query], out_dir: Path) -> dict:
    rows = []
    t0 = time.perf_counter()
    for q in queries:
        rows.append(ret.run(q, cfg))
    for rr in ret._rerankers.values():
        rr.flush()
    C.write_jsonl(out_dir / f"{name}.jsonl", rows)
    return {"system": name, "config": cfg.to_json(), "queries": len(rows),
            "seconds": round(time.perf_counter() - t0, 2),
            "mean_latency_ms": round(sum(r["latency_ms"] for r in rows) / max(1, len(rows)), 1)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True)
    ap.add_argument("--split", choices=["dev", "test", "all"], default="test")
    ap.add_argument("--set", dest="gold_set", choices=["main", "extended"], default="main", help="main = proposed_gold only; extended = adds needs_legal_review questions with verified provisions")
    ap.add_argument("--systems", default="all", help="comma list of preset/ablation names, 'systems', 'ablations' or 'all'")
    ap.add_argument("--tune", action="store_true", help="grid over field weights / rrf_k / acts_retained / seeds on the chosen split")
    ap.add_argument("--config-overrides", default=None, help="JSON dict applied to every Config (e.g. tuned parameters)")
    args = ap.parse_args(argv)

    queries = load_queries(args.split, args.gold_set)
    out_dir = C.EXPERIMENTS_DIR / "raw-rankings" / args.run
    out_dir.mkdir(parents=True, exist_ok=True)
    ret = R.Retriever()
    overrides = json.loads(args.config_overrides) if args.config_overrides else {}

    presets = {}
    if args.tune:
        grid = {
            "heading_w": [1.0, 2.0, 3.0, 4.0],
            "title_w": [1.0, 2.0, 3.0],
            "rrf_k": [20, 60],
            "acts": [2, 3, 4],
        }
        for hw, tw, kk, aa in itertools.product(*grid.values()):
            fw = dict(R.DEFAULT_FIELD_WEIGHTS, heading=hw, act_title=tw)
            presets[f"tune_bm25f_h{hw}_t{tw}"] = R.Config("bm25f", field_weights=fw)
            presets[f"tune_hybrid_h{hw}_t{tw}_k{kk}"] = R.Config("hybrid", field_weights=fw, rrf_k=kk)
            presets[f"tune_bundle_h{hw}_t{tw}_k{kk}_a{aa}"] = R.Config("bundle", field_weights=fw, rrf_k=kk, acts_retained=aa, rerank=False)
        for seeds in (10, 15, 20, 30):
            presets[f"tune_bundle_seeds{seeds}"] = R.Config("bundle", seeds=seeds, rerank=False)
        for gw in (0.0, 0.1, 0.15, 0.3):
            presets[f"tune_bundle_gsw{gw}"] = R.Config("bundle", graph_support_weight=gw)
    else:
        names = args.systems
        if names == "all":
            presets = {**R.SYSTEM_PRESETS, **R.ABLATIONS}
        elif names == "systems":
            presets = dict(R.SYSTEM_PRESETS)
        elif names == "ablations":
            presets = dict(R.ABLATIONS)
        elif names == "rerank-variants":
            presets = dict(R.RERANK_VARIANTS)
        else:
            allp = {**R.SYSTEM_PRESETS, **R.ABLATIONS, **R.RERANK_VARIANTS}
            presets = {n: allp[n] for n in names.split(",")}
    for cfg in presets.values():
        for k, v in overrides.items():
            if k == "field_weights":
                cfg.field_weights = dict(cfg.field_weights, **v)
            elif k == "expansion_relations":
                pass
            elif hasattr(cfg, k) and cfg.system in ("bm25f", "hybrid", "hybrid_rerank", "hier", "bundle"):
                setattr(cfg, k, v)

    results = []
    for name, cfg in presets.items():
        r = run_system(ret, name, cfg, queries, out_dir)
        results.append(r)
        print(f"{name:<32} {r['queries']} queries  {r['seconds']}s  mean {r['mean_latency_ms']} ms")

    try:
        import sentence_transformers, torch, transformers  # noqa
        env = {"python": platform.python_version(), "platform": platform.platform(),
               "torch": torch.__version__, "transformers": transformers.__version__,
               "sentence_transformers": sentence_transformers.__version__, "device": "cpu"}
    except Exception:
        env = {"python": platform.python_version(), "platform": platform.platform()}
    C.write_json(C.EXPERIMENTS_DIR / "configs" / f"{args.run}.json", {
        "run": args.run, "split": args.split, "gold_set": args.gold_set, "timestamp": C.utc_now(), "git_commit": C.git_commit(),
        "corpus_fingerprint": ret.corpus.fingerprint,
        "corpus_manifest_sha256": C.sha256_file(C.CORPUS_DIR / "manifest.json"),
        "public_input_sha256": C.sha256_file(C.BENCHMARK_DIR / ("public-input.jsonl" if args.gold_set == "main" else "public-input-extended.jsonl")),
        "split_file_sha256": C.sha256_file(C.BENCHMARK_DIR / f"{'development' if args.split == 'dev' else 'test'}-ids.json") if args.split != "all" else None,
        "embedding_model": R.EMBED_MODEL, "embedding_query_prefix": R.EMBED_QUERY_PREFIX, "chunking": {"chars": R.CHUNK_CHARS, "stride": R.CHUNK_STRIDE, "max_chunks": R.MAX_CHUNKS_PER_SECTION},
        "reranker_model": R.RERANK_MODEL, "reranker_max_length": 512,
        "bm25": {"k1": 1.2, "b": 0.75, "tokenizer": "[0-9a-z]+ casefold, closed-class stopwords"},
        "query_format": "normalized background (enriched where applied) + ' ' + question",
        "overrides": overrides, "environment": env, "systems": results,
    })
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
