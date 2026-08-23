"""Download every amending instrument known for a statute, from the Act archive.

This used to read one source, the header block of the consolidated PDF, and so
never attempted an instrument the corpus knew about only from somewhere else.
RUBRIK.md reported those as "no source located" when the truth was that nobody
had looked. It now asks for the union of all four sources the register uses:

    chain       data/processed/amendment-chains.csv, from the PDF header block
    html        data/processed/lankalaw-html-chains.csv, from the HTML edition
    curriculum  the Amendment/s column of the course statute tables
    marker      data/processed/actions.csv, from inline `[s., Act of Year]`

Whatever exists in the `nuuuwan/lk-acts-acts` dataset (parliament.lk Acts,
1950-2025) is fetched into `data/legal-sources/library/amendments`, named
`<no>-<year>-<slug>.pdf` to match the statutes folder.

What it cannot get, and why:

  * Anything before 1950. The dataset starts there, and the sources between them
    name well over a hundred distinct pre-1950 Ordinances. Those exist only
    inside the Legislative Enactments volumes.
  * Most National State Assembly *Laws* (1972-1977). The archive holds Acts.

Files are written only after the response is confirmed to be a PDF, so a 404
page cannot land in the library. Re-running skips what is already held, by
(number, year), so it is safe to repeat.

    uv run python scripts/download_amendment_chain_acts.py            # dry run
    uv run python scripts/download_amendment_chain_acts.py --apply
    uv run python scripts/download_amendment_chain_acts.py --chains-only
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "apps/statute-browser"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

CHAINS = REPO_ROOT / "data/processed/amendment-chains.csv"
HTML_CHAINS = REPO_ROOT / "data/processed/lankalaw-html-chains.csv"
ACTIONS = REPO_ROOT / "data/processed/actions.csv"
REGISTRY = REPO_ROOT / "data/legal-sources/manifests/source-registry.csv"
AMENDMENTS = REPO_ROOT / "data/legal-sources/library/amendments"
REPORT = REPO_ROOT / "data/processed/amendment-chain-downloads.csv"
PARQUET_URL = "https://huggingface.co/api/datasets/nuuuwan/lk-acts-acts/parquet/default/train/0.parquet"

NUMBER_YEAR_IN_NAME = re.compile(r"(?:^|-)(\d{1,3})-(1[89]\d{2}|20\d{2})(?:-|$)")
USER_AGENT = "draftly-research/1.0 (legal corpus build; contact via repository)"

# The catalogue entry points at Income Tax (Amendment) Act, No. 11 of 1955,
# not the Town and Country Planning instrument named by its metadata.
KNOWN_CONTENT_MISMATCHES = {(10, 1955)}


def slugify(text: str) -> str:
    slug = text.lower().replace("&", " and ").replace("'", "")
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", slug)).strip("-")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def read_chains() -> list[dict[str, str]]:
    return [r for r in read_csv(CHAINS) if r["role"] == "amending"]


def requests(chains_only: bool) -> list[tuple[tuple[int, int], str, str]]:
    """((number, year), statute title, source_id) for every instrument wanted.

    One row per (instrument, statute) pair and per source; the caller collapses
    them. Which source named it is not recorded here -- the register already
    tracks that, and this only needs to know what to ask the archive for.
    """
    asks: list[tuple[tuple[int, int], str, str]] = []
    for row in read_chains():
        asks.append(
            (
                (int(row["instrument_no"]), int(row["instrument_year"])),
                row["statute"],
                row["source_id"],
            )
        )
    if chains_only:
        return asks

    titles = {r["source_id"]: r["official_title"] for r in read_csv(REGISTRY)}
    titles |= {r["source_id"]: r["statute"] for r in read_chains()}

    for row in read_csv(HTML_CHAINS):
        if row["role"] != "amending":
            continue
        asks.append(
            (
                (int(row["instrument_no"]), int(row["instrument_year"])),
                row["statute"],
                row["source_id"],
            )
        )
    for row in read_csv(ACTIONS):
        if not row["amending_act_no"].isdigit() or not row["amending_year"].isdigit():
            continue
        key = (int(row["amending_act_no"]), int(row["amending_year"]))
        # Several statutes reached only through markers are absent from the
        # registry, so the marker's own statute name is the better label.
        name = titles.get(row["source_id"]) or row["statute_name"].title() or row["source_id"]
        asks.append((key, name, row["source_id"]))

    try:
        from build_rubrik import curriculum_amendments
    except Exception as error:  # noqa: BLE001 - the other three sources still stand
        print(f"  (curriculum list unavailable: {type(error).__name__}; skipping it)")
        return asks
    for source_id, listed in curriculum_amendments().items():
        for key in listed:
            asks.append((key, titles.get(source_id, source_id), source_id))
    return asks


def already_held() -> dict[tuple[int, int], str]:
    """Every (number, year) the amendments folder already has, from filenames."""
    held = {}
    for file in list(AMENDMENTS.glob("*.pdf")) + list(AMENDMENTS.glob("incoming/*.pdf")):
        for number, year in NUMBER_YEAR_IN_NAME.findall(file.stem):
            held[(int(number), int(year))] = file.name
    return held


def fetch(url: str) -> bytes | None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
    # A missing Act returns an HTML error page with a 200, so check the magic.
    return payload if payload[:5] == b"%PDF-" else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="perform the downloads")
    parser.add_argument("--limit", type=int, help="stop after this many downloads")
    parser.add_argument(
        "--chains-only",
        action="store_true",
        help="ask only for instruments named in a PDF header block, as this "
             "script did before it read the other three sources",
    )
    args = parser.parse_args()

    dataset = pd.read_parquet(PARQUET_URL)
    dataset["n"] = pd.to_numeric(dataset["act_sub_num"], errors="coerce")
    catalogue = {
        (int(row.n), int(row.act_year)): (row.act_source_url, row.act_description)
        for row in dataset.itertuples()
        if pd.notna(row.n)
    }

    held = already_held()
    wanted: dict[tuple[int, int], dict] = {}
    for key, statute, source_id in requests(args.chains_only):
        entry = wanted.setdefault(
            key, {"statutes": [], "source_ids": [], "url": None, "description": None}
        )
        entry["statutes"].append(statute)
        entry["source_ids"].append(source_id)
        if key in catalogue:
            entry["url"], entry["description"] = catalogue[key]

    mismatched = {k: v for k, v in wanted.items() if k in KNOWN_CONTENT_MISMATCHES}
    available = {
        k: v for k, v in wanted.items() if v["url"] and k not in KNOWN_CONTENT_MISMATCHES
    }
    missing = {k: v for k, v in wanted.items() if not v["url"]}
    todo = {k: v for k, v in available.items() if k not in held}
    skipped = {k: v for k, v in available.items() if k in held}

    scope = "chains" if args.chains_only else "all four sources"
    print(f"{scope} name {len(wanted)} distinct amending instruments")
    print(f"  {len(available)} available in the dataset, {len(missing)} not")
    print(f"  {len(skipped)} already held, {len(todo)} to download")
    if not args.apply:
        for key, entry in sorted(todo.items(), key=lambda kv: (kv[0][1], kv[0][0]))[:10]:
            print(f"    No. {key[0]} of {key[1]}  {entry['description'][:50]}")
        print(f"    ... and {max(0, len(todo) - 10)} more")
        print("\nDry run. Re-run with --apply to download.")
        return 0

    results = []
    for index, (key, entry) in enumerate(sorted(todo.items(), key=lambda kv: (kv[0][1], kv[0][0])), 1):
        if args.limit and index > args.limit:
            break
        number, year = key
        name = f"{number}-{year}-{slugify(entry['description'])}.pdf"
        target = AMENDMENTS / name
        try:
            payload = fetch(entry["url"])
        except Exception as error:  # noqa: BLE001 - report and continue the batch
            print(f"  [{index}/{len(todo)}] No. {number} of {year}: {type(error).__name__} {error}")
            results.append({**_row(key, entry, name), "outcome": f"error: {type(error).__name__}", "sha256": "", "bytes": 0})
            continue
        if payload is None:
            print(f"  [{index}/{len(todo)}] No. {number} of {year}: not a PDF, skipped")
            results.append({**_row(key, entry, name), "outcome": "not-a-pdf", "sha256": "", "bytes": 0})
            continue
        target.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        print(f"  [{index}/{len(todo)}] {name}  {len(payload) // 1024} KB")
        results.append({**_row(key, entry, name), "outcome": "downloaded", "sha256": digest, "bytes": len(payload)})
        time.sleep(0.4)

    for key, entry in sorted(mismatched.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        results.append(
            {
                **_row(key, entry, ""),
                "outcome": "content-mismatch-title-page",
                "sha256": "",
                "bytes": 0,
            }
        )
    for key, entry in sorted(missing.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        results.append(
            {
                **_row(key, entry, ""),
                "outcome": "not-in-dataset (pre-1950, or a Law rather than an Act)",
                "sha256": "",
                "bytes": 0,
            }
        )
    for key, entry in sorted(skipped.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        results.append({**_row(key, entry, held[key]), "outcome": "already-held", "sha256": "", "bytes": 0})

    with REPORT.open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "# Outcome per amending instrument known for a statute, from any of the four\n"
            "# sources the register reads: chain, html, curriculum, marker.\n"
            "# Generated by scripts/download_amendment_chain_acts.py. status=unverified:\n"
            "# a match is on Act number and year, and the file's own title page has not\n"
            "# been read back to confirm it.\n"
        )
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    downloaded = sum(1 for r in results if r["outcome"] == "downloaded")
    print(f"\ndownloaded {downloaded} files, wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


def _row(key: tuple[int, int], entry: dict, filename: str) -> dict:
    return {
        "instrument_no": key[0],
        "instrument_year": key[1],
        "description": entry["description"] or "",
        "amends": "; ".join(dict.fromkeys(entry["statutes"])),
        "source_ids": ";".join(dict.fromkeys(entry["source_ids"])),
        "url": entry["url"] or "",
        "filename": filename,
    }


if __name__ == "__main__":
    raise SystemExit(main())
