# supremecourt.lk scraper

Downloads every judgment PDF from <https://supremecourt.lk/judgements/>,
organized by decision year. Unlike `scripts/harvest_courts_caselaw.py` (which
keeps only conveyancing-matched text extracts), this scraper keeps the PDFs
themselves, unfiltered.

## Why Camoufox

`?case_year=<YYYY>` server-renders the full year's table in one page load —
the visible table only paginates client-side over rows already in the DOM.
Camoufox drives that page load; each PDF is then fetched through the same
browser context's request API (cookie-consistent, but HTTP-only per call —
no full render per file).

## Usage

```powershell
# Smoke test: one year, five PDFs
uv run python scripts/scrapers/supremecourt.lk/scrape.py --year 2026 --limit 5

# A year range
uv run python scripts/scrapers/supremecourt.lk/scrape.py --years 2020 2024

# Full site (all years discovered from the site's own filter dropdown)
uv run python scripts/scrapers/supremecourt.lk/scrape.py

# Debug with a visible browser
uv run python scripts/scrapers/supremecourt.lk/scrape.py --year 2026 --limit 3 --headed
```

Flags: `--year YYYY` (repeatable), `--years START END`, `--limit N` (cap per
year), `--delay SECONDS` (default 0.4, between PDF fetches), `--headed`,
`--force` (re-download even if the file exists).

## Output

```text
data/supremecourt.lk/
  <year>/<filename>.pdf
  manifest.csv   # year, date, case_no, parties, judge, pdf_url, filename, status, sha256, downloaded_at
```

The PDFs and `manifest.csv` under `data/supremecourt.lk/` are tracked.

**Resumable and idempotent.** A file that already exists on disk is skipped
(`status=skipped-exists` in the manifest) unless `--force` is passed; a
partial or interrupted run can just be re-invoked with the same arguments.
Progress is logged to stdout and to `tmp/supremecourt-lk/progress.log`.
