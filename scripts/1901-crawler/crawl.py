"""Crawl one CommonLII court-year into a raw archive plus a JSONL record set.

Stages are deliberately separate, so a parser bug can be fixed by re-running
stage 2 over the archive rather than re-downloading anything:

    1. crawl  -- year index -> judgment links -> raw HTML in raw/
    2. parse  -- raw HTML -> cases.jsonl
    3. report -- counts, failures, citation yield

Usage:
    python crawl.py --db LKSC --year 1906 --check   # robots + reachability
    python crawl.py --db LKSC --year 1906           # crawl then parse
    python crawl.py --parse-only                    # re-parse the archive

Stage 2 parses the whole raw/ archive, so cases.jsonl accumulates every
court-year crawled so far rather than just the one named on the command line.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch as F
import parse_case as P

HERE = Path(__file__).resolve().parent
CASES_JSONL = HERE / "cases.jsonl"
FAILURES = HERE / "parse-failures.csv"


def check(db: str, year: int, transport: str) -> int:
    """Report the site's stated terms and whether it will serve us at all."""
    print("CommonLII access check\n")
    try:
        r = F.read_robots()
    except Exception as e:  # noqa: BLE001
        print(f"  robots.txt unreadable: {type(e).__name__}: {e}")
        return 2
    print("  robots.txt content signals:")
    for k, v in r["signals"].items():
        note = {"ai-train": "  <- training/fine-tuning forbidden",
                "search": "  <- search indexing permitted"}.get(k, "")
        print(f"    {k:<10} = {v}{note}")
    if "ai-input" not in r["signals"]:
        print("    ai-input   = (unspecified) <- RAG/grounding is neither "
              "granted nor restricted")
    print(f"\n  user-agents fully disallowed: {len(r['blocked_agents'])}")
    print(f"    {', '.join(r['blocked_agents'])}")

    print(f"\n  reachability of {db} {year} over the {transport} transport:")
    # A live check, so bypass the cache -- a hit would prove nothing about now.
    f = F.Fetcher(transport=transport)
    url = f"{F.BASE}/lk/cases/{db}/{year}/"
    try:
        status, html = f._fetch_once(url)
        print(f"    HTTP {status}, {len(html):,} bytes -- crawling is possible")
        return 0
    except F.TransportUnavailable as e:
        print(f"    TRANSPORT UNAVAILABLE: {e}")
        return 4
    except (F.HTTPStatus, Exception) as e:  # noqa: BLE001
        print(f"    BLOCKED: {type(e).__name__}: {e}")
        return 3


def crawl(db: str, year: int, transport: str, delay_s: float) -> list[dict]:
    index_url = f"{F.BASE}/lk/cases/{db}/{year}/"
    f = F.Fetcher(transport=transport, delay_s=delay_s)
    print(f"  index: {index_url}")
    page = f.get(index_url, note=f"index:{db}:{year}")
    links = P.extract_links(page.html, index_url)
    print(f"  {len(links)} judgment links found")

    pages = []
    for i, url in enumerate(links, 1):
        try:
            p = f.get(url, note=f"case:{db}:{year}")
            pages.append(p)
            print(f"    [{i}/{len(links)}] {url.rsplit('/', 1)[-1]:<10} "
                  f"{len(p.html):>7,} bytes"
                  + ("  (cached)" if p.from_cache else ""))
        except F.AccessBlocked:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"    [{i}/{len(links)}] {url} FAILED {type(e).__name__}: {e}")
    print(f"\n  {f.summary()}")
    return [{"url": p.url, "html": p.html, "retrieved_at": p.fetched_at}
            for p in pages]


def parse_archive() -> tuple[list[dict], list[tuple[str, str]]]:
    """Stage 2: parse every archived page. No network."""
    f = F.Fetcher(offline=True)
    records, failures = [], []
    for meta_path in sorted(F.CACHE_META.glob("*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        url = meta["source_url"]
        if not P.PATH_RE.search(url):
            continue  # index pages, not judgments
        body = F.RAW / f"{F.url_key(url)}.html"
        if not body.exists():
            continue
        html = body.read_text(encoding="utf-8", errors="replace")
        try:
            records.append(P.parse_case(html, url,
                                        retrieved_at=meta["retrieved_at"]))
        except Exception as e:  # noqa: BLE001
            failures.append((url, f"{type(e).__name__}: {e}"))
    return records, failures


def write_outputs(records: list[dict], failures: list[tuple[str, str]]) -> None:
    with CASES_JSONL.open("w", encoding="utf-8") as fh:
        for r in sorted(records, key=lambda r: (r.get("year", 0),
                                                int(r.get("case_number") or 0))):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    if failures:
        import csv
        with FAILURES.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["url", "error"])
            w.writerows(failures)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default="LKHC")
    ap.add_argument("--year", type=int, default=1901)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--parse-only", action="store_true")
    ap.add_argument("--transport", choices=("cloudscraper", "urllib"),
                    default="cloudscraper",
                    help="cloudscraper solves Cloudflare's managed challenge; "
                         "urllib is the plain honest-User-Agent client, which "
                         "CommonLII currently 403s (see fetch.py)")
    ap.add_argument("--delay", type=float, default=F.DELAY_S,
                    help="seconds between live requests")
    a = ap.parse_args()

    if a.check:
        return check(a.db, a.year, a.transport)

    if not a.parse_only:
        print(f"CommonLII crawl: {a.db} {a.year} (transport: {a.transport})")
        try:
            crawl(a.db, a.year, a.transport, a.delay)
        except F.TransportUnavailable as e:
            print(f"\n  STOPPED: {e}")
            return 4
        except F.AccessBlocked as e:
            print(f"\n  STOPPED: {e}")
            print("\n  Nothing was downloaded. Run --check for the site's terms.")
            return 3

    records, failures = parse_archive()
    write_outputs(records, failures)
    print(f"\n  parsed {len(records)} case(s), {len(failures)} failure(s)")
    if records:
        cites = sum(len(r["report_citations"]) for r in records)
        legis = sum(len(r["cited_legislation"]) for r in records)
        print(f"  report citations: {cites} | legislation refs: {legis}")
        print(f"  wrote {CASES_JSONL.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
