"""Download every judgment listed in year-cases.json.

Files are stored as data/commonlii/raw/<db>/<year>/<case-number>.<extension>.
The run is resumable: valid existing HTML and PDF files are skipped.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from pathlib import Path

import fetch as F

HERE = Path(__file__).resolve().parent
RAW_ROOT = HERE.parents[1] / "data" / "commonlii" / "raw"
PROGRESS_NAME = "download-progress.json"
# cloudscraper solves Cloudflare's JS challenge in-process (via js2py) before
# a request ever hits the network. That solving step ignores requests'
# `timeout=` entirely, so a hard challenge variant can hang forever with no
# exception raised -- this happened live, after ~1500 requests on one
# session. HARD_TIMEOUT_S bounds the whole call from outside, in a daemon
# thread, so a hang can never block the run for more than this long.
HARD_TIMEOUT_S = 90


def call_with_hard_timeout(func, *args, hard_timeout_s=HARD_TIMEOUT_S, **kwargs):
    # NOTE: named hard_timeout_s, not timeout -- callers pass their own
    # `timeout=` for the wrapped function itself (e.g. requests' own
    # per-socket timeout); reusing the same name would silently swallow it
    # into *this* wrapper's budget instead of forwarding it in kwargs.
    outcome: dict = {}

    def run():
        try:
            outcome["value"] = func(*args, **kwargs)
        except BaseException as e:  # noqa: BLE001
            outcome["error"] = e

    # daemon=True: if func never returns, this thread must not block process
    # exit -- Python threads cannot be forcibly killed.
    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(hard_timeout_s)
    if t.is_alive():
        raise TimeoutError(
            f"{getattr(func, '__name__', func)} did not return within "
            f"{hard_timeout_s}s (likely cloudscraper's challenge-solver hanging)"
        )
    if "error" in outcome:
        raise outcome["error"]
    return outcome["value"]


def valid_file(path: Path, file_type: str) -> bool:
    if not path.is_file() or path.stat().st_size < 100:
        return False
    head = path.read_bytes()[:1024].lstrip()
    if file_type == "pdf":
        return head.startswith(b"%PDF-")
    lower = head.lower()
    return b"<html" in lower or b"<!doctype html" in lower


def write_progress(output: Path, payload: dict) -> None:
    (output / PROGRESS_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def download(manifest_path: Path, output: Path, delay_s: float, db: str,
             year_min: int | None = None, year_max: int | None = None,
             limit: int = 0) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)

    entries = []
    for year, cases in manifest["years"].items():
        if year_min is not None and int(year) < year_min:
            continue
        if year_max is not None and int(year) > year_max:
            continue
        for case in cases:
            entries.append((year, case))
    # The user explicitly requested these PDF years. Fetch them first.
    entries.sort(key=lambda item: (
        0 if item[0] in {"2011", "2012"} else 1,
        int(item[0]),
        int(item[1]["case_number"]),
    ))
    if limit:
        entries = entries[:limit]
        print(f"--limit {limit}: downloading only the first {len(entries)}")

    session = F.make_download_session()
    downloaded = skipped = 0
    failures: list[dict] = []
    last_request = 0.0
    primed_pdf_years: dict[str, str] = {}

    for position, (year, case) in enumerate(entries, 1):
        file_type = case["file_type"]
        destination = output / year / f"{case['case_number']}.{file_type}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if valid_file(destination, file_type):
            skipped += 1
            continue

        gap = time.monotonic() - last_request
        if gap < delay_s:
            time.sleep(delay_s - gap)
        last_request = time.monotonic()

        try:
            headers = {}
            if year not in primed_pdf_years:
                primed_pdf_years[year] = call_with_hard_timeout(
                    F.prime_download_year, session, db, int(year)
                )
            if file_type == "pdf":
                headers["Referer"] = primed_pdf_years[year]
            else:
                headers["Referer"] = primed_pdf_years[year]
            response = call_with_hard_timeout(
                session.get, case["url"], headers=headers, timeout=F.TIMEOUT_S
            )
            response.raise_for_status()
            content = response.content
            part = destination.with_suffix(destination.suffix + ".part")
            part.write_bytes(content)
            if not valid_file(part, file_type):
                part.unlink(missing_ok=True)
                raise ValueError(
                    f"response is not a valid {file_type.upper()} file"
                )
            part.replace(destination)
            downloaded += 1
            print(
                f"[{position}/{len(entries)}] {year}/{destination.name} "
                f"{len(content):,} bytes",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            failures.append({
                "year": int(year),
                "case_number": case["case_number"],
                "url": case["url"],
                "error": f"{type(exc).__name__}: {exc}",
            })
            print(
                f"[{position}/{len(entries)}] FAILED {case['url']}: {exc}",
                flush=True,
            )
            if isinstance(exc, TimeoutError):
                # The stuck request is abandoned (its thread leaks, harmless
                # at process exit), but the session that produced it may be
                # in a bad state -- start the next request clean rather than
                # risk hanging again on the same session.
                print("  rebuilding session after a hard-timeout", flush=True)
                session = F.make_download_session()
                primed_pdf_years.clear()

        write_progress(output, {
            "manifest": str(manifest_path),
            "total": len(entries),
            "downloaded_this_run": downloaded,
            "skipped_existing": skipped,
            "processed": position,
            "failures": failures,
        })

    write_progress(output, {
        "manifest": str(manifest_path),
        "total": len(entries),
        "downloaded_this_run": downloaded,
        "skipped_existing": skipped,
        "processed": len(entries),
        "failures": failures,
        "complete": not failures,
    })
    print(
        f"complete: {downloaded} downloaded, {skipped} already present, "
        f"{len(failures)} failed",
        flush=True,
    )
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="LKSC",
                        help="CommonLII database code, e.g. LKSC or LKCA")
    parser.add_argument("--manifest", type=Path, default=None,
                        help="defaults to year-cases-<db>.json")
    parser.add_argument("--output", type=Path, default=None,
                        help="defaults to data/commonlii/raw/<db>")
    parser.add_argument("--delay", type=float, default=F.DELAY_S)
    parser.add_argument("--year-min", type=int, default=None,
                        help="only download cases from this year onward")
    parser.add_argument("--year-max", type=int, default=None,
                        help="only download cases up to and including this year "
                             "-- for downloading in blocks instead of all at once")
    parser.add_argument("--limit", type=int, default=0,
                        help="download only the first N cases (0 = all) -- for "
                             "a quick test before a full run")
    args = parser.parse_args()
    manifest = (args.manifest or (HERE / f"year-cases-{args.db}.json")).resolve()
    output = (args.output or (RAW_ROOT / args.db)).resolve()
    try:
        return download(manifest, output, args.delay, args.db,
                         year_min=args.year_min, year_max=args.year_max,
                         limit=args.limit)
    except F.TransportUnavailable as e:
        print(f"\n  STOPPED: {e}")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
