"""Download every judgment listed in year-cases.json.

Files are stored as data/commonlii/raw/LKSC/<year>/<case-number>.<extension>.
The run is resumable: valid existing HTML and PDF files are skipped.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import fetch as F

HERE = Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE / "year-cases.json"
DEFAULT_OUTPUT = HERE.parents[1] / "data" / "commonlii" / "raw" / "LKSC"
PROGRESS_NAME = "download-progress.json"


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


def download(manifest_path: Path, output: Path, delay_s: float) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)

    entries = []
    for year, cases in manifest["years"].items():
        for case in cases:
            entries.append((year, case))
    # The user explicitly requested these PDF years. Fetch them first.
    entries.sort(key=lambda item: (
        0 if item[0] in {"2011", "2012"} else 1,
        int(item[0]),
        int(item[1]["case_number"]),
    ))

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
                primed_pdf_years[year] = F.prime_download_year(
                    session, "LKSC", int(year)
                )
            if file_type == "pdf":
                headers["Referer"] = primed_pdf_years[year]
            else:
                headers["Referer"] = primed_pdf_years[year]
            response = session.get(
                case["url"], headers=headers, timeout=F.TIMEOUT_S
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
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--delay", type=float, default=F.DELAY_S)
    args = parser.parse_args()
    return download(args.manifest.resolve(), args.output.resolve(), args.delay)


if __name__ == "__main__":
    raise SystemExit(main())
