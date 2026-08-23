"""Fetch LankaLaw's HTML text of the amending Acts, where it exists.

The amendment PDFs we hold from the parliamentary archive are image scans with
no text layer, several of them tens of megabytes. LankaLaw publishes many of the
same Acts as born-digital HTML with the same semantic classes as the
consolidated statutes, which `build_canonical_statutes.py` can already read.

Their A-Z index only lists consolidated statutes, so amending Acts are mostly
absent from it even when the page exists. The Apartment Ownership amendments are
a case in point: none of the four are indexed, all four are published. So each
instrument is looked up in the catalogue first, and otherwise the standalone-Act
URL is constructed as `<year>Y0V0C<number>A.html` and probed against the upload
months LankaLaw actually uses.

Coverage is partial and not predictable from the era. No. 45 of 1982 and No. 20
of 1976 are published; No. 6 of 1951 and No. 32 of 2022 are not. The register
records which, so the gaps are visible rather than assumed.

    uv run python scripts/harvest_lankalaw_amendments.py            # dry run
    uv run python scripts/harvest_lankalaw_amendments.py --apply
"""

from __future__ import annotations

import argparse
import collections
import csv
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "apps/statute-browser"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

CATALOGUE = REPO_ROOT / "data/processed/lankalaw-catalogue.csv"
CHAINS = REPO_ROOT / "data/processed/amendment-chains.csv"
HTML_CHAINS = REPO_ROOT / "data/processed/lankalaw-html-chains.csv"
DESTINATION = REPO_ROOT / "data/legal-sources/library/amendments/html"
REPORT = REPO_ROOT / "data/processed/lankalaw-amendment-downloads.csv"

BASE = "https://lankalaw.net/wp-content/uploads/{path}/{act_id}.html"
UPLOAD_PATHS = ("2025/02", "2025/03", "2025/01", "2024/12", "2024/03")
STANDALONE_ID = re.compile(r"/(\d{4})Y0V0C(\d+)A(?:-\d+)?\.html")
TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
USER_AGENT = "Mozilla/5.0 (compatible; draftly-research/1.0; legal corpus build)"


def slugify(text: str) -> str:
    slug = text.lower().replace("&", " and ").replace("'", "")
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", slug)).strip("-")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def wanted() -> dict[tuple[int, int], set[str]]:
    """Every amending instrument known for a curriculum statute, and what it amends."""
    from build_rubrik import curriculum_amendments
    from build_statute_tiers import match_curriculum

    primary = {e["source_id"] for e in match_curriculum()[0]}
    titles = {r["source_id"]: r["statute"] for r in read_csv(CHAINS)}
    titles |= {r["source_id"]: r["statute"] for r in read_csv(HTML_CHAINS)}

    instruments: dict[tuple[int, int], set[str]] = collections.defaultdict(set)
    for rows in (read_csv(CHAINS), read_csv(HTML_CHAINS)):
        for row in rows:
            if row["role"] != "amending" or row["source_id"] not in primary:
                continue
            key = (int(row["instrument_no"]), int(row["instrument_year"]))
            instruments[key].add(row["statute"])
    for source_id, listed in curriculum_amendments().items():
        if source_id not in primary:
            continue
        for key in listed:
            instruments[key].add(titles.get(source_id, source_id))
    return instruments


def catalogue_urls() -> dict[tuple[int, int], str]:
    found = {}
    for row in read_csv(CATALOGUE):
        match = STANDALONE_ID.search(row["url"])
        if match:
            found[(int(match.group(2)), int(match.group(1)))] = row["url"]
    return found


def get(url: str) -> bytes | None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except urllib.error.HTTPError:
        return None
    except Exception:  # noqa: BLE001 - a transport failure is a miss, not a crash
        return None


def locate(key: tuple[int, int], catalogue: dict) -> tuple[str, bytes] | None:
    if key in catalogue:
        payload = get(catalogue[key])
        if payload:
            return catalogue[key], payload
    act_id = f"{key[1]}Y0V0C{key[0]}A"
    for path in UPLOAD_PATHS:
        url = BASE.format(path=path, act_id=act_id)
        payload = get(url)
        if payload:
            return url, payload
        time.sleep(0.15)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    instruments = wanted()
    catalogue = catalogue_urls()
    already = {
        tuple(int(p) for p in match.groups())
        for file in DESTINATION.glob("*.html")
        if (match := re.match(r"^(\d{1,3})-(\d{4})-", file.stem))
    }
    todo = sorted(set(instruments) - already, key=lambda k: (k[1], k[0]))

    print(f"{len(instruments)} amending instruments known for curriculum statutes")
    print(f"  {len(set(instruments) & set(catalogue))} appear in the LankaLaw catalogue")
    print(f"  {len(already)} already fetched, {len(todo)} to look up")
    if not args.apply:
        print("\nDry run. Re-run with --apply to probe and download.")
        return 0

    DESTINATION.mkdir(parents=True, exist_ok=True)
    results = []
    for index, key in enumerate(todo, 1):
        if args.limit and index > args.limit:
            break
        number, year = key
        located = locate(key, catalogue)
        row = {
            "instrument_no": number,
            "instrument_year": year,
            "amends": "; ".join(sorted(instruments[key])),
            "url": "",
            "title": "",
            "filename": "",
            "outcome": "",
        }
        if not located:
            row["outcome"] = "not published as HTML"
            results.append(row)
            print(f"  [{index}/{len(todo)}] No. {number} of {year}: not published")
            continue

        url, payload = located
        page = payload.decode("utf-8", errors="replace")
        match = TITLE.search(page)
        title = re.sub(r"\s+", " ", match.group(1)).strip() if match else ""
        name = f"{number}-{year}-{slugify(title) or 'untitled'}.html"
        (DESTINATION / name).write_bytes(payload)
        row |= {"url": url, "title": title, "filename": name, "outcome": "downloaded"}
        results.append(row)
        print(f"  [{index}/{len(todo)}] {name}  {len(payload) // 1024} KB  {title[:44]}")
        time.sleep(0.3)

    with REPORT.open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "# LankaLaw HTML lookup for each amending Act of a curriculum statute.\n"
            "# Coverage is partial and does not follow the era. status=unverified:\n"
            "# the title below is the page's own, matched on Act number and year only.\n"
        )
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    got = sum(1 for r in results if r["outcome"] == "downloaded")
    print(f"\ndownloaded {got} of {len(results)}; wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
