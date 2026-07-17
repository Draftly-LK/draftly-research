"""Track A — deterministic headnote / Held-block extraction for reported cases.

Reported NLR/SLR judgments carry an editor-written headnote with a `Held:` block
that already states the rule. We locate it by rule (no LLM), so the rule text is
the reporter's own words, verbatim. ~64% of reported cases have a clean marker.
"""

from __future__ import annotations

import re

# End the Held block at the next structural marker of the judgment body.
_END = re.compile(
    r"(APPEAL|application|Cur\.?\s*adv\.?\s*vult|The following|Counsel|"
    r"Cases? referred to|delivered (his|her|the) judgment|"
    r"\bJ\.\s*[—-]|\bC\.?J\.?\s*[—-])", re.I)

_HELD = re.compile(r"\bHeld\s*[:\-—]", re.I)
_CATCHWORD = re.compile(r"\n([A-Z][A-Za-z][^\n]{0,120}—[^\n]{0,400})\n")  # "Topic—subtopic—..." line


def extract_headnote(text: str) -> dict | None:
    """Return {'held': <held block>, 'catchwords': <line or ''>} or None if no clean Held block."""
    m = _HELD.search(text)
    if not m:
        return None
    start = m.end()
    tail = text[start:start + 2500]
    end_m = _END.search(tail)
    held = (tail[:end_m.start()] if end_m else tail[:1500]).strip()
    held = re.sub(r"\s+", " ", held).strip(" .;:-—")
    if not (40 <= len(held) <= 2200):   # too short = false hit; too long = ran into the judgment
        return None
    cw = _CATCHWORD.search(text[:m.start()])
    catch = re.sub(r"\s+", " ", cw.group(1)).strip() if cw else ""
    return {"held": held, "catchwords": catch}


def split_holdings(held: str) -> list[str]:
    """A Held block often numbers multiple holdings: '(1) ... (2) ...'. Split, capped at 3."""
    parts = re.split(r"\(\s*\d+\s*\)|\(\s*[ivx]+\s*\)", held)
    parts = [re.sub(r"\s+", " ", p).strip(" .;:-—") for p in parts if len(p.strip()) > 30]
    return (parts or [held])[:3]
