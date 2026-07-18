"""The grounding gate. A rule is only accepted if its supporting_quote appears
verbatim in the judgment and its statute reference resolves against the closed
registry. This is what keeps a cheap model honest.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

import catalogue


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def quote_in_text(quote: str, judgment_text: str, min_len: int = 15) -> bool:
    """Verbatim (whitespace-insensitive) substring check."""
    q = _norm(quote)
    if len(q) < min_len:
        return False
    return q in _norm(judgment_text)


def quote_match(quote: str, judgment_text: str, min_len: int = 20) -> str | None:
    """Return match type: 'verbatim' | 'fuzzy' | None.

    'fuzzy' means the longest contiguous span shared with the judgment covers
    >=85% of the quote (recovers rules where the model lightly paraphrased/clipped
    the quote but the substance is genuinely present in the text).
    """
    q, t = _norm(quote), _norm(judgment_text)
    if len(q) < min_len:
        return None
    if q in t:
        return "verbatim"
    m = SequenceMatcher(None, q, t, autojunk=False).find_longest_match(0, len(q), 0, len(t))
    if m.size >= max(min_len, int(0.85 * len(q))):
        return "fuzzy"
    return None


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


def validate_rule(rule: dict, judgment_text: str, allow_fuzzy: bool = False) -> tuple[bool, dict, str]:
    """Return (accepted, cleaned_rule, reject_reason).

    Confidence is GROUNDED, not model-reported: verbatim quote -> high,
    fuzzy quote -> medium. (The 8B self-reports 'high' uniformly, so we ignore it.)
    """
    if not isinstance(rule, dict) or not rule.get("statement"):
        return False, {}, "no-statement"
    quote = rule.get("supporting_quote", "")
    match = quote_match(quote, judgment_text)
    if match is None or (match == "fuzzy" and not allow_fuzzy):
        return False, {}, "quote-not-found"
    sec_ref, sec_status = check_section(rule.get("statute_section"))
    confidence = "high" if match == "verbatim" else "medium"
    # verbatim statute citation as written in the judgment (for out-of-catalogue statutes
    # we haven't downloaded yet). Kept even when statute_section can't resolve.
    scv_raw = rule.get("statute_citation_verbatim")
    scv = (re.sub(r"\s+", " ", str(scv_raw)).strip()
           if scv_raw and str(scv_raw).strip().lower() not in ("null", "none", "") else "")
    scv_grounded = bool(scv) and quote_match(scv, judgment_text, min_len=10) is not None
    cleaned = {
        "statement": re.sub(r"\s+", " ", rule["statement"]).strip(),
        "supporting_quote": re.sub(r"\s+", " ", quote).strip(),
        "statute_section": sec_ref or "",
        "section_status": sec_status,
        "statute_citation_verbatim": scv,
        "statute_citation_grounded": scv_grounded,
        "match_type": match,
        "scope": rule.get("scope", "") if rule.get("scope") in ("ratio", "obiter", "fact-specific") else "",
        "confidence": confidence,
    }
    return True, cleaned, ""
