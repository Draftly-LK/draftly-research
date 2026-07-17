"""Track B — build a focused, size-capped extract of an unreported judgment.

We don't send the whole judgment (cost + dilution). Sri Lankan judgments state
the ruling near the end ("I hold…", "the appeal is allowed…"). Send: the opening
(facts/issue framing) + the closing (reasoning/order) + any paragraphs with
ruling cues, deduped and capped.
"""

from __future__ import annotations

import re

import config

_RULING_CUE = re.compile(
    r"(I\s+(?:hold|am of (?:the )?view|am inclined|therefore hold)|"
    r"it is (?:hereby )?(?:held|ordered|declared)|"
    r"the appeal is (?:allowed|dismissed)|"
    r"I (?:set aside|affirm|allow|dismiss)|"
    r"in (?:my|our) (?:view|opinion|judgment)|"
    r"the (?:learned )?(?:trial |district )?judge (?:erred|was (?:right|wrong)))",
    re.I)


def _paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def build_window(text: str) -> str:
    """Head + ruling-cue paragraphs + tail, deduped, capped at WINDOW_MAX_CHARS."""
    text = text.strip()
    if len(text) <= config.WINDOW_MAX_CHARS:
        return text

    head = text[: config.WINDOW_HEAD_CHARS]
    tail = text[-config.WINDOW_TAIL_CHARS:]

    cue_paras = []
    budget = config.WINDOW_MAX_CHARS - len(head) - len(tail)
    if budget > 0:
        for p in _paragraphs(text[config.WINDOW_HEAD_CHARS: -config.WINDOW_TAIL_CHARS or None]):
            if _RULING_CUE.search(p):
                cue_paras.append(p)
                budget -= len(p)
                if budget <= 0:
                    break

    middle = ("\n\n[...]\n\n" + "\n\n".join(cue_paras) if cue_paras else "")
    window = head + middle + "\n\n[...]\n\n" + tail
    return window[: config.WINDOW_MAX_CHARS + 2000]  # small slack; head+tail are load-bearing
