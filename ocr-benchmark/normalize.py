"""Normalization, edit-distance metrics, and the guards that keep values local.

`platform_norm` is byte-identical to draftly-platform/backend/scripts/eval_extraction.py
`_norm`. If the two ever diverge, the benchmark's headline accuracy stops being
comparable to the platform's own golden-set number and the cross-check in the
README becomes meaningless. There is a test pinning it.

CER/WER are vendored rather than pulling in `jiwer`: the repo deliberately carries
no fuzzy-match dependency (validate.py uses stdlib difflib), and this is ~40 lines
of well-understood code that must work on the offline path with no extra install.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Iterable, Sequence

# ── normalization ────────────────────────────────────────────────────────────
# Ported from registry.normalize_field_value. A model answering "N/A" means
# "I did not find it", which is a miss, not a wrong string.
NULL_TOKENS = {"", "null", "none", "n/a", "unknown", "undetected"}


def null_collapse(value: object) -> str | None:
    """Collapse the model's ways of saying nothing into None."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in NULL_TOKENS:
        return None
    return text


def platform_norm(value: str) -> str:
    """Comparison-normalise, byte-identical to the platform's eval_extraction._norm.

    NFC, collapse whitespace, casefold, then strip the punctuation noise that
    makes 'Rs. 4,590,000/=' and '4590000' the same answer.
    """
    text = unicodedata.normalize("NFC", value)
    text = " ".join(text.split()).casefold()
    return text.replace(",", "").replace("/=", "").replace("/-", "").strip(" .")


def strict_norm(value: str) -> str:
    """NFC and whitespace only. Case- and punctuation-sensitive.

    Reported alongside platform_norm for critical identifiers, because stripping
    commas is right for money and wrong for a cadastral number.
    """
    return " ".join(unicodedata.normalize("NFC", value).split())


def ref_norm(value: str) -> str:
    """Reference normalization for CER/WER. Deliberately does NOT casefold.

    Casefolding a CER reference understates real recognition errors, and Sinhala
    has no case for it to help with anyway.
    """
    return " ".join(unicodedata.normalize("NFC", value).split())


# ── script detection ─────────────────────────────────────────────────────────
_SINHALA = re.compile(r"[඀-෿]")
_TAMIL = re.compile(r"[஀-௿]")
_LATIN = re.compile(r"[A-Za-z]")


def script_of(text: str) -> str:
    """Coarse script label from Unicode block counts. Heuristic, not ground truth."""
    if not text or not text.strip():
        return "unknown"
    counts = {
        "sinhala": len(_SINHALA.findall(text)),
        "tamil": len(_TAMIL.findall(text)),
        "latin": len(_LATIN.findall(text)),
    }
    present = [k for k, v in counts.items() if v > 0]
    if not present:
        return "unknown"
    if len(present) > 1:
        top = max(counts, key=lambda k: counts[k])
        # Latin digits and stray letters ride along with Sinhala constantly;
        # only call it mixed when the minority script is a real presence.
        others = sum(v for k, v in counts.items() if k != top)
        return "mixed" if others >= 0.15 * counts[top] else top
    return present[0]


# ── edit distance ────────────────────────────────────────────────────────────
def levenshtein(a: Sequence[object], b: Sequence[object]) -> int:
    """Edit distance over any sequence, two-row rolling array."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,        # deletion
                    current[j - 1] + 1,     # insertion
                    previous[j - 1] + (ca != cb),  # substitution
                )
            )
        previous = current
    return previous[-1]


def cer(reference: str, hypothesis: str) -> float | None:
    """Character error rate. None when the reference is empty (undefined)."""
    ref, hyp = ref_norm(reference), ref_norm(hypothesis)
    if not ref:
        return None
    return levenshtein(ref, hyp) / len(ref)


def wer(reference: str, hypothesis: str) -> float | None:
    """Word error rate. None when the reference is empty (undefined)."""
    ref = ref_norm(reference).split()
    hyp = ref_norm(hypothesis).split()
    if not ref:
        return None
    return levenshtein(ref, hyp) / len(ref)


# ── provenance / grounding ───────────────────────────────────────────────────
def value_in_text(value: str, text: str) -> bool:
    """Is the value verbatim present in the OCR text?

    Substring on the platform normalization - the same semantics as
    validate.quote_in_text. Deliberately NOT fuzzy: this metric backs the
    invented-value rate, and a fuzzy version would forgive exactly the
    hallucination it exists to catch.
    """
    needle = platform_norm(value or "")
    if not needle:
        return False
    return needle in platform_norm(text or "")


# ── confidence interval ──────────────────────────────────────────────────────
def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval. 26 pages is a small sample; report the error bars."""
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    margin = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


# ── validators (ported from the platform registry, reported not enforced) ────
def is_valid_nic(value: str) -> bool:
    return bool(re.fullmatch(r"\d{9}[VXvx]|\d{12}", value.strip()))


def is_valid_iso_date(value: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()))


def is_valid_extent(value: str) -> bool:
    return bool(re.search(r"\d", value)) and bool(
        re.search(r"\b(ha|hectare|hectares)\b", value, re.I)
    )


def is_digits(value: str) -> bool:
    return value.strip().isdigit()


VALIDATORS = {
    "is_valid_nic": is_valid_nic,
    "is_valid_iso_date": is_valid_iso_date,
    "is_valid_extent": is_valid_extent,
    "is_digits": is_digits,
}


# ── privacy guard ────────────────────────────────────────────────────────────
VALUE_COLUMNS = {
    "value", "expected", "predicted", "verbatimValue", "normalizedValue",
    "text", "verbatimText", "fullPageTranscript", "reference", "hypothesis",
}


def assert_no_raw_values(path: Path, columns: Iterable[str]) -> None:
    """Refuse to write field values anywhere that git could pick them up.

    reports/ is tracked and holds aggregates. Anything carrying a transcribed
    value belongs under runs/ or labels/, both gitignored.
    """
    parts = set(Path(path).resolve().parts)
    if "runs" in parts or "labels" in parts:
        return
    leaked = sorted(VALUE_COLUMNS.intersection(columns))
    if leaked:
        raise ValueError(
            f"refusing to write value columns {leaked} to tracked path {path}; "
            "write per-field detail under runs/ instead"
        )
