"""Retrieval systems for statutory-qa-v1.

Retrieval unit = corpus section (corpus/sections.jsonl). Every system returns
a ranked list of section_ids for a query. Systems:

  bm25            System 1  plain BM25 over "title heading body"
  bm25f           System 2  field-weighted BM25 (act title, part heading,
                            section heading, body, defined terms, xref text)
  dense           System 3  BAAI/bge-base-en-v1.5, cosine, max over chunks
  hybrid          System 4  RRF(bm25f, dense), k=60
  hybrid_rerank   System 5  hybrid top-100 -> cross-encoder -> top-20
  hier            System 6  Act routing (top-A Acts) -> hybrid inside them
  bundle          System 7  hier seeds -> typed-edge expansion -> temporal
                            filter -> rerank with graph support

Every model call is cached on disk under experiments/cache/ keyed by the
corpus fingerprint, so re-running a system is deterministic and free.
Nothing here reads gold labels.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import pickle
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sq_common as C  # noqa: E402

CACHE_DIR = C.EXPERIMENTS_DIR / "cache"
EMBED_MODEL = "BAAI/bge-base-en-v1.5"
EMBED_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
CHUNK_CHARS = 1500
CHUNK_STRIDE = 1200
MAX_CHUNKS_PER_SECTION = 12

STOPWORDS = frozenset("""
a an and are as at be been being but by can did do does for from had has have
he her his how i if in into is it its me my nor not of on or our ours out over
she should so some such than that the their them then there these they this
those to too under until up upon was we were what when where which while who
whom why will with would you your shall may any every such said
""".split())
TOKEN_RE = re.compile(r"[0-9a-z]+")

FIELDS = ["act_title", "part_heading", "heading", "body", "defined_terms", "xref_text"]
DEFAULT_FIELD_WEIGHTS = {"act_title": 2.0, "part_heading": 1.0, "heading": 3.0,
                         "body": 1.0, "defined_terms": 2.0, "xref_text": 0.5}
EXPANSION_RELATIONS = ["defines", "excepts", "qualifies", "cross_references",
                       "procedurally_requires", "amends"]


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(C.normalize_ws(text).casefold()) if t not in STOPWORDS]


def _fingerprint() -> str:
    return C.read_json(C.CORPUS_DIR / "manifest.json")["corpus_fingerprint"]


# --------------------------------------------------------------------------- #
# corpus
# --------------------------------------------------------------------------- #

class Corpus:
    def __init__(self) -> None:
        self.fingerprint = _fingerprint()
        self.sections: list[dict] = C.read_jsonl(C.CORPUS_DIR / "sections.jsonl")
        self.by_id = {s["section_id"]: s for s in self.sections}
        self.ids = [s["section_id"] for s in self.sections]
        self.pos = {sid: i for i, sid in enumerate(self.ids)}
        self.acts = {a["act_id"]: a for a in C.read_jsonl(C.CORPUS_DIR / "acts.jsonl")}
        self.edges = C.read_jsonl(C.CORPUS_DIR / "edges.jsonl")
        self.out_edges: dict[str, list[dict]] = defaultdict(list)
        for e in self.edges:
            self.out_edges[e["src"]].append(e)
        self.sections_by_act: dict[str, list[str]] = defaultdict(list)
        for s in self.sections:
            self.sections_by_act[s["act_id"]].append(s["section_id"])

    def in_force(self, sid: str, year: int | None) -> bool:
        if year is None:
            return True
        s = self.by_id[sid]
        y = s.get("in_force_from_year")
        if y and y > year:
            return False
        a = self.acts[s["act_id"]]
        if a["kind"] == "amendment" and a.get("year") and a["year"] > year:
            return False
        return True


# --------------------------------------------------------------------------- #
# BM25 / BM25F
# --------------------------------------------------------------------------- #

class BM25F:
    """BM25 with per-field weighted term frequencies (a simple BM25F). With all
    weights 1 and a single concatenated field it is plain BM25."""

    def __init__(self, corpus: Corpus, weights: dict[str, float] | None, k1: float = 1.2, b: float = 0.75):
        self.corpus = corpus
        self.weights = dict(weights) if weights else None
        self.k1, self.b = k1, b
        key = hashlib.sha256(json.dumps({"fp": corpus.fingerprint, "w": self.weights, "k1": k1, "b": b}, sort_keys=True).encode()).hexdigest()[:16]
        cache = CACHE_DIR / f"bm25-{key}.pkl"
        if cache.exists():
            with open(cache, "rb") as fh:
                self.postings, self.doc_len, self.avgdl, self.df = pickle.load(fh)
            return
        self.postings: dict[str, list[tuple[int, float]]] = defaultdict(list)
        self.doc_len = np.zeros(len(corpus.ids), dtype=np.float32)
        self.df: Counter[str] = Counter()
        for i, s in enumerate(corpus.sections):
            tf: Counter[str] = Counter()
            if self.weights is None:
                toks = tokenize(f"{s['act_title']} {s['part_heading']} {s['heading']} {s['body']}")
                tf.update(toks)
                self.doc_len[i] = len(toks)
            else:
                total = 0.0
                for f in FIELDS:
                    w = self.weights.get(f, 0.0)
                    if w <= 0:
                        continue
                    val = s[f] if not isinstance(s[f], list) else " ".join(s[f])
                    toks = tokenize(val)
                    for t in toks:
                        tf[t] += w
                    total += w * len(toks)
                self.doc_len[i] = total
            for t, f in tf.items():
                self.postings[t].append((i, f))
                self.df[t] += 1
        self.avgdl = float(self.doc_len.mean()) if len(self.doc_len) else 1.0
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache, "wb") as fh:
            pickle.dump((dict(self.postings), self.doc_len, self.avgdl, self.df), fh)

    def scores(self, query: str, allowed: np.ndarray | None = None) -> np.ndarray:
        n = len(self.corpus.ids)
        out = np.zeros(n, dtype=np.float32)
        for t in set(tokenize(query)):
            plist = self.postings.get(t)
            if not plist:
                continue
            idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
            for i, f in plist:
                denom = f + self.k1 * (1 - self.b + self.b * self.doc_len[i] / self.avgdl)
                out[i] += idf * f * (self.k1 + 1) / denom
        if allowed is not None:
            out = np.where(allowed, out, -np.inf)
        return out


# --------------------------------------------------------------------------- #
# dense
# --------------------------------------------------------------------------- #

class Dense:
    def __init__(self, corpus: Corpus):
        self.corpus = corpus
        self.model = None
        key = hashlib.sha256(f"{corpus.fingerprint}|{EMBED_MODEL}|{CHUNK_CHARS}|{CHUNK_STRIDE}".encode()).hexdigest()[:16]
        self.cache = CACHE_DIR / f"dense-{key}.npz"
        self.qcache_path = CACHE_DIR / f"dense-queries-{key}.pkl"
        self.qcache: dict[str, np.ndarray] = {}
        if self.qcache_path.exists():
            with open(self.qcache_path, "rb") as fh:
                self.qcache = pickle.load(fh)
        if self.cache.exists():
            z = np.load(self.cache)
            self.vectors, self.owner = z["vectors"], z["owner"]
        else:
            self.build()

    def _load_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(EMBED_MODEL, device="cpu")
        return self.model

    @staticmethod
    def chunks(s: dict) -> list[str]:
        head = f"{s['act_title']}. {s['heading']}. "
        body = s["body"]
        if len(body) <= CHUNK_CHARS:
            return [head + body]
        out = []
        for i, start in enumerate(range(0, len(body), CHUNK_STRIDE)):
            piece = body[start:start + CHUNK_CHARS]
            if len(piece) < 200 and out:
                break
            out.append(head + piece)
            if i + 1 >= MAX_CHUNKS_PER_SECTION:
                break
        return out

    def build(self) -> None:
        model = self._load_model()
        texts, owner = [], []
        for i, s in enumerate(self.corpus.sections):
            for c in self.chunks(s):
                texts.append(c)
                owner.append(i)
        t0 = time.time()
        vecs = model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=True, convert_to_numpy=True)
        self.vectors = vecs.astype(np.float32)
        self.owner = np.asarray(owner, dtype=np.int32)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        np.savez(self.cache, vectors=self.vectors, owner=self.owner)
        C.write_json(self.cache.with_suffix(".json"), {"model": EMBED_MODEL, "chunks": len(texts), "sections": len(self.corpus.sections), "seconds": round(time.time() - t0, 1), "chunk_chars": CHUNK_CHARS, "stride": CHUNK_STRIDE})

    def embed_query(self, query: str) -> np.ndarray:
        key = hashlib.sha256(query.encode()).hexdigest()
        if key not in self.qcache:
            v = self._load_model().encode([EMBED_QUERY_PREFIX + query], normalize_embeddings=True, convert_to_numpy=True)[0]
            self.qcache[key] = v.astype(np.float32)
            with open(self.qcache_path, "wb") as fh:
                pickle.dump(self.qcache, fh)
        return self.qcache[key]

    def scores(self, query: str, allowed: np.ndarray | None = None) -> np.ndarray:
        q = self.embed_query(query)
        sims = self.vectors @ q
        out = np.full(len(self.corpus.ids), -np.inf, dtype=np.float32)
        np.maximum.at(out, self.owner, sims)
        if allowed is not None:
            out = np.where(allowed, out, -np.inf)
        return out


# --------------------------------------------------------------------------- #
# reranker
# --------------------------------------------------------------------------- #

class Reranker:
    def __init__(self, corpus: Corpus, model_name: str = RERANK_MODEL):
        self.corpus = corpus
        self.model_name = model_name
        self.model = None
        key = hashlib.sha256(f"{corpus.fingerprint}|{model_name}".encode()).hexdigest()[:16]
        self.cache_path = CACHE_DIR / f"rerank-{key}.pkl"
        self.cache: dict[tuple[str, str], float] = {}
        if self.cache_path.exists():
            with open(self.cache_path, "rb") as fh:
                self.cache = pickle.load(fh)
        self.dirty = 0

    def _load(self):
        if self.model is None:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name, device="cpu", max_length=512)
        return self.model

    def passage(self, sid: str) -> str:
        s = self.corpus.by_id[sid]
        return f"{s['act_title']}. {s['heading']}. {s['body'][:2000]}"

    def score(self, query: str, sids: list[str]) -> dict[str, float]:
        qk = hashlib.sha256(query.encode()).hexdigest()[:24]
        todo = [sid for sid in sids if (qk, sid) not in self.cache]
        if todo:
            preds = self._load().predict([(query, self.passage(sid)) for sid in todo], batch_size=32, show_progress_bar=False)
            for sid, p in zip(todo, preds):
                self.cache[(qk, sid)] = float(p)
            self.dirty += len(todo)
            if self.dirty >= 500:
                self.flush()
        return {sid: self.cache[(qk, sid)] for sid in sids}

    def flush(self) -> None:
        if self.dirty:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "wb") as fh:
                pickle.dump(self.cache, fh)
            self.dirty = 0


# --------------------------------------------------------------------------- #
# fusion helpers
# --------------------------------------------------------------------------- #

def ranked(scores: np.ndarray, ids: list[str], k: int) -> list[str]:
    order = np.argsort(-scores, kind="stable")
    out = []
    for i in order[:k * 3 + 50]:
        if not np.isfinite(scores[i]) or scores[i] <= 0 and False:
            continue
        if not np.isfinite(scores[i]):
            break
        out.append(ids[i])
        if len(out) >= k:
            break
    return out


def rrf(rankings: list[list[str]], k: int = 60, weights: list[float] | None = None) -> dict[str, float]:
    weights = weights or [1.0] * len(rankings)
    fused: dict[str, float] = defaultdict(float)
    for w, ranking in zip(weights, rankings):
        for r, sid in enumerate(ranking):
            fused[sid] += w / (k + r + 1)
    return dict(fused)


def top(d: dict[str, float], k: int) -> list[str]:
    return [sid for sid, _ in sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[:k]]


# --------------------------------------------------------------------------- #
# systems
# --------------------------------------------------------------------------- #

@dataclass
class Query:
    query_id: str
    matter_id: str
    text: str
    reference_year: int | None
    question: str = ""
    background: str = ""

    def rerank_text(self, mode: str, bg_chars: int) -> str:
        """Short query for the cross-encoder. The full background plus question
        overflows a 512-token window and truncates the passage away."""
        if mode == "full" or not self.question:
            return self.text
        if mode == "question":
            return self.question
        return C.normalize_ws(f"{self.question} {self.background[:bg_chars]}")


@dataclass
class Config:
    system: str
    top_k: int = 20
    field_weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_FIELD_WEIGHTS))
    rrf_k: int = 60
    rrf_weights: tuple[float, float] = (1.0, 1.0)
    candidate_depth: int = 100
    use_dense: bool = True
    use_field_weights: bool = True
    # hierarchical
    acts_retained: int = 3
    act_routing: bool = True
    act_score_from_sections: int = 5     # top-N section scores aggregated per Act
    # bundle
    seeds: int = 15
    expansion_relations: tuple[str, ...] = tuple(EXPANSION_RELATIONS)
    temporal_filter: bool = True
    rerank: bool = True
    rerank_query: str = "question+bg"   # full | question | question+bg
    reranker_model: str = RERANK_MODEL
    rerank_bg_chars: int = 400
    graph_support_weight: float = 0.15
    expansion_decay: float = 0.6        # expanded score = decay * best seed score (+ support)
    # decomposition (optional; needs pre-generated sub-queries)
    subqueries: dict[str, list[str]] | None = None

    def to_json(self) -> dict:
        d = self.__dict__.copy()
        d["expansion_relations"] = list(self.expansion_relations)
        d["subqueries"] = None if self.subqueries is None else f"{len(self.subqueries)} queries"
        return d


class Retriever:
    def __init__(self, corpus: Corpus | None = None):
        self.corpus = corpus or Corpus()
        self._bm25: dict[str, BM25F] = {}
        self._dense: Dense | None = None
        self._rerank: Reranker | None = None
        self._rerankers: dict[str, Reranker] = {}

    def bm25(self, weights: dict[str, float] | None) -> BM25F:
        key = json.dumps(weights, sort_keys=True)
        if key not in self._bm25:
            self._bm25[key] = BM25F(self.corpus, weights)
        return self._bm25[key]

    @property
    def dense(self) -> Dense:
        if self._dense is None:
            self._dense = Dense(self.corpus)
        return self._dense

    def reranker_for(self, cfg: "Config") -> Reranker:
        name = cfg.reranker_model
        if name not in self._rerankers:
            self._rerankers[name] = Reranker(self.corpus, name)
        self._rerank = self._rerankers[name]
        return self._rerank

    # -- channels ---------------------------------------------------------
    def lexical_ranking(self, q: Query, cfg: Config, allowed: np.ndarray | None, k: int) -> list[str]:
        idx = self.bm25(cfg.field_weights if cfg.use_field_weights else None)
        return ranked(idx.scores(q.text, allowed), self.corpus.ids, k)

    def dense_ranking(self, q: Query, cfg: Config, allowed: np.ndarray | None, k: int) -> list[str]:
        return ranked(self.dense.scores(q.text, allowed), self.corpus.ids, k)

    def hybrid_scores(self, q: Query, cfg: Config, allowed: np.ndarray | None, depth: int) -> dict[str, float]:
        rankings = [self.lexical_ranking(q, cfg, allowed, depth)]
        weights = [cfg.rrf_weights[0]]
        if cfg.use_dense:
            rankings.append(self.dense_ranking(q, cfg, allowed, depth))
            weights.append(cfg.rrf_weights[1])
        if cfg.subqueries and q.query_id in cfg.subqueries:
            for sq in cfg.subqueries[q.query_id]:
                sub = Query(q.query_id, q.matter_id, sq, q.reference_year)
                rankings.append(self.lexical_ranking(sub, cfg, allowed, depth))
                weights.append(0.5)
                if cfg.use_dense:
                    rankings.append(self.dense_ranking(sub, cfg, allowed, depth))
                    weights.append(0.5)
        return rrf(rankings, cfg.rrf_k, weights)

    # -- act routing ------------------------------------------------------
    def route_acts(self, q: Query, cfg: Config) -> list[str]:
        fused = self.hybrid_scores(q, cfg, None, cfg.candidate_depth)
        per_act: dict[str, list[float]] = defaultdict(list)
        for sid, sc in fused.items():
            per_act[self.corpus.by_id[sid]["act_id"]].append(sc)
        act_scores = {a: sum(sorted(v, reverse=True)[:cfg.act_score_from_sections]) for a, v in per_act.items()}
        # fold amending Acts into their principal enactment for routing
        merged: dict[str, float] = defaultdict(float)
        for a, sc in act_scores.items():
            principal = self.corpus.acts[a].get("amends_act_id") or a
            merged[principal] += sc
        return top(merged, cfg.acts_retained)

    def allowed_mask(self, act_ids: Iterable[str]) -> np.ndarray:
        acts = set(act_ids)
        # include amending Acts of the routed principal enactments
        for a in list(acts):
            acts |= {x["act_id"] for x in self.corpus.acts.values() if x.get("amends_act_id") == a}
        mask = np.zeros(len(self.corpus.ids), dtype=bool)
        for a in acts:
            for sid in self.corpus.sections_by_act.get(a, []):
                mask[self.corpus.pos[sid]] = True
        return mask

    # -- expansion --------------------------------------------------------
    def expand(self, seeds: list[str], cfg: Config, year: int | None,
               seed_scores: dict[str, float] | None = None) -> tuple[list[str], dict[str, int], dict[str, str], dict[str, float]]:
        support: Counter[str] = Counter()
        via: dict[str, str] = {}
        inherited: dict[str, float] = {}
        rels = set(cfg.expansion_relations)
        seed_set = set(seeds)
        for sid in seeds:
            base = (seed_scores or {}).get(sid, 0.0)
            for e in self.corpus.out_edges.get(sid, []):
                if e["relation"] not in rels:
                    continue
                dst = e["dst"]
                if dst in seed_set:
                    continue
                if cfg.temporal_filter and not self.corpus.in_force(dst, year):
                    continue
                support[dst] += 1
                inherited[dst] = max(inherited.get(dst, 0.0), base)
                via.setdefault(dst, f"{sid} -{e['relation']}->")
        expanded = sorted(support, key=lambda d: (-(inherited[d] * (1 + 0.25 * math.log1p(support[d]))), d))
        return expanded, dict(support), via, inherited

    # -- public -----------------------------------------------------------
    def run(self, q: Query, cfg: Config) -> dict[str, Any]:
        t0 = time.perf_counter()
        info: dict[str, Any] = {}
        k = cfg.top_k
        year = q.reference_year if cfg.temporal_filter else None
        if cfg.system == "bm25":
            ranking = self.lexical_ranking(q, Config("bm25", use_field_weights=False), None, k)
        elif cfg.system == "bm25f":
            ranking = self.lexical_ranking(q, cfg, None, k)
        elif cfg.system == "dense":
            ranking = self.dense_ranking(q, cfg, None, k)
        elif cfg.system == "hybrid":
            ranking = top(self.hybrid_scores(q, cfg, None, cfg.candidate_depth), k)
        elif cfg.system == "hybrid_rerank":
            cands = top(self.hybrid_scores(q, cfg, None, cfg.candidate_depth), cfg.candidate_depth)
            sc = self.reranker_for(cfg).score(q.rerank_text(cfg.rerank_query, cfg.rerank_bg_chars), cands)
            ranking = top(sc, k)
        elif cfg.system in ("hier", "bundle"):
            allowed = None
            if cfg.act_routing:
                acts = self.route_acts(q, cfg)
                info["acts_retained"] = acts
                allowed = self.allowed_mask(acts)
            fused = self.hybrid_scores(q, cfg, allowed, cfg.candidate_depth)
            if cfg.temporal_filter and year:
                fused = {sid: sc for sid, sc in fused.items() if self.corpus.in_force(sid, year)}
            if cfg.system == "hier":
                ranking = top(fused, k)
            else:
                seeds = top(fused, cfg.seeds)
                expanded, support, via, inherited = self.expand(seeds, cfg, year, fused)
                info["seeds"] = seeds
                info["expanded"] = expanded[:40]
                info["via"] = {s: via[s] for s in expanded[:40]}
                # score every candidate on the fused scale: seeds keep their
                # fused score, expansions inherit a decayed share of the best
                # seed that reached them, boosted by graph support
                base: dict[str, float] = {sid: fused[sid] for sid in seeds}
                for sid in expanded:
                    base[sid] = cfg.expansion_decay * inherited[sid] * (1 + 0.25 * math.log1p(support[sid]))
                pool = top(base, cfg.candidate_depth)
                if cfg.rerank:
                    sc = self.reranker_for(cfg).score(q.rerank_text(cfg.rerank_query, cfg.rerank_bg_chars), pool)
                    vals = np.array(list(sc.values()), dtype=np.float32)
                    lo, hi = float(vals.min()), float(vals.max())
                    span = (hi - lo) or 1.0
                    bvals = np.array([base[s] for s in pool], dtype=np.float32)
                    blo, bhi = float(bvals.min()), float(bvals.max())
                    bspan = (bhi - blo) or 1.0
                    final = {}
                    for sid in pool:
                        ce = (sc[sid] - lo) / span
                        fz = (base[sid] - blo) / bspan
                        gs = math.log1p(support.get(sid, 0))
                        final[sid] = 0.5 * ce + 0.5 * fz + cfg.graph_support_weight * gs
                    ranking = top(final, k)
                else:
                    ranking = top(base, k)
        else:
            raise ValueError(cfg.system)
        info["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return {"query_id": q.query_id, "matter_id": q.matter_id, "ranking": ranking, **info}


SYSTEM_PRESETS: dict[str, Config] = {
    "S1_bm25": Config("bm25", use_field_weights=False),
    "S2_bm25f": Config("bm25f"),
    "S3_dense": Config("dense"),
    "S4_hybrid_rrf": Config("hybrid"),
    "S5_hybrid_rerank": Config("hybrid_rerank"),
    "S6_hier": Config("hier", temporal_filter=False),
    "S7_bundle": Config("bundle"),
}

RERANK_VARIANTS: dict[str, Config] = {
    "V1_s5_minilm_qbg": Config("hybrid_rerank"),
    "V2_s5_minilm_q": Config("hybrid_rerank", rerank_query="question"),
    "V3_s5_bge_qbg": Config("hybrid_rerank", reranker_model="BAAI/bge-reranker-base"),
    "V4_s5_bge_q": Config("hybrid_rerank", reranker_model="BAAI/bge-reranker-base", rerank_query="question"),
    "V5_s7_bge_qbg": Config("bundle", reranker_model="BAAI/bge-reranker-base"),
    "V6_s7_bge_q": Config("bundle", reranker_model="BAAI/bge-reranker-base", rerank_query="question"),
}

ABLATIONS: dict[str, Config] = {
    "A1_no_act_routing": Config("bundle", act_routing=False),
    "A2_no_field_weights": Config("bundle", use_field_weights=False),
    "A3_no_dense": Config("bundle", use_dense=False),
    "A4_no_temporal": Config("bundle", temporal_filter=False),
    "A5_no_defines": Config("bundle", expansion_relations=tuple(r for r in EXPANSION_RELATIONS if r != "defines")),
    "A6_no_excepts_qualifies": Config("bundle", expansion_relations=tuple(r for r in EXPANSION_RELATIONS if r not in ("excepts", "qualifies"))),
    "A7_no_xref_procedural": Config("bundle", expansion_relations=tuple(r for r in EXPANSION_RELATIONS if r not in ("cross_references", "procedurally_requires"))),
    "A8_no_amends": Config("bundle", expansion_relations=tuple(r for r in EXPANSION_RELATIONS if r != "amends")),
    "A9_no_rerank": Config("bundle", rerank=False),
    "A10_no_expansion": Config("bundle", expansion_relations=()),
}


if __name__ == "__main__":
    # Build the caches (BM25 variants + dense embeddings) so later runs are free.
    sys.stdout.reconfigure(encoding="utf-8")
    r = Retriever()
    r.bm25(None)
    r.bm25(DEFAULT_FIELD_WEIGHTS)
    d = r.dense
    print("dense chunks", d.vectors.shape)
    q = Query("demo", "M000", "Can a notary attest a deed for land outside his district?", 2020)
    for name, cfg in SYSTEM_PRESETS.items():
        if cfg.system in ("hybrid_rerank", "bundle"):
            continue
        out = r.run(q, cfg)
        print(name, out["ranking"][:5], out["latency_ms"], "ms")
