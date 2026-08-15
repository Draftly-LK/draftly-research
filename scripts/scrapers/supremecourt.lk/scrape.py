"""Download every Supreme Court judgment PDF from supremecourt.lk, year by year.

https://supremecourt.lk/judgements/?case_year=<YYYY> server-renders the entire
filtered table in the initial HTML — the visible DataTable only paginates
client-side over rows already in the DOM — so one page load per year is
enough to see every judgment for that year.

Camoufox drives navigation (per project instruction, and as a hedge against
future JS/anti-bot changes); each PDF is then fetched through the same
browser context's request API, which reuses the browser's cookies without
paying for a full page render per file.

Output:
  data/supremecourt.lk/<year>/<filename>.pdf
  data/supremecourt.lk/manifest.csv   (merged/resumable across runs)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

from camoufox.sync_api import Camoufox
from lxml import html as lxml_html

BASE_URL = "https://supremecourt.lk/judgements/"
REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "data" / "supremecourt.lk"
MANIFEST = OUT_DIR / "manifest.csv"
PROGRESS_LOG = REPO_ROOT / "tmp" / "supremecourt-lk" / "progress.log"

FIELDS = [
    "year", "date", "case_no", "parties", "judge", "pdf_url", "filename",
    "status", "sha256", "downloaded_at",
]


def log(message: str) -> None:
    print(message, flush=True)
    PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(message + "\n")


def discover_years(page) -> list[int]:
    page.goto(BASE_URL, wait_until="domcontentloaded")
    tree = lxml_html.fromstring(page.content())
    years = []
    for option in tree.xpath('//select[@name="case_year"]/option'):
        value = (option.get("value") or "").strip()
        if value.isdigit():
            years.append(int(value))
    return sorted(set(years), reverse=True)


def parse_year_page(html: str, year: int) -> list[dict]:
    tree = lxml_html.fromstring(html)
    rows = []
    for tr in tree.xpath('//table[contains(@id, "jmFE_")]/tbody/tr'):
        cells = tr.xpath("./td")
        if len(cells) < 4:
            continue
        date = "".join(cells[0].itertext()).strip()
        case_no = "".join(cells[1].itertext()).strip()
        full_text = cells[2].xpath('.//span[contains(@class, "full-text")]')
        parties_source = full_text[0] if full_text else cells[2]
        parties = " ".join("".join(parties_source.itertext()).split())
        seen_urls: set[str] = set()
        for judge_line in cells[3].xpath('.//div[contains(@class, "jm-fe-judge-line")]'):
            judge = "".join(judge_line.xpath('.//span[contains(@class, "jm-fe-judge-badge")]/text()')).strip()
            for link in judge_line.xpath('.//a[contains(@class, "jm-fe-dl-btn-sm")]/@href'):
                url = link.strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                rows.append({
                    "year": year, "date": date, "case_no": case_no,
                    "parties": parties, "judge": judge, "pdf_url": url,
                    "filename": url.rsplit("/", 1)[-1],
                })
    return rows


def load_manifest() -> dict[tuple[str, str], dict]:
    merged: dict[tuple[str, str], dict] = {}
    if MANIFEST.exists():
        with MANIFEST.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                merged[(row["year"], row["filename"])] = row
    return merged


def save_manifest(merged: dict[tuple[str, str], dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(merged.values())


def download_year(page, year: int, rows: list[dict], merged: dict, delay: float, force: bool) -> None:
    year_dir = OUT_DIR / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    for i, row in enumerate(rows, 1):
        key = (str(year), row["filename"])
        dest = year_dir / row["filename"]
        record = dict(row)
        record["year"] = str(year)
        if dest.exists() and not force:
            record["status"] = "skipped-exists"
            record["sha256"] = merged.get(key, {}).get("sha256", "")
            record["downloaded_at"] = merged.get(key, {}).get("downloaded_at", "")
            merged[key] = {field: str(record.get(field, "")) for field in FIELDS}
            continue
        time.sleep(delay)
        try:
            response = page.context.request.get(row["pdf_url"])
            if not response.ok:
                log(f"  [warn] {row['pdf_url']}: HTTP {response.status}")
                record["status"] = f"error:http-{response.status}"
            else:
                body = response.body()
                dest.write_bytes(body)
                record["status"] = "ok"
                record["sha256"] = hashlib.sha256(body).hexdigest()
                record["downloaded_at"] = datetime.now(timezone.utc).isoformat()
        except Exception as exc:  # noqa: BLE001
            log(f"  [warn] {row['pdf_url']}: {exc}")
            record["status"] = f"error:{exc}"
        merged[key] = {field: str(record.get(field, "")) for field in FIELDS}
        if i % 50 == 0:
            log(f"  {year}: {i}/{len(rows)}")
            save_manifest(merged)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", action="append", type=int, help="Scope to one year; repeatable.")
    parser.add_argument("--years", nargs=2, type=int, metavar=("START", "END"), help="Inclusive year range.")
    parser.add_argument("--limit", type=int, help="Cap PDFs downloaded per year (smoke testing).")
    parser.add_argument("--delay", type=float, default=0.4, help="Seconds between PDF fetches.")
    parser.add_argument("--headed", action="store_true", help="Run Camoufox with a visible browser.")
    parser.add_argument("--force", action="store_true", help="Re-download even if the file already exists.")
    args = parser.parse_args()

    merged = load_manifest()

    with Camoufox(headless=not args.headed) as browser:
        page = browser.new_page()

        if args.year:
            years = sorted(set(args.year), reverse=True)
        elif args.years:
            start, end = args.years
            years = list(range(max(start, end), min(start, end) - 1, -1))
        else:
            years = discover_years(page)
            log(f"Discovered {len(years)} years: {years}")

        total_ok = total_skipped = total_err = 0
        for year in years:
            url = f"{BASE_URL}?case_year={year}&month=&judgment_by="
            page.goto(url, wait_until="domcontentloaded")
            rows = parse_year_page(page.content(), year)
            if args.limit:
                rows = rows[: args.limit]
            log(f"== {year}: {len(rows)} judgment PDFs ==")
            download_year(page, year, rows, merged, args.delay, args.force)
            save_manifest(merged)
            year_records = [v for k, v in merged.items() if k[0] == str(year)]
            total_ok += sum(1 for r in year_records if r["status"] == "ok")
            total_skipped += sum(1 for r in year_records if r["status"] == "skipped-exists")
            total_err += sum(1 for r in year_records if r["status"].startswith("error"))

    save_manifest(merged)
    log(f"DONE downloaded={total_ok} skipped={total_skipped} errors={total_err}")


if __name__ == "__main__":
    main()
