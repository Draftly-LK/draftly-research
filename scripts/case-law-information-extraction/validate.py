"""The grounding gate. A rule is only accepted if its supporting_quote appears
verbatim in the judgment and its statute reference resolves against the closed
registry. This is what keeps a cheap model honest.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

import catalogue


_ALL_QUOTES = re.compile(r'[\'"‘’“”�]')


def _norm(s: str) -> str:
    # Quote-marks are unreliable in this OCR'd corpus: reporters re-insert a stray
    # `"` at every wrapped line inside a multi-line quote, and the model sometimes
    # renders the same quote with single quotes instead of double. Strip them
    # entirely (from both the model's quote and the judgment text) rather than
    # just the wrapping ones, so only the actual words have to match. Also strips
    # U+FFFD, the "unreadable character" marker some scans have in place of an
    # apostrophe (e.g. "executors� accounts" for "executors' accounts").
    s = _ALL_QUOTES.sub("", s or "")
    return re.sub(r"\s+", " ", s).strip().lower()


def quote_in_text(quote: str, judgment_text: str, min_len: int = 15) -> bool:
    """Verbatim (whitespace-insensitive) substring check."""
    q = _norm(quote)
    if len(q) < min_len:
        return False
    return q in _norm(judgment_text)


FUZZY_COVERAGE = 0.90  # fraction of the quote's characters that must land in matching blocks
FUZZY_WINDOW_PAD = 2.0  # how many quote-lengths of context to search around the anchor


def _digits(s: str) -> set[str]:
    return set(re.findall(r"\d+", s))


def quote_match(quote: str, judgment_text: str, min_len: int = 20) -> str | None:
    """Return match type: 'verbatim' | 'fuzzy' | None.

    'fuzzy' means: anchor on the best-aligning region of the judgment, then sum
    ALL matching blocks between the quote and that region (not just the single
    longest run) — this recovers quotes with several small scattered OCR/paraphrase
    diffs, not only a single clean break. Requires >=90% of the quote's characters
    to be covered. Hard-blocked if any digit sequence in the quote (a section
    number, date, amount, ...) doesn't appear anywhere in the aligned region —
    a near-miss must never be allowed to silently swap a citation or figure.
    """
    q, t = _norm(quote), _norm(judgment_text)
    if len(q) < min_len:
        return None
    if q in t:
        return "verbatim"
    anchor = SequenceMatcher(None, q, t, autojunk=False).find_longest_match(0, len(q), 0, len(t))
    if anchor.size == 0:
        return None
    pad = int(len(q) * FUZZY_WINDOW_PAD)
    start = max(0, anchor.b - pad)
    end = min(len(t), anchor.b + anchor.size + pad)
    window = t[start:end]
    q_nums = _digits(q)
    if q_nums and not q_nums.issubset(_digits(window)):
        return None
    sm = SequenceMatcher(None, q, window, autojunk=False)
    covered = sum(block.size for block in sm.get_matching_blocks())
    if covered >= max(min_len, FUZZY_COVERAGE * len(q)):
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
