"""Catalogue and fetch LankaLaw's per-statute consolidated HTML.

LankaLaw publishes each consolidated statute as a single HTML page and indexes
them alphabetically at

    /legislations/acts-and-laws/consolidated-acts-2024/consolidated-acts-2024-<letter>/

Those pages carry the amendment chain, the marginal-note headings and the full
section text, which is what the section index needs. The corpus holds thirteen
curriculum statutes whose only source is a 26 MB Legislative Enactments volume,
and sections cannot be extracted from a volume without a page range. A
per-statute page fixes that.

Two steps, so the matching can be reviewed before anything is downloaded:

    uv run python scripts/harvest_lankalaw_consolidated.py catalogue
    uv run python scripts/harvest_lankalaw_consolidated.py match
    uv run python scripts/harvest_lankalaw_consolidated.py fetch --apply

`catalogue` writes `data/processed/lankalaw-catalogue.csv`. `match` pairs the
catalogue against registry statutes that have no extracted sections. Nothing is
verified: a match is on title, and LankaLaw is a private republisher, not the
Government Printer.
"""

from __future__ import annotations

import argparse
import csv
import html as html_module
import re
import string
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"
SECTION_INDEX = REPO_ROOT / "data/legal-sources/manifests/statute-section-index.json"
CATALOGUE = REPO_ROOT / "data/processed/lankalaw-catalogue.csv"
MATCHES = REPO_ROOT / "data/processed/lankalaw-matches.csv"
DESTINATION = REPO_ROOT / "data/legal-sources/library/statutes/html"

INDEX_URL = (
    "https://lankalaw.net/legislations/acts-and-laws/"
    "consolidated-acts-2024/consolidated-acts-2024-{letter}/"
)
LINK = re.compile(
    r'href="([^"]*wp-content/uploads/[^"]+\.html?)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL
)
USER_AGENT = "Mozilla/5.0 (compatible; draftly-research/1.0; legal corpus build)"
STOPWORDS = {"ordinance", "act", "law", "the", "of", "and", "no", "nos"}

# Pinned by hand where title matching cannot decide. Each is a judgement, so it
# is recorded here rather than buried in a similarity threshold.
OVERRIDES = {
    # LankaLaw spells it "Thesawalamai"; the registry has "Tesawalamai".
    "SRC046": "https://lankalaw.net/wp-content/uploads/2025/02/2001Y3V64C.html",
    # Two pages share this title. 1981Y11V290C is the 1981 revised edition,
    # 1956Y12V455C the 1956 one; the later revision is the current text.
    "SRC079": "https://lankalaw.net/wp-content/uploads/2025/02/1981Y11V290C-1.html",
}


def get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def clean(label: str) -> str:
    text = html_module.unescape(re.sub(r"<[^>]+>", "", label))
    return re.sub(r"\s+", " ", text.replace("�", "'")).strip()


def stem(title: str) -> frozenset[str]:
    title = re.sub(r"\bN[o°]?s?\.?\s*\d+\s*of\s*\d{4}\b", "", title, flags=re.IGNORECASE)
    words = re.sub(r"[^a-zA-Z ]", " ", title).lower().split()
    return frozenset(re.sub(r"s$", "", w) for w in words if w and w not in STOPWORDS)


def build_catalogue() -> list[dict[str, str]]:
    rows, seen = [], set()
    for letter in string.ascii_lowercase:
        url = INDEX_URL.format(letter=letter)
        try:
            page = get(url).decode("utf-8", errors="replace")
        except Exception as error:  # noqa: BLE001 - one missing letter is not fatal
            print(f"  {letter}: {type(error).__name__}", file=sys.stderr)
            continue
        found = 0
        for href, label in LINK.findall(page):
            title = clean(label)
            if not title or href in seen:
                continue
            seen.add(href)
            rows.append({"letter": letter, "title": title, "url": href})
            found += 1
        print(f"  {letter}: {found}")
        time.sleep(0.3)
    return rows


def load_targets() -> list[dict[str, str]]:
    """Registry statutes with no sections in the index, or served by a volume."""
    import json

    indexed = set(json.loads(SECTION_INDEX.read_text(encoding="utf-8")))
    with REGISTRY.open(encoding="utf-8-sig") as handle:
        rows = [r for r in csv.DictReader(handle) if r["source_type"] == "statute"]
    targets = []
    for row in rows:
        pdf = Path(row.get("local_pdf_path") or "")
        volume_only = pdf.name.startswith("legislative-enactments")
        if row["source_id"] not in indexed or volume_only:
            targets.append(
                {
                    **row,
                    "reason": "no sections extracted"
                    if row["source_id"] not in indexed
                    else "source is a compendium volume",
                }
            )
    return targets


def cmd_catalogue(args) -> int:
    rows = build_catalogue()
    CATALOGUE.parent.mkdir(parents=True, exist_ok=True)
    with CATALOGUE.open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "# LankaLaw consolidated-statute HTML pages, from their A-Z index.\n"
            "# Private republisher, not the Government Printer. status=unverified.\n"
            "# Generated by scripts/harvest_lankalaw_consolidated.py catalogue.\n"
        )
        writer = csv.DictWriter(handle, fieldnames=["letter", "title", "url"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nwrote {CATALOGUE.relative_to(REPO_ROOT)} with {len(rows)} pages")
    return 0


def cmd_match(args) -> int:
    with CATALOGUE.open(encoding="utf-8") as handle:
        catalogue = list(csv.DictReader(l for l in handle if not l.startswith("#")))
    by_stem: dict[frozenset[str], list[dict]] = {}
    for entry in catalogue:
        by_stem.setdefault(stem(entry["title"]), []).append(entry)

    by_url = {entry["url"]: entry for entry in catalogue}
    results = []
    for target in load_targets():
        if target["source_id"] in OVERRIDES:
            url = OVERRIDES[target["source_id"]]
            entry = by_url.get(url, {"title": "(pinned by hand)"})
            results.append(
                {
                    "source_id": target["source_id"],
                    "official_title": target["official_title"],
                    "act_no": target["act_or_ordinance_no"],
                    "year": target["year"],
                    "reason": target["reason"],
                    "match_count": 1,
                    "matched_title": entry["title"],
                    "url": url,
                    "candidates": "pinned in OVERRIDES",
                }
            )
            continue
        key = stem(target["official_title"])
        hits = by_stem.get(key, [])
        if not hits:
            # Fall back to the best subset overlap, which catches "Thesawalamai"
            # against "Tesawalamai" style spelling drift only when one contains
            # the other; anything looser is left unmatched for a person to judge.
            hits = [
                e
                for s, entries in by_stem.items()
                if key and (key <= s or s <= key) and len(key & s) >= 2
                for e in entries
            ]
        results.append(
            {
                "source_id": target["source_id"],
                "official_title": target["official_title"],
                "act_no": target["act_or_ordinance_no"],
                "year": target["year"],
                "reason": target["reason"],
                "match_count": len(hits),
                "matched_title": hits[0]["title"] if len(hits) == 1 else "",
                "url": hits[0]["url"] if len(hits) == 1 else "",
                "candidates": " | ".join(h["title"] for h in hits) if len(hits) > 1 else "",
            }
        )

    with MATCHES.open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "# Registry statutes with no extracted sections, matched by title against\n"
            "# the LankaLaw catalogue. match_count=1 rows are what `fetch` downloads.\n"
        )
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    exact = [r for r in results if r["match_count"] == 1]
    none = [r for r in results if r["match_count"] == 0]
    many = [r for r in results if r["match_count"] > 1]
    print(f"{len(results)} statutes need a source")
    print(f"  {len(exact)} matched exactly, {len(many)} ambiguous, {len(none)} unmatched")
    for row in exact:
        print(f"    OK   {row['source_id']} {row['official_title'][:46]:48} {row['url'].rsplit('/', 1)[-1]}")
    for row in many:
        print(f"    ??   {row['source_id']} {row['official_title'][:46]:48} {row['match_count']} candidates")
    for row in none:
        print(f"    --   {row['source_id']} {row['official_title'][:46]:48} no match")
    print(f"\nwrote {MATCHES.relative_to(REPO_ROOT)}")
    return 0


def cmd_fetch(args) -> int:
    with MATCHES.open(encoding="utf-8") as handle:
        rows = [
            r
            for r in csv.DictReader(l for l in handle if not l.startswith("#"))
            if r["match_count"] == "1"
        ]
    print(f"{len(rows)} pages to fetch")
    if not args.apply:
        print("Dry run. Re-run with --apply.")
        return 0

    DESTINATION.mkdir(parents=True, exist_ok=True)
    for index, row in enumerate(rows, 1):
        number, year = row["act_no"], row["year"]
        prefix = f"{int(number)}-{year}-" if number and year.isdigit() and year != "0" else ""
        slug = re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", row["official_title"].lower())).strip("-")
        target = DESTINATION / f"{prefix}{slug}.html"
        try:
            payload = get(row["url"])
        except Exception as error:  # noqa: BLE001
            print(f"  [{index}/{len(rows)}] {row['source_id']}: {type(error).__name__}")
            continue
        target.write_bytes(payload)
        print(f"  [{index}/{len(rows)}] {target.name}  {len(payload) // 1024} KB")
        time.sleep(0.4)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("catalogue").set_defaults(func=cmd_catalogue)
    sub.add_parser("match").set_defaults(func=cmd_match)
    fetch = sub.add_parser("fetch")
    fetch.add_argument("--apply", action="store_true")
    fetch.set_defaults(func=cmd_fetch)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
