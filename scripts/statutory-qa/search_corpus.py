"""Command-line search over the frozen statutory-qa-v1 corpus.

This is the only corpus access the legal-research and verification agents
have. It never reads gold files. Section ids printed here are the ids a gold
provision must carry.

    uv run python scripts/statutory-qa/search_corpus.py acts
    uv run python scripts/statutory-qa/search_corpus.py search "notary attest outside district" [-k 20] [--act 1-1907]
    uv run python scripts/statutory-qa/search_corpus.py grep "two or more witnesses" [--act 7-1840]
    uv run python scripts/statutory-qa/search_corpus.py show 1-1907/s31 [--full]
    uv run python scripts/statutory-qa/search_corpus.py toc 1-1907
    uv run python scripts/statutory-qa/search_corpus.py edges 38-2014/s3
    uv run python scripts/statutory-qa/search_corpus.py defs 38-2014 foreigner
    uv run python scripts/statutory-qa/search_corpus.py check 7-1840/s2 "No sale, purchase, transfer"
"""

from __future__ import annotations

import argparse
import math
import pickle
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sq_common as C  # noqa: E402

STOPWORDS = frozenset("""
a an and are as at be been being but by can did do does for from had has have
he her his how i if in into is it its me my nor not of on or our ours out over
she should so some such than that the their them then there these they this
those to too under until up upon was we were what when where which while who
whom why will with would you your shall may any every such said
""".split())
TOKEN_RE = re.compile(r"[0-9a-z]+")
CACHE = C.CORPUS_DIR / ".search_cache.pkl"


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(C.normalize_ws(text).casefold()) if t not in STOPWORDS]


class Corpus:
    def __init__(self) -> None:
        self.sections = C.read_jsonl(C.CORPUS_DIR / "sections.jsonl")
        self.by_id = {s["section_id"]: s for s in self.sections}
        self.acts = {a["act_id"]: a for a in C.read_jsonl(C.CORPUS_DIR / "acts.jsonl")}
        self.edges = C.read_jsonl(C.CORPUS_DIR / "edges.jsonl")
        self.out_edges = defaultdict(list)
        self.in_edges = defaultdict(list)
        for e in self.edges:
            self.out_edges[e["src"]].append(e)
            self.in_edges[e["dst"]].append(e)
        self.provisions = None
        self._bm25 = None

    def bm25(self):
        if self._bm25 is None:
            self._bm25 = BM25.load_or_build(self.sections)
        return self._bm25

    def load_provisions(self):
        if self.provisions is None:
            self.provisions = C.read_jsonl(C.CORPUS_DIR / "provisions.jsonl")
        return self.provisions


class BM25:
    """Plain BM25 (k1=1.2, b=0.75) over section text = title + heading + body."""

    def __init__(self, ids, tfs, dls, df, n):
        self.ids, self.tfs, self.dls, self.df, self.n = ids, tfs, dls, df, n
        self.avgdl = sum(dls) / max(1, len(dls))
        self.k1, self.b = 1.2, 0.75

    @staticmethod
    def doc_text(s: dict) -> str:
        return f"{s['act_title']} {s['part_heading']} {s['heading']} {s['body']}"

    @classmethod
    def load_or_build(cls, sections):
        fp = (C.CORPUS_DIR / "manifest.json")
        key = C.read_json(fp)["corpus_fingerprint"] if fp.exists() else None
        if CACHE.exists():
            try:
                with open(CACHE, "rb") as fh:
                    obj = pickle.load(fh)
                if obj.get("key") == key:
                    return obj["index"]
            except Exception:
                pass
        ids, tfs, dls = [], [], []
        df: Counter[str] = Counter()
        for s in sections:
            toks = tokenize(cls.doc_text(s))
            tf = Counter(toks)
            ids.append(s["section_id"])
            tfs.append(tf)
            dls.append(len(toks))
            df.update(tf.keys())
        index = cls(ids, tfs, dls, df, len(ids))
        try:
            with open(CACHE, "wb") as fh:
                pickle.dump({"key": key, "index": index}, fh)
        except Exception:
            pass
        return index

    def search(self, query: str, k: int = 20, allowed: set[str] | None = None):
        q = tokenize(query)
        scores = defaultdict(float)
        for term in set(q):
            if term not in self.df:
                continue
            idf = math.log(1 + (self.n - self.df[term] + 0.5) / (self.df[term] + 0.5))
            for i, tf in enumerate(self.tfs):
                f = tf.get(term)
                if not f:
                    continue
                if allowed is not None and self.ids[i] not in allowed:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * self.dls[i] / self.avgdl)
                scores[self.ids[i]] += idf * f * (self.k1 + 1) / denom
        return sorted(scores.items(), key=lambda kv: -kv[1])[:k]


def snippet(body: str, query: str, width: int = 260) -> str:
    toks = tokenize(query)
    low = body.casefold()
    best, best_pos = -1, 0
    for i in range(0, max(1, len(body) - width), 80):
        window = low[i:i + width]
        hits = sum(1 for t in toks if t in window)
        if hits > best:
            best, best_pos = hits, i
    return ("..." if best_pos else "") + body[best_pos:best_pos + width].strip() + ("..." if best_pos + width < len(body) else "")


def cmd_acts(c: Corpus, args) -> None:
    for a in sorted(c.acts.values(), key=lambda a: (a["kind"] != "principal", a["title"])):
        if args.principal_only and a["kind"] != "principal":
            continue
        extra = f" (amends {a['amends_act_id']})" if a["kind"] == "amendment" else ""
        print(f"{a['act_id']:>9}  {a['kind']:<9} {a['label']}{extra}  [{a['n_sections']} sections]")


def cmd_search(c: Corpus, args) -> None:
    allowed = None
    if args.act:
        allowed = {s["section_id"] for s in c.sections if s["act_id"] in set(args.act)}
    if args.principal_only:
        pr = {s["section_id"] for s in c.sections if s["act_kind"] == "principal"}
        allowed = pr if allowed is None else allowed & pr
    for sid, score in c.bm25().search(args.query, args.k, allowed):
        s = c.by_id[sid]
        print(f"{score:6.2f}  {sid:<18} {s['citation']} | {s['heading'][:70]}")
        print(f"        {snippet(s['body'], args.query)}")


def cmd_grep(c: Corpus, args) -> None:
    pat = re.compile(args.pattern, re.I)
    n = 0
    for s in c.sections:
        if args.act and s["act_id"] not in set(args.act):
            continue
        m = pat.search(s["body"]) or pat.search(s["heading"])
        if m:
            n += 1
            i = max(0, (m.start() if m.re.search(s["body"]) else 0) - 100)
            print(f"{s['section_id']:<18} {s['citation']} | {s['heading'][:60]}")
            print(f"        ...{s['body'][i:i + 260].strip()}...")
            if n >= args.k:
                break
    if n == 0:
        print("no match")


def cmd_show(c: Corpus, args) -> None:
    s = c.by_id.get(args.section_id)
    if not s:
        print(f"unknown section_id {args.section_id}")
        return
    a = c.acts[s["act_id"]]
    print(f"section_id: {s['section_id']}")
    print(f"citation:   {s['citation']}")
    print(f"act:        {a['label']}  kind={a['kind']}  edition={a['edition_kind']}")
    print(f"source:     {a['source_file']}  sha256={a['source_sha256']}")
    print(f"part:       {s['part_heading']}")
    print(f"heading:    {s['heading']}")
    print(f"in_force_from_year: {s['in_force_from_year']}  latest_change_year: {s['latest_change_year']}")
    if s["amendment_events"]:
        print("amendment_events:")
        for ev in s["amendment_events"]:
            print(f"   - {ev['operation']} by {ev['instrument']} s.{ev['amending_section']} ({ev['year']})")
    if s["defined_terms"]:
        print(f"defined_terms: {s['defined_terms']}")
    body = s["body"]
    limit = None if args.full else 6000
    print("body:")
    print(body if limit is None or len(body) <= limit else body[:limit] + f"\n... [{len(body) - limit} more chars; use --full]")
    if args.provisions:
        print("provisions:")
        for p in c.load_provisions():
            if p["section_id"] == s["section_id"]:
                print(f"   {p['node_id']:<40} {p['text'][:120]}")


def cmd_toc(c: Corpus, args) -> None:
    a = c.acts.get(args.act_id)
    if not a:
        print(f"unknown act_id {args.act_id}")
        return
    print(f"{a['label']}  kind={a['kind']}  edition={a['edition_kind']}")
    for s in c.sections:
        if s["act_id"] == args.act_id:
            print(f"  {s['section_id']:<18} [{s['part_heading'][:30]}] s {s['section_number']}: {s['heading'][:80]}  ({s['n_chars']} chars)")


def cmd_edges(c: Corpus, args) -> None:
    sid = args.section_id
    print(f"outgoing from {sid}:")
    for e in c.out_edges.get(sid, []):
        d = c.by_id.get(e["dst"])
        print(f"  -> {e['relation']:<22} {e['dst']:<18} {d['citation'] if d else ''} | {e['evidence'][:60]}")
    print(f"incoming to {sid}:")
    for e in c.in_edges.get(sid, [])[:40]:
        d = c.by_id.get(e["src"])
        print(f"  <- {e['relation']:<22} {e['src']:<18} {d['citation'] if d else ''} | {e['evidence'][:60]}")


def cmd_defs(c: Corpus, args) -> None:
    term = args.term.casefold() if args.term else None
    for s in c.sections:
        if s["act_id"] != args.act_id or not s["defined_terms"]:
            continue
        for t in s["defined_terms"]:
            if term and term not in t.casefold():
                continue
            print(f"{s['section_id']:<18} defines \"{t}\"")
    if term:
        pat = re.compile(r'"' + re.escape(args.term) + r'"[^;.]{0,400}', re.I)
        for s in c.sections:
            if s["act_id"] == args.act_id:
                for m in pat.finditer(s["body"]):
                    print(f"  {s['section_id']}: {m.group(0)[:400]}")


def cmd_check(c: Corpus, args) -> None:
    s = c.by_id.get(args.section_id)
    if not s:
        print("FAIL unknown section_id")
        return
    ok = C.excerpt_in(args.excerpt, s["body"])
    print("OK verbatim excerpt found in", s["section_id"] if ok else "FAIL excerpt is not a verbatim substring of " + s["section_id"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("acts"); p.add_argument("--principal-only", action="store_true"); p.set_defaults(fn=cmd_acts)
    p = sub.add_parser("search"); p.add_argument("query"); p.add_argument("-k", type=int, default=20); p.add_argument("--act", action="append"); p.add_argument("--principal-only", action="store_true"); p.set_defaults(fn=cmd_search)
    p = sub.add_parser("grep"); p.add_argument("pattern"); p.add_argument("-k", type=int, default=30); p.add_argument("--act", action="append"); p.set_defaults(fn=cmd_grep)
    p = sub.add_parser("show"); p.add_argument("section_id"); p.add_argument("--full", action="store_true"); p.add_argument("--provisions", action="store_true"); p.set_defaults(fn=cmd_show)
    p = sub.add_parser("toc"); p.add_argument("act_id"); p.set_defaults(fn=cmd_toc)
    p = sub.add_parser("edges"); p.add_argument("section_id"); p.set_defaults(fn=cmd_edges)
    p = sub.add_parser("defs"); p.add_argument("act_id"); p.add_argument("term", nargs="?"); p.set_defaults(fn=cmd_defs)
    p = sub.add_parser("check"); p.add_argument("section_id"); p.add_argument("excerpt"); p.set_defaults(fn=cmd_check)
    args = ap.parse_args(argv)
    args.fn(Corpus(), args)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
