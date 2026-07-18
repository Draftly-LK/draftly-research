"""Reproducible audit: does the cue-aware window recover rulings that a naive
head+tail window would miss?

Defined population and denominator (no hand-waving):

  POPULATION  = CommonLII cases cached as `no-headnote` whose full text exceeds
                WINDOW_MAX_CHARS (i.e. windowing actually drops a middle).
  AT_RISK     = POPULATION cases that have >=1 _RULING_CUE match located in the
                OMITTED MIDDLE (HEAD_CHARS < offset < len-TAIL_CHARS) AND whose
                local context is NOT already present in the naive head+tail.
                These are the cases a naive window would genuinely miss.
  RECOVERED   = AT_RISK cases where build_window() now includes at least one such
                middle cue's local context (byte-checked, whitespace-normalised).

  Headline recall = RECOVERED / AT_RISK.

Also reports SAFE = POPULATION cases whose cue is already in the naive head/tail
(never at risk), for context. $0 — no API. Deterministic. Run:

  python scripts/case-law-information-extraction/audit_window_recall.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import config
import windowing

PROBE_LEN = 180  # chars of local context checked byte-for-byte


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def _text_for(case: dict) -> str | None:
    p = Path(case.get("text_path", ""))
    for cand in (config.ROOT / p, p):
        if cand.exists():
            return cand.read_text(encoding="utf-8", errors="replace").strip()
    return None


def main() -> None:
    no_head = {
        cf.stem
        for cf in config.CACHE.glob("commonlii-*.json")
        if _safe_status(cf) == "no-headnote"
    }

    population = at_risk = recovered = safe = 0
    misses = []
    for line in (config.ROOT / "data/processed/cases.jsonl").open(encoding="utf-8"):
        try:
            c = json.loads(line)
        except Exception:
            continue
        if c.get("case_id") not in no_head or c.get("source") != "commonlii":
            continue
        text = _text_for(c)
        if not text or len(text) <= config.WINDOW_MAX_CHARS:
            continue
        population += 1

        naive = _norm(text[: config.WINDOW_HEAD_CHARS] + text[-config.WINDOW_TAIL_CHARS:])
        window = _norm(windowing.build_window(text))

        middle_lo, middle_hi = config.WINDOW_HEAD_CHARS, len(text) - config.WINDOW_TAIL_CHARS
        risk_probes, safe_hit = [], False
        for m in windowing._RULING_CUE.finditer(text):
            probe = _norm(text[m.start(): m.start() + PROBE_LEN]).strip()
            if not probe:
                continue
            if middle_lo < m.start() < middle_hi and probe not in naive:
                risk_probes.append(probe)
            elif probe in naive:
                safe_hit = True

        if risk_probes:
            at_risk += 1
            if any(pr in window for pr in risk_probes):
                recovered += 1
            else:
                misses.append(c.get("case_id"))
        elif safe_hit:
            safe += 1

    pct = (recovered / at_risk * 100) if at_risk else 0.0
    print("=== window-recall audit (CommonLII no-headnote, text > WINDOW_MAX_CHARS) ===")
    print(f"POPULATION (windowed no-headnote cases): {population}")
    print(f"  SAFE   (ruling already in naive head/tail, never at risk): {safe}")
    print(f"  AT_RISK(ruling only in omitted middle, naive window misses): {at_risk}")
    print(f"  RECOVERED by cue-aware window: {recovered}")
    print(f"  HEADLINE RECALL = RECOVERED / AT_RISK = {recovered}/{at_risk} = {pct:.1f}%")
    if misses:
        print(f"  still-missed sample: {misses[:10]}")


def _safe_status(cf: Path) -> str:
    try:
        return json.loads(cf.read_text(encoding="utf-8")).get("status", "")
    except Exception:
        return ""


if __name__ == "__main__":
    main()
