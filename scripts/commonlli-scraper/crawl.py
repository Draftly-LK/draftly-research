"""Crawl one CommonLII court-year into a raw archive plus a JSONL record set.

Stages are deliberately separate, so a parser bug can be fixed by re-running
stage 2 over the archive rather than re-downloading anything:

    1. crawl  -- year index -> judgment links -> raw HTML in raw/<db>/
    2. parse  -- raw HTML -> cases-<db>.jsonl
    3. report -- counts, failures, citation yield

Usage:
    python crawl.py --db LKSC --year 1906 --check   # robots + reachability
    python crawl.py --db LKSC --year 1906           # crawl then parse
    python crawl.py --db LKSC --all-years            # year indexes -> year-cases-LKSC.json
    python crawl.py --db LKSC --parse-only           # re-parse the LKSC archive

Every output is namespaced by --db (raw/<db>/, cases-<db>.jsonl,
cases-<db>.json, year-cases-<db>.json, parse-failures-<db>.csv), so running
this for a different database never touches another database's files.

Stage 2 parses the whole raw/<db>/ archive, so cases-<db>.jsonl accumulates
every year of that court crawled so far rather than just the one named on the
command line.
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


def output_paths(db: str) -> dict[str, Path]:
    """Every output file for one database, all namespaced by --db."""
    return {
        "cases_jsonl": HERE / f"cases-{db}.jsonl",
        "cases_json": HERE / f"cases-{db}.json",
        "year_cases_json": HERE / f"year-cases-{db}.json",
        "failures": HERE / f"parse-failures-{db}.csv",
    }

YEARS = (
    1878, 1895, 1896, 1897, 1898, 1899, 1900, 1901, 1902, 1903, 1904, 1905,
    1906, 1908, 1909, 1910, 1911, 1912, 1913, 1914, 1915, 1916, 1917, 1918,
    1919, 1920, 1921, 1922, 1923, 1924, 1925, 1926, 1927, 1928, 1929, 1930,
    1931, 1932, 1933, 1934, 1935, 1936, 1937, 1938, 1939, 1940, 1941, 1942,
    1943, 1944, 1945, 1946, 1947, 1948, 1949, 1950, 1951, 1952, 1953, 1954,
    1955, 1956, 1957, 1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966,
    1967, 1968, 1969, 1970, 1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978,
    1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990,
    1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002,
    2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012,
)


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
    f = F.Fetcher(db, transport=transport)
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


def crawl(db: str, year: int, transport: str, delay_s: float,
          limit: int = 0) -> list[dict]:
    index_url = f"{F.BASE}/lk/cases/{db}/{year}/"
    f = F.Fetcher(db, transport=transport, delay_s=delay_s)
    print(f"  index: {index_url}")
    page = f.get(index_url, note=f"index:{db}:{year}")
    links = P.extract_links(page.html, index_url)
    print(f"  {len(links)} judgment links found")
    if limit:
        links = links[:limit]
        print(f"  --limit {limit}: downloading only the first {len(links)}")

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


def crawl_year_indexes(db: str, transport: str, delay_s: float) -> int:
    """Fetch each requested year index and write its downloadable case links."""
    f = F.Fetcher(db, transport=transport, delay_s=delay_s)
    by_year: dict[str, list[dict]] = {}
    failures: list[dict] = []

    for position, year in enumerate(YEARS, 1):
        index_url = f"{F.BASE}/lk/cases/{db}/{year}/"
        try:
            page = f.get(index_url, note=f"index:{db}:{year}")
            links = P.extract_download_links(page.html, index_url)
            cases = []
            for url in links:
                match = P.DOWNLOAD_PATH_RE.search(url)
                cases.append({
                    "case_number": match.group("number") if match else None,
                    "file_type": match.group("file_type").lower() if match else None,
                    "url": url,
                })
            by_year[str(year)] = cases
            print(f"  [{position}/{len(YEARS)}] {year}: {len(cases)} cases"
                  + (" (cached)" if page.from_cache else ""))
        except Exception as exc:  # noqa: BLE001
            by_year[str(year)] = []
            failures.append({
                "year": year,
                "index_url": index_url,
                "error": f"{type(exc).__name__}: {exc}",
            })
            print(f"  [{position}/{len(YEARS)}] {year}: FAILED "
                  f"{type(exc).__name__}: {exc}")

        # Keep a valid, resumable result even if a long crawl is interrupted.
        payload = {
            "database": db,
            "year_count": len(YEARS),
            "case_count": sum(len(items) for items in by_year.values()),
            "years": by_year,
            "failures": failures,
        }
        year_cases_json = output_paths(db)["year_cases_json"]
        year_cases_json.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"\n  {f.summary()}")
    print(f"  wrote {year_cases_json.name}: {payload['case_count']} cases "
          f"across {len(YEARS)} years; {len(failures)} failed indexes")
    return 1 if failures else 0


def parse_archive(db: str) -> tuple[list[dict], list[tuple[str, str]]]:
    """Stage 2: parse every archived page for this database. No network."""
    f = F.Fetcher(db, offline=True)
    records, failures = [], []
    for meta_path in sorted(f.cache_meta.glob("*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        url = meta["source_url"]
        if not P.PATH_RE.search(url):
            continue  # index pages, not judgments
        body = f.raw / f"{F.url_key(url)}.html"
        if not body.exists():
            continue
        html = body.read_text(encoding="utf-8", errors="replace")
        try:
            records.append(P.parse_case(html, url,
                                        retrieved_at=meta["retrieved_at"]))
        except Exception as e:  # noqa: BLE001
            failures.append((url, f"{type(e).__name__}: {e}"))
    return records, failures


def write_outputs(records: list[dict], failures: list[tuple[str, str]],
                   db: str) -> None:
    paths = output_paths(db)
    ordered = sorted(records, key=lambda r: (r.get("year", 0),
                                             int(r.get("case_number") or 0)))
    with paths["cases_jsonl"].open("w", encoding="utf-8") as fh:
        for r in ordered:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    paths["cases_json"].write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if failures:
        import csv
        with paths["failures"].open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["url", "error"])
            w.writerows(failures)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default="LKHC")
    ap.add_argument("--year", type=int, default=1901)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--all-years", action="store_true",
                    help="crawl all configured year indexes for --db and write "
                         "year-cases-<db>.json without downloading judgments")
    ap.add_argument("--parse-only", action="store_true")
    ap.add_argument("--transport", choices=("cloudscraper", "urllib"),
                    default="cloudscraper",
                    help="cloudscraper solves Cloudflare's managed challenge; "
                         "urllib is the plain honest-User-Agent client, which "
                         "CommonLII currently 403s (see fetch.py)")
    ap.add_argument("--delay", type=float, default=F.DELAY_S,
                    help="seconds between live requests")
    ap.add_argument("--limit", type=int, default=0,
                    help="download only the first N judgments from the year "
                         "index (0 = all) -- for a quick test before a full run")
    a = ap.parse_args()

    if a.check:
        return check(a.db, a.year, a.transport)

    if a.all_years:
        print(f"CommonLII year-index crawl: {a.db} ({len(YEARS)} years)")
        return crawl_year_indexes(a.db, a.transport, a.delay)

    if not a.parse_only:
        print(f"CommonLII crawl: {a.db} {a.year} (transport: {a.transport})")
        try:
            crawl(a.db, a.year, a.transport, a.delay, limit=a.limit)
        except F.TransportUnavailable as e:
            print(f"\n  STOPPED: {e}")
            return 4
        except F.AccessBlocked as e:
            print(f"\n  STOPPED: {e}")
            print("\n  Nothing was downloaded. Run --check for the site's terms.")
            return 3

    records, failures = parse_archive(a.db)
    write_outputs(records, failures, a.db)
    print(f"\n  parsed {len(records)} case(s), {len(failures)} failure(s)")
    if records:
        cites = sum(len(r["report_citations"]) for r in records)
        legis = sum(len(r["cited_legislation"]) for r in records)
        print(f"  report citations: {cites} | legislation refs: {legis}")
        paths = output_paths(a.db)
        print(f"  wrote {paths['cases_jsonl'].name} and {paths['cases_json'].name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
