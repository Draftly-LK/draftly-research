"""Shared paths and helpers for the statutory-qa-v1 benchmark pipeline.

Nothing here reads the law, calls a model or touches the network. Every
artifact produced under data/evaluvation/statutory-qa-v1/ is status=unverified
until a lawyer signs it off.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = ROOT / "data" / "evaluvation" / "statutory-qa-v1"
CORPUS_DIR = DATASET_DIR / "corpus"
CANDIDATES_DIR = DATASET_DIR / "candidates"
RESERVED_DIR = DATASET_DIR / "reserved"
ANNOTATIONS_DIR = DATASET_DIR / "annotations"
MATTERS_DIR = ANNOTATIONS_DIR / "matters"
REVIEW_DIR = DATASET_DIR / "review"
BENCHMARK_DIR = DATASET_DIR / "benchmark"
AUDITS_DIR = DATASET_DIR / "audits"
EXPERIMENTS_DIR = DATASET_DIR / "experiments"
SCHEMAS_DIR = DATASET_DIR / "schemas"
MANIFESTS_DIR = DATASET_DIR / "manifests"
PROMPTS_DIR = ROOT / "scripts" / "statutory-qa" / "prompts"

ATOMIC_DIR = ROOT / "data" / "evaluvation" / "parsed-pastpapers" / "atomic"
ATOMIC_QUESTIONS = ATOMIC_DIR / "atomic-questions.jsonl"
ATOMIC_CLASSIFICATIONS = ATOMIC_DIR / "atomic-classifications.jsonl"
PAPERS_CSV = ROOT / "data" / "evaluvation" / "papers.csv"
FINALIZED_DIR = ROOT / "data" / "legal-sources" / "library" / "finalized"

RUN_ID = "statutory-qa-v1"


# --------------------------------------------------------------------------- #
# text
# --------------------------------------------------------------------------- #

def normalize_ws(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def excerpt_in(excerpt: str, body: str) -> bool:
    """True when `excerpt` is a verbatim substring of `body`, whitespace and
    quote style normalised on both sides."""
    e = normalize_ws(excerpt).casefold()
    b = normalize_ws(body).casefold()
    return bool(e) and e in b


# --------------------------------------------------------------------------- #
# hashing / io
# --------------------------------------------------------------------------- #

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _atomic_write(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_json(path: Path, obj: Any) -> None:
    _atomic_write(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path: Path, rows: Iterable[Any]) -> None:
    _atomic_write(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def write_text(path: Path, text: str) -> None:
    _atomic_write(path, text)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def git_commit() -> str | None:
    head = ROOT / ".git" / "HEAD"
    try:
        ref = head.read_text().strip()
        if ref.startswith("ref:"):
            return (ROOT / ".git" / ref.split(" ", 1)[1]).read_text().strip()
        return ref
    except OSError:
        return None


# --------------------------------------------------------------------------- #
# exam session -> matter reference date
# --------------------------------------------------------------------------- #

_MONTHS = {"JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4, "MAY": 5, "JUNE": 6,
           "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11,
           "DECEMBER": 12}


def paper_sessions() -> dict[int, dict[str, Any]]:
    """paper_no -> {session, year, month, date}. The *earliest* session named
    on a paper is used when two are printed, so a provision is only treated as
    in force if it was in force at the earliest possible exam date."""
    import csv

    out: dict[int, dict[str, Any]] = {}
    with open(PAPERS_CSV, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            session = (row.get("session") or "").strip()
            best = None
            for part in session.split("/"):
                m = re.search(r"([A-Z]+)\s+(\d{4})", part.strip().upper())
                if not m or m.group(1) not in _MONTHS:
                    continue
                cand = (int(m.group(2)), _MONTHS[m.group(1)])
                if best is None or cand < best:
                    best = cand
            year, month = best if best else (None, None)
            out[int(row["paper_no"])] = {
                "session": session,
                "year": year,
                "month": month,
                "date": f"{year:04d}-{month:02d}" if year else None,
            }
    return out
