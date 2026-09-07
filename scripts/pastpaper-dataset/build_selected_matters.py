"""Build the first matter-level slice of the conveyancing past-paper QA benchmark.

Reads the atomic past-paper questions and their per-question classifications,
joins them on `atomic_id`, selects the gold-research-ready subset, groups the
survivors into legal matters, and writes three artefacts:

    selected-matters.jsonl        one record per matter, questions nested
    selected-questions.jsonl      one record per selected atomic question
    selected-matters-audit.json   counts, distributions, every normalization
                                  change, and anything left for a human

This stage does selection, grouping and whitespace normalization only. It does
not identify laws, answer anything, or add facts. Everything it emits is
status=unverified; a lawyer has not looked at any of it.

Selection predicate (all must hold):

    candidate_action   == "keep"
    scenario_richness  == "detailed"
    extraction_quality == "clean"
    confidence         >= 0.80
    context_dependency in {"required", "partial"}

Matter identity is the source `matter_id`, or `atomic:<atomic_id>` for a
record without one. Matters are sorted by (paper_no, question_no, key) and
numbered M001..; questions inside a matter follow paper order.

Context handling. Each question's effective background is built from the
fields named in its classification's `context_sources`, in the order
shared -> group -> prior -> own, with exact duplicates dropped. The matter
background is the run of segments present in *every* question of the matter
(compared on normalized text, so a fact that is `own_background` for part 1 and
`prior_background` for part 2 counts as common); anything else stays inside the
question record under `question_specific_context`. Instructional `stem` and
`group_lead` text is never treated as fact. If a selected record carries a
`group_lead` that does not look purely instructional it is written to the audit
under `group_lead_factual_context_review` rather than silently included or
dropped.

Normalization is conservative: line endings, runs of whitespace, and a space
before punctuation when the punctuation is followed by a space or the end of
the text. A space before punctuation that is followed by a letter (OCR such as
"Colombo .Her") is left alone and listed under `proposed_ocr_corrections`.
Both original and normalized text are stored.

The expected counts are checked and the script exits 2 with a diagnostic if
they do not hold. It never forces the output to a count.

    python scripts/pastpaper-dataset/build_selected_matters.py
    python scripts/pastpaper-dataset/build_selected_matters.py \
        --questions data/.../atomic-questions.jsonl \
        --classifications data/.../atomic-classifications.jsonl \
        --out-dir data/evaluvation/parsed-pastpapers/benchmark \
        --expected-questions 84 --expected-matters 44
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import statistics
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
ATOMIC_DIR = ROOT / "data/evaluvation/parsed-pastpapers/atomic"
DEFAULT_QUESTIONS = ATOMIC_DIR / "atomic-questions.jsonl"
DEFAULT_CLASSIFICATIONS = ATOMIC_DIR / "atomic-classifications.jsonl"
DEFAULT_OUT_DIR = ROOT / "data/evaluvation/parsed-pastpapers/benchmark"

EXPECTED_QUESTIONS = 84
EXPECTED_MATTERS = 44

SELECTION_PREDICATE: dict[str, Any] = {
    "candidate_action": "keep",
    "scenario_richness": "detailed",
    "extraction_quality": "clean",
    "confidence_min": 0.80,
    "context_dependency": ["required", "partial"],
}

ALLOWED_CONTEXT_SOURCES = {"shared", "group", "prior", "local"}
ALLOWED_DEPENDENCY = {"required", "partial", "none", "unclear"}
ALLOWED_RICHNESS = {"detailed", "minimal", "none", "unclear"}
ALLOWED_QUALITY = {"clean", "review", "malformed", "unclear"}
ALLOWED_ACTION = {"keep", "enrich", "drop_candidate", "repair", "review"}

REQUIRED_QUESTION_FIELDS = (
    "atomic_id", "part_uid", "paper_no", "question_no", "part_id", "item_id",
    "matter_id", "stem", "shared_background", "group_background", "group_lead",
    "prior_background", "own_background", "question", "marks", "pdf_page",
    "source_quote",
)
REQUIRED_CLASSIFICATION_FIELDS = (
    "atomic_id", "context_sources", "context_dependency", "scenario_richness",
    "extraction_quality", "candidate_action", "confidence", "flags",
)

# context_sources token -> atomic-question field, in effective-background order.
CONTEXT_FIELDS: tuple[tuple[str, str], ...] = (
    ("shared", "shared_background"),
    ("group", "group_background"),
    ("prior", "prior_background"),
    ("local", "own_background"),
)

# A group_lead / stem that is only an instruction, not a fact pattern.
INSTRUCTIONAL_LEAD = re.compile(
    r"^\s*(write|answer|explain|discuss|describe|state|give|list|define|"
    r"distinguish|comment|draft|note|briefly)\b",
    re.IGNORECASE,
)

SELECTION_STATUS = "gold_research_ready"


class ValidationError(Exception):
    """Raised when the inputs or the derived dataset fail a hard check."""

    def __init__(self, message: str, report: dict[str, Any] | None = None):
        super().__init__(message)
        self.report = report or {}


# --------------------------------------------------------------------------- io


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file, failing loudly on a bad line."""
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValidationError(
                    f"{path}:{line_no}: expected an object, got {type(record).__name__}"
                )
            records.append(record)
    return records


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=False)


def write_atomic(path: Path, text: str) -> None:
    """Write text to `path` via a temp file in the same directory, then replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    write_atomic(path, "".join(dumps(r) + "\n" for r in records))


def write_json(path: Path, obj: Any) -> None:
    write_atomic(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


# ------------------------------------------------------------------ validation


def _check_fields(record: dict[str, Any], required: Iterable[str], label: str) -> None:
    missing = [f for f in required if f not in record]
    if missing:
        raise ValidationError(f"{label} {record.get('atomic_id')!r} is missing fields {missing}")


def _check_enum(value: Any, allowed: set[str], field: str, atomic_id: str) -> None:
    if value not in allowed:
        raise ValidationError(
            f"classification {atomic_id!r}: {field}={value!r} not in {sorted(allowed)}"
        )


def find_duplicates(ids: Iterable[str]) -> list[str]:
    counts = collections.Counter(ids)
    return sorted(i for i, n in counts.items() if n > 1)


def join_records(
    questions: list[dict[str, Any]], classifications: list[dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Validate both inputs and return them keyed by atomic_id.

    Every classification must point at exactly one question. Questions without a
    classification are tolerated (they can never be selected) but reported by
    the caller via `missing_join_ids`.
    """
    for q in questions:
        _check_fields(q, REQUIRED_QUESTION_FIELDS, "atomic question")
        if not isinstance(q["prior_background"], list):
            raise ValidationError(
                f"atomic question {q['atomic_id']!r}: prior_background must be a list"
            )
    for c in classifications:
        _check_fields(c, REQUIRED_CLASSIFICATION_FIELDS, "classification")
        aid = c["atomic_id"]
        _check_enum(c["context_dependency"], ALLOWED_DEPENDENCY, "context_dependency", aid)
        _check_enum(c["scenario_richness"], ALLOWED_RICHNESS, "scenario_richness", aid)
        _check_enum(c["extraction_quality"], ALLOWED_QUALITY, "extraction_quality", aid)
        _check_enum(c["candidate_action"], ALLOWED_ACTION, "candidate_action", aid)
        if not isinstance(c["context_sources"], list):
            raise ValidationError(f"classification {aid!r}: context_sources must be a list")
        for s in c["context_sources"]:
            _check_enum(s, ALLOWED_CONTEXT_SOURCES, "context_sources", aid)
        conf = c["confidence"]
        if (
            isinstance(conf, bool)
            or not isinstance(conf, (int, float))
            or not (0.0 <= conf <= 1.0)
        ):
            raise ValidationError(
                f"classification {aid!r}: confidence={conf!r} is not a number in [0, 1]"
            )
        if not isinstance(c["flags"], list):
            raise ValidationError(f"classification {aid!r}: flags must be a list")

    dup_q = find_duplicates(q["atomic_id"] for q in questions)
    dup_c = find_duplicates(c["atomic_id"] for c in classifications)
    if dup_q or dup_c:
        raise ValidationError(
            f"duplicate atomic_id values: questions={dup_q} classifications={dup_c}",
            {"duplicate_atomic_ids": sorted(set(dup_q) | set(dup_c))},
        )

    by_q = {q["atomic_id"]: q for q in questions}
    by_c = {c["atomic_id"]: c for c in classifications}
    orphans = sorted(set(by_c) - set(by_q))
    if orphans:
        raise ValidationError(
            f"{len(orphans)} classification(s) have no atomic question: {orphans[:10]}",
            {"missing_join_ids": orphans},
        )
    return by_q, by_c


# ------------------------------------------------------------------- selection


def failed_predicates(c: dict[str, Any]) -> list[str]:
    """The predicate clauses this classification fails; empty means selected."""
    p = SELECTION_PREDICATE
    failed = []
    if c["candidate_action"] != p["candidate_action"]:
        failed.append(f"candidate_action={c['candidate_action']}")
    if c["scenario_richness"] != p["scenario_richness"]:
        failed.append(f"scenario_richness={c['scenario_richness']}")
    if c["extraction_quality"] != p["extraction_quality"]:
        failed.append(f"extraction_quality={c['extraction_quality']}")
    if float(c["confidence"]) < p["confidence_min"]:
        failed.append(f"confidence={c['confidence']}")
    if c["context_dependency"] not in p["context_dependency"]:
        failed.append(f"context_dependency={c['context_dependency']}")
    return failed


def is_selected(c: dict[str, Any]) -> bool:
    return not failed_predicates(c)


def grouping_key(q: dict[str, Any]) -> str:
    mid = q.get("matter_id")
    if isinstance(mid, str) and mid.strip():
        return mid
    return "atomic:" + q["atomic_id"]


# -------------------------------------------------------------------- ordering

_ROMAN = {"i": 1, "v": 5, "x": 10, "l": 50}
_ROMAN_RE = re.compile(r"^[ivxl]+$", re.IGNORECASE)


def _roman_to_int(s: str) -> int:
    total, prev = 0, 0
    for ch in reversed(s.lower()):
        val = _ROMAN[ch]
        total = total - val if val < prev else total + val
        prev = max(prev, val)
    return total


def label_sort_key(label: Any) -> tuple:
    """Order part/item labels the way the paper does: 1 < 2 < 10, i < iv < ix, a < b.

    Numeric labels sort first, then roman numerals, then letters, then anything
    else lexically. Mixed families inside one matter are not expected, but the
    key is total so sorting never fails.
    """
    if label is None:
        return (0, (), "")
    s = str(label).strip()
    if re.fullmatch(r"\d+(\.\d+)*", s):
        return (1, tuple(int(p) for p in s.split(".")), s)
    if _ROMAN_RE.fullmatch(s):
        return (2, (_roman_to_int(s),), s.lower())
    if re.fullmatch(r"[A-Za-z]", s):
        return (3, (ord(s.lower()),), s.lower())
    return (4, (), s)


def question_sort_key(q: dict[str, Any]) -> tuple:
    return (
        q["question_no"],
        label_sort_key(q["part_id"]),
        label_sort_key(q["item_id"]),
        q["atomic_id"],
    )


# --------------------------------------------------------------- normalization

# Space before punctuation only when the punctuation is followed by whitespace,
# a closing bracket/quote, or the end of the text. "extent .If" is left alone.
_SPACE_BEFORE_PUNCT = re.compile(r"[ \t]+([,.;:?!])(?=[\s)\]\"'”’]|$)")
_AMBIGUOUS_PUNCT = re.compile(r"\s+([,.;:?!])(?=[^\s)\]\"'”’])")


def normalize_text(text: str) -> tuple[str, list[str]]:
    """Whitespace-only normalization. Returns (normalized, change_kinds)."""
    changes: list[str] = []
    out = text.replace("\r\n", "\n").replace("\r", "\n")
    if out != text:
        changes.append("line_endings")
    collapsed = re.sub(r"\s+", " ", out).strip()
    if collapsed != out:
        changes.append("collapsed_whitespace")
    out = collapsed
    depunct = _SPACE_BEFORE_PUNCT.sub(r"\1", out)
    if depunct != out:
        changes.append("space_before_punctuation")
    out = depunct
    return out, changes


def ambiguous_punctuation(text: str) -> list[str]:
    """Snippets where a space precedes punctuation glued to the next word."""
    snippets = []
    for m in _AMBIGUOUS_PUNCT.finditer(text):
        lo, hi = max(0, m.start() - 20), min(len(text), m.end() + 20)
        snippets.append(text[lo:hi])
    return snippets


# ---------------------------------------------------------------------- context


class Segment:
    """One piece of factual context with its origin."""

    __slots__ = ("source", "field", "original", "normalized", "index")

    def __init__(self, source: str, field: str, original: str, index: int | None = None):
        self.source = source
        self.field = field
        self.original = original
        self.normalized = normalize_text(original)[0]
        self.index = index  # position inside prior_background, else None

    def key(self) -> str:
        return self.normalized

    @property
    def field_label(self) -> str:
        return self.field if self.index is None else f"{self.field}[{self.index}]"


def context_segments(q: dict[str, Any], sources: Iterable[str]) -> list[Segment]:
    """Ordered, de-duplicated context segments named by `sources`.

    Only fields listed in the classification's context_sources are consulted,
    in the fixed order shared -> group -> prior -> own. Empty fields contribute
    nothing. A segment whose normalized text has already appeared is dropped.
    """
    wanted = set(sources)
    out: list[Segment] = []
    seen: set[str] = set()
    for source, field in CONTEXT_FIELDS:
        if source not in wanted:
            continue
        value = q.get(field)
        if value is None or value == "" or value == []:
            continue
        values = value if isinstance(value, list) else [value]
        for i, text in enumerate(values):
            if not isinstance(text, str) or not text.strip():
                continue
            seg = Segment(source, field, text, i if isinstance(value, list) else None)
            if seg.key() in seen:
                continue
            seen.add(seg.key())
            out.append(seg)
    return out


def join_segments(segs: list[Segment], attr: str) -> str:
    return "\n\n".join(getattr(s, attr) for s in segs)


# ------------------------------------------------------------------------ build


def _empty_audit(n_q: int, n_c: int, exp_q: int | None, exp_m: int | None) -> dict[str, Any]:
    return {
        "source_counts": {"atomic_questions": n_q, "classifications": n_c},
        "selection_predicate": SELECTION_PREDICATE,
        "expected_counts": {"questions": exp_q, "matters": exp_m},
        "selected_atomic_question_count": 0,
        "selected_matter_count": 0,
        "questions_per_matter_distribution": {},
        "questions_by_paper": {},
        "context_source_distribution": {},
        "dependency_distribution": {},
        "confidence": {"minimum": None, "maximum": None, "mean": None},
        "duplicate_atomic_ids": [],
        "missing_join_ids": [],
        "empty_background_ids": [],
        "empty_question_ids": [],
        "background_conflicts": [],
        "normalization_changes": [],
        "proposed_ocr_corrections": [],
        "ocr_flag_review": [],
        "group_lead_factual_context_review": [],
        "stem_factual_context_review": [],
        "overlapping_context_segments": [],
        "quarantined_records": [],
        "validation_passed": False,
    }


def build(
    questions: list[dict[str, Any]],
    classifications: list[dict[str, Any]],
    expected_questions: int | None = EXPECTED_QUESTIONS,
    expected_matters: int | None = EXPECTED_MATTERS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Return (matters, flat_questions, audit). Raises ValidationError on failure."""
    audit = _empty_audit(len(questions), len(classifications), expected_questions, expected_matters)

    try:
        by_q, by_c = join_records(questions, classifications)
    except ValidationError as exc:
        audit.update(exc.report)
        raise ValidationError(str(exc), audit) from exc

    # Questions with no classification can never be selected; report them.
    audit["missing_join_ids"] = sorted(set(by_q) - set(by_c))

    selected_ids = sorted(aid for aid, c in by_c.items() if is_selected(c))
    audit["selected_atomic_question_count"] = len(selected_ids)

    if expected_questions is not None and len(selected_ids) != expected_questions:
        near = []
        for aid, c in sorted(by_c.items()):
            failed = failed_predicates(c)
            if len(failed) == 1:
                near.append({
                    "atomic_id": aid,
                    "failed": failed,
                    **{k: c[k] for k in (
                        "candidate_action", "scenario_richness", "extraction_quality",
                        "context_dependency", "confidence",
                    )},
                })
        audit["selected_atomic_ids"] = selected_ids
        audit["near_miss_records"] = near
        raise ValidationError(
            f"selected {len(selected_ids)} atomic questions, expected {expected_questions}; "
            "see audit selected_atomic_ids / near_miss_records",
            audit,
        )

    # ---- group
    groups: dict[str, list[str]] = collections.defaultdict(list)
    for aid in selected_ids:
        groups[grouping_key(by_q[aid])].append(aid)
    for key in groups:
        groups[key].sort(key=lambda a: question_sort_key(by_q[a]))

    def matter_sort_key(key: str) -> tuple:
        first = by_q[groups[key][0]]
        return (first["paper_no"], first["question_no"], key)

    ordered_keys = sorted(groups, key=matter_sort_key)
    audit["selected_matter_count"] = len(ordered_keys)
    if expected_matters is not None and len(ordered_keys) != expected_matters:
        audit["grouping"] = {k: groups[k] for k in ordered_keys}
        raise ValidationError(
            f"grouped into {len(ordered_keys)} matters, expected {expected_matters}; "
            "see audit grouping",
            audit,
        )

    # ---- per-question context and normalization
    norm_changes: dict[tuple[str, str], dict[str, Any]] = {}
    proposed: dict[tuple[str, str, str], dict[str, Any]] = {}

    def record_normalization(aid: str, field: str, text: str) -> str:
        norm, kinds = normalize_text(text)
        if kinds:
            norm_changes.setdefault((aid, field), {
                "atomic_id": aid, "field": field, "changes": kinds,
                "chars_before": len(text), "chars_after": len(norm),
            })
        for snip in ambiguous_punctuation(text):
            proposed.setdefault((aid, field, snip), {
                "atomic_id": aid, "field": field, "snippet": snip,
                "issue": "space before punctuation glued to next word; not applied",
            })
        return norm

    matters: list[dict[str, Any]] = []
    flat: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []

    for m_idx, key in enumerate(ordered_keys, 1):
        mid = f"M{m_idx:03d}"
        aids = groups[key]
        per_q_segments: dict[str, list[Segment]] = {}
        problems: list[str] = []

        for aid in aids:
            q, c = by_q[aid], by_c[aid]
            segs = context_segments(q, c["context_sources"])
            per_q_segments[aid] = segs
            # A listed source that is empty is a boundary problem in the source data.
            for source, field in CONTEXT_FIELDS:
                if source in c["context_sources"] and not q.get(field):
                    problems.append(f"{aid}: context_sources lists {source!r} but {field} is empty")
            if not segs:
                problems.append(f"{aid}: no factual context from {c['context_sources']}")
            # Exact duplicates are dropped; a segment that merely contains another
            # (prior = group text + new facts) is kept verbatim and reported.
            for outer in segs:
                for inner in segs:
                    if outer is not inner and inner.key() in outer.key():
                        audit["overlapping_context_segments"].append({
                            "atomic_id": aid, "matter": mid,
                            "contains": inner.field_label, "within": outer.field_label,
                        })
            if q.get("group_lead") and not INSTRUCTIONAL_LEAD.match(q["group_lead"]):
                audit["group_lead_factual_context_review"].append({
                    "atomic_id": aid, "matter": mid, "group_lead": q["group_lead"],
                    "group_in_context_sources": "group" in c["context_sources"],
                })
            if q.get("stem") and not INSTRUCTIONAL_LEAD.match(q["stem"]):
                audit["stem_factual_context_review"].append(
                    {"atomic_id": aid, "matter": mid, "stem": q["stem"]}
                )
            for flag in c["flags"]:
                if re.search(r"ocr|typo", str(flag), re.IGNORECASE):
                    audit["ocr_flag_review"].append({"atomic_id": aid, "matter": mid, "flag": flag})

        # Shared background must be one text across the matter where it is used.
        shared_texts = {
            normalize_text(by_q[a]["shared_background"])[0]
            for a in aids
            if "shared" in by_c[a]["context_sources"] and by_q[a].get("shared_background")
        }
        if len(shared_texts) > 1:
            problems.append("shared_background differs between questions that list 'shared'")

        if problems:
            conflicts.append({"matter": mid, "grouping_key": key, "problems": problems})
            quarantined.append({"grouping_key": key, "atomic_ids": aids, "reason": problems})
            continue

        # Matter background = segments present in every question, in first-question order.
        first_segs = per_q_segments[aids[0]]
        common_keys = {s.key() for s in first_segs}
        for aid in aids[1:]:
            common_keys &= {s.key() for s in per_q_segments[aid]}
        common_segs = [s for s in first_segs if s.key() in common_keys]

        source_fields: list[dict[str, Any]] = []
        for i, seg in enumerate(common_segs):
            by_field: dict[str, list[str]] = collections.defaultdict(list)
            for aid in aids:
                for s in per_q_segments[aid]:
                    if s.key() == seg.key():
                        by_field[s.field].append(aid)
            for field in sorted(by_field):
                source_fields.append(
                    {"segment_index": i, "field": field, "atomic_ids": by_field[field]}
                )

        matter_questions: list[dict[str, Any]] = []
        for q_idx, aid in enumerate(aids, 1):
            q, c = by_q[aid], by_c[aid]
            qid = f"{mid}-Q{q_idx:02d}"
            segs = per_q_segments[aid]
            for s in segs:
                record_normalization(aid, s.field_label, s.original)
            residual = [s for s in segs if s.key() not in common_keys]
            specific = {
                "group_background": next(
                    (s.original for s in residual if s.field == "group_background"), None
                ),
                "prior_background": [s.original for s in residual if s.field == "prior_background"],
                "own_background": next(
                    (s.original for s in residual if s.field == "own_background"), None
                ),
            }
            q_norm = record_normalization(aid, "question", q["question"])
            eff_orig = join_segments(segs, "original")
            eff_norm = join_segments(segs, "normalized")
            if not eff_norm:
                audit["empty_background_ids"].append(aid)
            if not q_norm:
                audit["empty_question_ids"].append(aid)
            classification = {
                "context_sources": list(c["context_sources"]),
                "context_dependency": c["context_dependency"],
                "scenario_richness": c["scenario_richness"],
                "extraction_quality": c["extraction_quality"],
                "candidate_action": c["candidate_action"],
                "confidence": c["confidence"],
                "flags": list(c["flags"]),
            }
            matter_questions.append({
                "benchmark_question_id": qid,
                "atomic_id": aid,
                "part_uid": q["part_uid"],
                "part_id": q["part_id"],
                "item_id": q["item_id"],
                "marks": q["marks"],
                "pdf_page": q["pdf_page"],
                "question_original": q["question"],
                "question_normalized": q_norm,
                "question_specific_context": specific,
                "effective_background_original": eff_orig,
                "effective_background_normalized": eff_norm,
                "source_quote": q["source_quote"],
                "classification": classification,
            })
            flat.append({
                "benchmark_question_id": qid,
                "benchmark_matter_id": mid,
                "atomic_id": aid,
                "paper_no": q["paper_no"],
                "background_original": eff_orig,
                "background_normalized": eff_norm,
                "question_original": q["question"],
                "question_normalized": q_norm,
                "source_quote": q["source_quote"],
                "provenance": {
                    "source_matter_id": q.get("matter_id") or None,
                    "part_uid": q["part_uid"],
                    "pdf_page": q["pdf_page"],
                    "context_sources": list(c["context_sources"]),
                },
                "selection": {
                    "candidate_action": c["candidate_action"],
                    "scenario_richness": c["scenario_richness"],
                    "extraction_quality": c["extraction_quality"],
                    "context_dependency": c["context_dependency"],
                    "confidence": c["confidence"],
                },
                "legal_map_status": "pending",
                "lawyer_validation_status": "pending",
            })

        first = by_q[aids[0]]
        matters.append({
            "benchmark_matter_id": mid,
            "source_matter_id": first.get("matter_id") or None,
            "grouping_key": key,
            "paper_no": first["paper_no"],
            "question_no": first["question_no"],
            "selection_status": SELECTION_STATUS,
            "matter_background": {
                "original": join_segments(common_segs, "original"),
                "normalized": join_segments(common_segs, "normalized"),
                "source_fields": source_fields,
            },
            "questions": matter_questions,
        })

    audit["background_conflicts"] = conflicts
    audit["quarantined_records"] = quarantined
    audit["normalization_changes"] = list(norm_changes.values())
    audit["proposed_ocr_corrections"] = list(proposed.values())

    # ---- distributions
    audit["questions_per_matter_distribution"] = {
        str(n): cnt
        for n, cnt in sorted(collections.Counter(len(m["questions"]) for m in matters).items())
    }
    audit["questions_by_paper"] = {
        str(p): cnt for p, cnt in sorted(collections.Counter(f["paper_no"] for f in flat).items())
    }
    audit["context_source_distribution"] = {
        "+".join(k): v
        for k, v in sorted(
            collections.Counter(tuple(f["provenance"]["context_sources"]) for f in flat).items()
        )
    }
    audit["dependency_distribution"] = dict(sorted(
        collections.Counter(f["selection"]["context_dependency"] for f in flat).items()
    ))
    confs = [float(f["selection"]["confidence"]) for f in flat]
    if confs:
        audit["confidence"] = {
            "minimum": min(confs),
            "maximum": max(confs),
            "mean": round(statistics.fmean(confs), 4),
        }

    # ---- final checks
    failures: list[str] = []
    if quarantined:
        failures.append(f"{len(quarantined)} matter(s) quarantined for background-boundary problems")
    if audit["empty_background_ids"]:
        failures.append(f"empty effective background: {audit['empty_background_ids']}")
    if audit["empty_question_ids"]:
        failures.append(f"empty question: {audit['empty_question_ids']}")
    flat_ids = [f["atomic_id"] for f in flat]
    if sorted(flat_ids) != selected_ids:
        failures.append("flattened questions do not match the selected set")
    nested_ids = sorted(qq["atomic_id"] for m in matters for qq in m["questions"])
    if nested_ids != selected_ids:
        failures.append("nested questions do not match the selected set")
    matter_ids = {m["benchmark_matter_id"] for m in matters}
    if any(f["benchmark_matter_id"] not in matter_ids for f in flat):
        failures.append("a flattened question references a missing matter")
    if expected_matters is not None and len(matters) != expected_matters:
        failures.append(f"{len(matters)} matters written, expected {expected_matters}")
    if expected_questions is not None and len(flat) != expected_questions:
        failures.append(f"{len(flat)} questions written, expected {expected_questions}")
    for f in flat:
        q = by_q[f["atomic_id"]]
        if f["question_original"] != q["question"] or f["source_quote"] != q["source_quote"]:
            failures.append(f"{f['atomic_id']}: original text or quote altered")
    if failures:
        raise ValidationError("; ".join(failures), audit)

    audit["validation_passed"] = True
    return matters, flat, audit


# ------------------------------------------------------------------------- cli


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    ap.add_argument("--classifications", type=Path, default=DEFAULT_CLASSIFICATIONS)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument(
        "--expected-questions", type=int, default=EXPECTED_QUESTIONS,
        help="fail unless exactly this many atomic questions are selected (-1 to skip)",
    )
    ap.add_argument(
        "--expected-matters", type=int, default=EXPECTED_MATTERS,
        help="fail unless exactly this many matters result (-1 to skip)",
    )
    args = ap.parse_args(argv)

    out_dir: Path = args.out_dir
    audit_path = out_dir / "selected-matters-audit.json"
    exp_q = None if args.expected_questions < 0 else args.expected_questions
    exp_m = None if args.expected_matters < 0 else args.expected_matters

    try:
        questions = read_jsonl(args.questions)
        classifications = read_jsonl(args.classifications)
    except (OSError, ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        matters, flat, audit = build(questions, classifications, exp_q, exp_m)
    except ValidationError as exc:
        audit = dict(exc.report)
        audit["validation_passed"] = False
        audit["error"] = str(exc)
        write_json(audit_path, audit)
        print(f"VALIDATION FAILED: {exc}\nDiagnostic written to {audit_path}", file=sys.stderr)
        return 2

    write_jsonl(out_dir / "selected-matters.jsonl", matters)
    write_jsonl(out_dir / "selected-questions.jsonl", flat)
    write_json(audit_path, audit)
    print(f"wrote {len(matters)} matters, {len(flat)} questions -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
