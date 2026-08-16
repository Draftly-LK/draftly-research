"""Paths, models, and spend caps for the OCR benchmark.

Shape follows scripts/case-law-information-extraction/config.py: resolve the repo
root from __file__, load .env, expose path constants, mkdir the writable ones at
import. Env var names match notebooks/05_courts_judgment_extraction.ipynb so a
single .env drives both.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

load_dotenv(ROOT / ".env")

# ── Local, gitignored working directories ────────────────────────────────────
# cases/ holds one directory per matter. Splitting by matter matters: pages from
# the same transaction must never land on both sides of a train/test split, so
# the matter is the unit everything downstream groups by.
CASES = HERE / "cases"
RENDERS = HERE / "renders"
RUNS = HERE / "runs"
LABELS = HERE / "labels"
# Tracked: aggregates only, never field values.
REPORTS = HERE / "reports"
SCHEMAS = HERE / "schemas"

RUNS_YAML = HERE / "runs.yaml"
USAGE_JSON = RUNS / "gemini-usage.json"

for _d in (CASES, RENDERS, RUNS, LABELS, REPORTS):
    _d.mkdir(parents=True, exist_ok=True)

# ── Inputs ───────────────────────────────────────────────────────────────────
# Every matter directory under cases/. Point somewhere else with
# DRAFTLY_OCR_BENCH_INPUTS (useful for reading a bundle in place instead of
# copying client documents).
INPUTS = Path(os.environ.get("DRAFTLY_OCR_BENCH_INPUTS", str(CASES)))

DOC_EXTENSIONS = {".pdf", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def case_dirs() -> list[Path]:
    """Matter directories, sorted. A flat folder of documents counts as one matter."""
    if not INPUTS.is_dir():
        return []
    subdirs = [
        d for d in sorted(INPUTS.iterdir())
        if d.is_dir() and any(f.suffix.lower() in DOC_EXTENSIONS for f in d.iterdir())
    ]
    if subdirs:
        return subdirs
    has_docs = any(f.suffix.lower() in DOC_EXTENSIONS for f in INPUTS.iterdir())
    return [INPUTS] if has_docs else []


def case_documents(case: Path) -> list[Path]:
    return sorted(f for f in case.iterdir() if f.suffix.lower() in DOC_EXTENSIONS)


def expected_fields_path(case: Path) -> Path:
    return case / "expected-fields.json"

# ── Models ───────────────────────────────────────────────────────────────────
# Defaults match draftly-platform/backend/src/platform/config.py so a benchmark
# result transfers to production unchanged.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
CLASSIFY_MODEL = os.environ.get("DRAFTLY_OCR_CLASSIFY_MODEL", "gemini-3.1-flash-lite")
EXTRACT_MODEL = os.environ.get(
    "DRAFTLY_OCR_EXTRACT_MODEL", os.environ.get("DRAFTLY_GEMINI_MODEL", "gemini-3.5-flash")
)

# Platform raster_dpi default. The DPI ablation measures against this baseline.
DEFAULT_DPI = 200
SCHEMA_VERSION = "1.0"
DATASET_ID = "case-001-smoke-26p"

# ── Spend caps ───────────────────────────────────────────────────────────────
# Hard stops, not advisories. runner.py raises when either is crossed.
MAX_CALLS = int(os.environ.get("DRAFTLY_OCR_MAX_CALLS", "400"))
MAX_USD = float(os.environ.get("DRAFTLY_OCR_MAX_USD", "5.00"))

# USD per million tokens. Hand-maintained; verify before quoting a cost.
# Checked 2026-08-14.
PRICE_PER_MTOK: dict[str, dict[str, float]] = {
    "gemini-3.1-flash-lite": {"input": 0.10, "output": 0.40},
    "gemini-3.5-flash": {"input": 0.30, "output": 2.50},
}


def code_commit() -> str:
    """HEAD sha plus a dirty marker, for the run manifest."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        return f"{sha}-dirty" if dirty else sha
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def assert_inputs_private() -> None:
    """Refuse to run if the resolved input directory could be committed.

    These are real client documents. A benchmark that silently reads from a
    tracked path is one `git add -A` away from publishing them.
    """
    if not INPUTS.is_dir() or not case_dirs():
        raise SystemExit(
            f"No case documents found under {INPUTS}\n"
            "Put one directory per matter in ocr-benchmark/cases/, or set "
            "DRAFTLY_OCR_BENCH_INPUTS to a bundle directory."
        )
    try:
        inside = INPUTS.resolve().is_relative_to(ROOT.resolve())
    except AttributeError:  # pragma: no cover - Python < 3.9
        inside = str(INPUTS.resolve()).startswith(str(ROOT.resolve()))
    if not inside:
        return  # Outside this repo entirely; nothing here can commit it.
    probe = case_documents(case_dirs()[0])[0]
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(probe)], cwd=ROOT, capture_output=True
    )
    if result.returncode != 0:
        raise SystemExit(
            f"{INPUTS} is inside the repo but NOT gitignored.\n"
            "Add it to .gitignore before running; these are client documents."
        )
