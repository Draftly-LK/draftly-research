"""The grounding gate. A rule is only accepted if its supporting_quote appears
verbatim in the judgment and its statute reference resolves against the closed
registry. This is what keeps a cheap model honest.
"""

from __future__ import annotations

import re

import catalogue


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def quote_in_text(quote: str, judgment_text: str, min_len: int = 15) -> bool:
    """Verbatim (whitespace-insensitive) substring check."""
    q = _norm(quote)
    if len(q) < min_len:
        return False
    return q in _norm(judgment_text)


def check_section(ref: str) -> tuple[str | None, str]:
    """Return (normalized_ref | None, status). status ∈ {ok, ok-unchecked, bad-source,
    section-not-found, none}."""
    if not ref or str(ref).lower() in ("null", "none", ""):
        return None, "none"
    sid, sec = catalogue.parse_ref(ref)
    if not sid or not catalogue.valid_source(sid):
        return None, "bad-source"
    if not sec:
        return sid, "ok"  # statute-level only
    exists = catalogue.section_exists(sid, sec)
    norm = f"{sid}-s{sec}"
    if exists is False:
        return norm, "section-not-found"
    return norm, ("ok" if exists else "ok-unchecked")


def validate_rule(rule: dict, judgment_text: str) -> tuple[bool, dict, str]:
    """Return (accepted, cleaned_rule, reject_reason)."""
    if not isinstance(rule, dict) or not rule.get("statement"):
        return False, {}, "no-statement"
    quote = rule.get("supporting_quote", "")
    if not quote_in_text(quote, judgment_text):
        return False, {}, "quote-not-found"
    sec_ref, sec_status = check_section(rule.get("statute_section"))
    cleaned = {
        "statement": re.sub(r"\s+", " ", rule["statement"]).strip(),
        "supporting_quote": re.sub(r"\s+", " ", quote).strip(),
        "statute_section": sec_ref or "",
        "section_status": sec_status,
        "scope": rule.get("scope", "") if rule.get("scope") in ("ratio", "obiter", "fact-specific") else "",
        "confidence": rule.get("confidence", "") if rule.get("confidence") in ("high", "medium", "low") else "medium",
    }
    return True, cleaned, ""
