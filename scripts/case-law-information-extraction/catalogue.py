"""The closed statute catalogue — our unfair advantage over the open-world papers.

Builds the ~57-line allowed-set string handed to the model, resolves/validates a
returned `SRCxxx-sN`, and (best-effort) checks a section number actually appears
in the statute's extracted text.
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache

import config

STATUTE_KINDS = {"statute", "amendment", "gazette", "institution-guide"}


@lru_cache(maxsize=1)
def _registry() -> dict[str, dict]:
    with config.REGISTRY.open(encoding="utf-8-sig") as fh:
        return {r["source_id"]: r for r in csv.DictReader(fh)}


@lru_cache(maxsize=1)
def catalogue_lines() -> str:
    """One line per statutory source, for the prompt's allowed-set."""
    lines = []
    for sid, r in sorted(_registry().items()):
        if r.get("source_type") not in STATUTE_KINDS:
            continue
        no = r.get("act_or_ordinance_no", "").strip()
        yr = r.get("year", "").strip()
        tag = f" No.{no} of {yr}" if no else (f" ({yr})" if yr else "")
        lines.append(f"{sid}\t{r['official_title']}{tag}")
    return "\n".join(lines)


def valid_source(sid: str) -> bool:
    return sid in _registry() and _registry()[sid].get("source_type") in STATUTE_KINDS


def title_of(sid: str) -> str:
    return _registry().get(sid, {}).get("official_title", "")


@lru_cache(maxsize=256)
def _statute_text(sid: str) -> str:
    r = _registry().get(sid, {})
    md = (r.get("local_markdown_path") or "").strip()
    from pathlib import Path
    p = config.ROOT / md if md else None
    if p and p.exists():
        return p.read_text(encoding="utf-8", errors="ignore")
    return ""


def section_exists(sid: str, section: str) -> bool | None:
    """True/False if we can check against the statute text; None if no text available."""
    text = _statute_text(sid)
    if not text:
        return None
    sec = re.escape(str(section).strip())
    return bool(re.search(rf"\b(section|sec\.?|s\.)\s*{sec}\b", text, re.I)
                or re.search(rf"^\s*{sec}\.", text, re.M))


def parse_ref(ref: str) -> tuple[str | None, str | None]:
    """'SRC001-s2' -> ('SRC001','2'); 'SRC001' -> ('SRC001', None); junk -> (None,None)."""
    if not ref or not isinstance(ref, str):
        return None, None
    m = re.match(r"\s*(SRC\d+)(?:[-\s]*s\.?\s*([0-9]+[A-Za-z]?))?\s*$", ref, re.I)
    if not m:
        return None, None
    return m.group(1).upper(), (m.group(2) if m.group(2) else None)
