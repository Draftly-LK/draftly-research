"""Harvest the revised Legislative Enactments from srilankalaw.lk.

Two things we cannot get anywhere else that works:

1. **Commencement dates.** The alphabetical list carries a Date of Commencement
   for every one of ~1,464 statutes, in a single request. Our temporal model is
   currently keyed to the amending Act's *year*, so a boundary case ("did this
   1980 Act bind a court sitting in 1981?") cannot be settled. Exact dates fix
   that for the whole statute book.

2. **Text for statutes we hold no text for.** 22 statutes in the section index
   have section numbering but no text. Five of them nominally have a PDF, but it
   is a 1980 Legislative Enactments *volume* shared by several statutes -- one
   volume file is listed against four registry rows -- so extracting a single
   statute means finding its boundaries inside a 480,000-word book. Fetching the
   per-statute page is cheaper and far less error-prone. The volume PDFs stay as
   the check.

Why not the government sites: `documents.gov.lk` serves a placeholder page,
`lawnet.gov.lk` returns an empty body, and `parliament.lk` carries recent Acts
and Bills rather than the nineteenth-century Ordinances this corpus cites.

PROVENANCE, stated plainly: srilankalaw.lk is a private site republishing the
Legislative Enactments. It is NOT the Government Printer. Under
`data/legal-sources/conveyancing-source-checklist.md` it sits at priority 3,
the same tier as any other consolidator -- what improves is access (free, no
login, no seat limit), not authority. Everything it supplies is labelled
`text_source: srilankalaw` and stays `status=unverified`.

    python scripts/harvest_srilankalaw.py --dates          # 1 request
    python scripts/harvest_srilankalaw.py --text           # the statutes we lack
    python scripts/harvest_srilankalaw.py --dates --text
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.srilankalaw.lk"
LIST_URL = f"{BASE}/revised-statutes/alphabetical-list-of-statutes.html?limit=0"

CACHE = ROOT / "tmp/srilankalaw-cache"
REGISTRY = ROOT / "data/legal-sources/manifests/source-registry.csv"
INDEX = ROOT / "data/legal-sources/derived/statute-section-index.json"
OUT_DATES = ROOT / "data/processed/statute_commencement.csv"
SECTIONS_OUT = ROOT / "data/legal-sources/derived/srilankalaw-sections.json"
TEXT_DIR = ROOT / "data/legal-sources/library-markdown/srilankalaw"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Draftly-research/1.0"
DELAY_S = 1.0
PROVIDER = "srilankalaw"

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(t).lower()).strip()


class Fetcher:
    """Cached and rate limited. A cached URL is never re-fetched, so re-running
    the harvest makes zero requests."""

    def __init__(self, delay_s: float = DELAY_S):
        self.delay_s = delay_s
        self.client = httpx.Client(headers={"User-Agent": UA}, timeout=90,
                                   follow_redirects=True, verify=False)
        self.requests = self.hits = 0
        self._last = 0.0
        CACHE.mkdir(parents=True, exist_ok=True)

    def get(self, url: str) -> tuple[str, dict]:
        key = hashlib.sha1(url.encode()).hexdigest()
        body, meta = CACHE / f"{key}.html", CACHE / f"{key}.json"
        if body.exists() and meta.exists():
            self.hits += 1
            return body.read_text(encoding="utf-8", errors="replace"), \
                json.loads(meta.read_text(encoding="utf-8"))
        gap = time.monotonic() - self._last
        if gap < self.delay_s:
            time.sleep(self.delay_s - gap)
        self._last = time.monotonic()
        r = self.client.get(url)
        r.raise_for_status()
        self.requests += 1
        prov = {"source_url": url, "retrieved_at": utc_now(),
                "content_hash": "sha256:" + hashlib.sha256(r.content).hexdigest(),
                "source_provider": PROVIDER}
        body.write_text(r.text, encoding="utf-8")
        meta.write_text(json.dumps(prov, indent=2), encoding="utf-8")
        return r.text, prov

    def summary(self) -> str:
        return f"{self.requests} request(s), {self.hits} from cache"


def parse_date(value: str) -> str:
    """`12 May 1972` -> `1972-05-12`. Returns '' when the form is unexpected."""
    m = re.match(r"\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", value or "")
    if not m:
        return ""
    month = MONTHS.get(m.group(2).lower())
    return f"{m.group(3)}-{month:02d}-{int(m.group(1)):02d}" if month else ""


def parse_list(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for a in soup.find_all("a", href=True):
        if "/alphabetical-list-of-statutes/" not in a["href"]:
            continue
        title = a.get_text(" ", strip=True)
        if not title:
            continue
        row = a.find_parent("tr")
        raw = ""
        if row:
            cells = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            raw = next((c for c in cells
                        if re.match(r"\d{1,2}\s+[A-Za-z]+\s+\d{4}", c)), "")
        out.append({"title": title, "href": a["href"],
                    "commencement_raw": raw, "commencement": parse_date(raw)})
    seen, dedup = set(), []
    for r in out:
        if r["href"] not in seen:
            seen.add(r["href"])
            dedup.append(r)
    return dedup


# The site is paywalled part-way through an article. What sits ABOVE the paywall
# -- long title, Arrangement of Sections, amending-Act list, commencement date --
# is complete. The body below it is cut at an unmarked point, which for a legal
# corpus is worse than having nothing: a section silently missing looks like a
# section that does not exist. So the body text is stored but flagged, and only
# the arrangement is promoted into the section index.
PAYWALL = re.compile(
    r"(?i)only available for our subscribers|subscribe to a subscription plan")

ARRANGEMENT = re.compile(
    r"Arrangement of Sections(.*?)(?:\n\s*\d+ of \d{4}|AN ORDINANCE\b|A LAW\b|AN ACT\b)",
    re.S)
ARR_ENTRY = re.compile(r"(?m)^\s*(\d{1,3}[A-Z]?)\s*\.\s*(.*?)\s*$")


def parse_arrangement(text: str) -> list[dict]:
    """`3. Term of prescription for land.` -> {section, heading}.

    This block precedes the paywall, so it is complete even when the body is
    truncated. It gives an independent second opinion on the section list.
    """
    m = ARRANGEMENT.search(text)
    block = m.group(1) if m else ""
    out, seen = [], set()
    for sec, heading in ARR_ENTRY.findall(block):
        if sec in seen:
            continue
        seen.add(sec)
        heading = re.sub(r"\s+", " ", heading).strip().rstrip(".")
        out.append({"section": sec, "heading": (heading + ".") if heading else ""})
    return out


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "form"]):
        tag.decompose()
    body = soup.find("div", class_=re.compile("item-page|article-content")) or soup
    text = body.get_text("\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text)


def load_registry() -> list[dict]:
    with REGISTRY.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def match_registry(listing: list[dict], registry: list[dict]) -> dict[str, dict]:
    """source_id -> listing row, by normalised title, then by containment.

    Containment is one-directional and only accepted when unique, because
    `Land Registration Ordinance` is contained in `Temple Land Registration
    Ordinance` and matching those would be a silent, wrong join.
    """
    by_norm = {norm(r["title"]): r for r in listing}
    out: dict[str, dict] = {}
    for row in registry:
        title = norm(row.get("official_title", ""))
        if not title:
            continue
        if title in by_norm:
            out[row["source_id"]] = by_norm[title]
            continue
        hits = [v for k, v in by_norm.items() if k == title]
        if not hits:
            cand = [v for k, v in by_norm.items()
                    if k.startswith(title + " ") or title.startswith(k + " ")]
            if len(cand) == 1:
                out[row["source_id"]] = cand[0]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dates", action="store_true", help="harvest commencement dates")
    ap.add_argument("--text", action="store_true",
                    help="fetch text for statutes in the index that have none")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    if not (args.dates or args.text):
        ap.error("pass --dates, --text, or both")

    f = Fetcher()
    html, prov = f.get(LIST_URL)
    listing = parse_list(html)
    registry = load_registry()
    matched = match_registry(listing, registry)
    print(f"  statutes listed        : {len(listing):,}")
    print(f"  with a commencement date: {sum(1 for r in listing if r['commencement']):,}")
    print(f"  matched to a source_id : {len(matched)} of {len(registry)}")

    if args.dates:
        by_sid = {sid: r for sid, r in matched.items()}
        OUT_DATES.parent.mkdir(parents=True, exist_ok=True)
        with OUT_DATES.open("w", encoding="utf-8", newline="") as fh:
            fh.write("# Commencement dates for the revised Legislative Enactments.\n")
            fh.write(f"# Source: {PROVIDER} ({BASE}), a private republisher, NOT the "
                     "Government Printer. status=unverified.\n")
            fh.write("# Generated by scripts/harvest_srilankalaw.py; do not edit by hand.\n")
            w = csv.DictWriter(fh, lineterminator="\n", fieldnames=[
                "source_id", "statute_title", "listed_title", "commencement",
                "commencement_raw", "source_provider", "source_url",
                "retrieved_at", "status"])
            w.writeheader()
            reg_by_id = {r["source_id"]: r for r in registry}
            for sid in sorted(by_sid):
                r = by_sid[sid]
                w.writerow({
                    "source_id": sid,
                    "statute_title": reg_by_id[sid]["official_title"],
                    "listed_title": r["title"],
                    "commencement": r["commencement"],
                    "commencement_raw": r["commencement_raw"],
                    "source_provider": PROVIDER,
                    "source_url": BASE + r["href"],
                    "retrieved_at": prov["retrieved_at"],
                    "status": "unverified",
                })
        dated = sum(1 for sid in by_sid if by_sid[sid]["commencement"])
        print(f"  wrote {OUT_DATES.relative_to(ROOT)}  ({dated} dated)")

    if args.text:
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        reg_by_id = {r["source_id"]: r for r in registry}
        need = [sid for sid in index
                if not (reg_by_id.get(sid, {}).get("local_markdown_path") or "").strip()]
        todo = [(sid, matched[sid]) for sid in need if sid in matched]
        missing = [sid for sid in need if sid not in matched]
        print(f"\n  statutes with no text  : {len(need)}")
        print(f"    available here       : {len(todo)}")
        print(f"    not matched          : {len(missing)}"
              + (f" -> {', '.join(missing[:6])}" if missing else ""))
        TEXT_DIR.mkdir(parents=True, exist_ok=True)
        written = 0
        arrangement: dict[str, dict] = {}
        for sid, row in (todo[:args.limit] if args.limit else todo):
            try:
                page, p = f.get(BASE + row["href"])
            except Exception as e:  # noqa: BLE001
                print(f"    {sid} {row['title'][:38]:<40} FAILED {type(e).__name__}")
                continue
            text = extract_text(page)
            if len(text) < 500:
                print(f"    {sid} {row['title'][:38]:<40} SKIPPED, only {len(text)} chars")
                continue
            truncated = bool(PAYWALL.search(text))
            arrangement[sid] = {
                "source_id": sid, "statute_title": row["title"],
                "sections": parse_arrangement(text),
                "body_truncated": truncated,
                **{k: p[k] for k in ("source_url", "retrieved_at", "content_hash",
                                     "source_provider")},
                "status": "unverified",
            }
            out = TEXT_DIR / f"{sid}-{re.sub(r'[^a-z0-9]+', '-', row['title'].lower()).strip('-')}.md"
            out.write_text(
                f"<!-- source_id: {sid} -->\n"
                f"<!-- source_provider: {PROVIDER} (republisher, not the Government Printer) -->\n"
                f"<!-- source_url: {p['source_url']} -->\n"
                f"<!-- retrieved_at: {p['retrieved_at']} -->\n"
                f"<!-- content_hash: {p['content_hash']} -->\n"
                f"<!-- body_truncated: {str(truncated).lower()} -->\n"
                f"<!-- status: unverified -->\n\n"
                + ("> **Body text is incomplete.** This page is paywalled part-way\n"
                   "> through. The Arrangement of Sections above the cut is complete;\n"
                   "> the section text below it stops at an unmarked point. Do not\n"
                   "> treat the absence of a section here as evidence it does not\n"
                   "> exist.\n\n" if truncated else "")
                + f"# {row['title']}\n\n{text}\n", encoding="utf-8")
            written += 1
            print(f"    {sid} {row['title'][:38]:<40} {len(text):>7,} chars, "
                  f"{len(arrangement[sid]['sections']):>3} in arrangement"
                  + ("  PAYWALLED" if truncated else ""))
        SECTIONS_OUT.parent.mkdir(parents=True, exist_ok=True)
        SECTIONS_OUT.write_text(
            json.dumps(arrangement, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        pay = sum(1 for v in arrangement.values() if v["body_truncated"])
        print(f"  wrote {written} file(s) to {TEXT_DIR.relative_to(ROOT)}")
        print(f"  body truncated by the paywall in {pay} of {written} "
              f"-- text is NOT promoted to the corpus, only the arrangement is")
        print(f"  wrote {SECTIONS_OUT.relative_to(ROOT)}  "
              f"({sum(len(v['sections']) for v in arrangement.values()):,} sections)")

    print(f"\n  {f.summary()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
