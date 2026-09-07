"""Shared helpers for the legal-qa-v1 benchmark pipeline.

Everything under `scripts/legal-qa-pipeline/` is plumbing: schema validation,
hashing, atomic JSON/JSONL writes, stable identifier generation and the
per-matter state machine. Nothing here reads the law, calls a model or touches
the network. Every artifact these tools accept or emit carries
status=unverified semantics until a lawyer signs it off; the tools can only
tell you that an artifact is internally consistent, not that it is right.

Schemas are the frozen JSON Schema 2020-12 files in
`data/evaluvation/legal-qa-v1/schemas/`. Validation uses the `jsonschema`
package (present in the environment as a transitive dependency).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable, Iterator

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
LEGAL_QA_DIR = ROOT / "data" / "evaluvation" / "legal-qa-v1"
SCHEMA_DIR = LEGAL_QA_DIR / "schemas"
RUNS_DIR = LEGAL_QA_DIR / "runs"
DEFAULT_SOURCE_DIR = ROOT / "data" / "evaluvation" / "parsed-pastpapers" / "benchmark"

SCHEMA_FILES: dict[str, str] = {
    "authority": "authority.schema.json",
    "issue-map": "issue-map.schema.json",
    "legal-map": "legal-map.schema.json",
    "predicate": "predicate.schema.json",
    "document-spec": "document-spec.schema.json",
    "matter-ledger": "matter-ledger.schema.json",
    "synthetic-document": "synthetic-document.schema.json",
    "gold-question": "gold-question.schema.json",
    "lawyer-review": "lawyer-review.schema.json",
    "run-manifest": "run-manifest.schema.json",
}

SYNTHETIC_MARKER = (
    "SYNTHETIC BENCHMARK DOCUMENT - Draftly legal-qa-v1 - not a real instrument; "
    "all persons, numbers and places are fictional"
)

# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

ORDERED_STATES: list[str] = [
    "selected",
    "issue_mapped",
    "authorities_candidate",
    "authorities_verified",
    "predicates_defined",
    "documents_specified",
    "ledger_built",
    "synthetic_bundle_generated",
    "lawyer_review_pending",
    "lawyer_validated",
]
FAILURE_STATES: list[str] = [
    "blocked_missing_authority",
    "blocked_temporal_uncertainty",
    "blocked_source_conflict",
    "blocked_scenario_ambiguity",
    "needs_legal_review",
]
ALL_STATES: list[str] = ORDERED_STATES + FAILURE_STATES
HUMAN_ONLY_STATES: frozenset[str] = frozenset({"lawyer_validated"})


def state_index(state: str) -> int:
    """Position of an ordered state; -1 for failure or unknown states."""
    return ORDERED_STATES.index(state) if state in ORDERED_STATES else -1


def effective_ordered_state(state: str, state_history: Iterable[dict[str, Any]] = ()) -> str:
    """The last ordered state a matter reached.

    A matter parked in a failure state keeps the progress it had made; the
    history tells us where it was. With no history it is back at `selected`.
    """
    if state in ORDERED_STATES:
        return state
    last = "selected"
    for entry in state_history:
        s = entry.get("state")
        if s in ORDERED_STATES:
            last = s
    return last


def can_advance(current: str, target: str, state_history: Iterable[dict[str, Any]] = ()) -> bool:
    """True only when `target` is the immediate successor of the current progress.

    `lawyer_validated` is never reachable by code, whatever the input.
    """
    if target in HUMAN_ONLY_STATES or target not in ORDERED_STATES:
        return False
    base = effective_ordered_state(current, state_history)
    return state_index(target) == state_index(base) + 1


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def prefixed_sha256(hexdigest: str) -> str:
    return f"sha256:{hexdigest}"


def strip_sha256_prefix(value: str) -> str:
    return value[7:] if value.startswith("sha256:") else value


def canonical_json(obj: Any) -> str:
    """Stable serialisation used for hashing records (sorted keys, no spaces)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------

def dumps_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def write_json(path: Path, obj: Any) -> None:
    atomic_write_text(path, dumps_json(obj))


def read_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def read_text(path: Path) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[Any]) -> None:
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    atomic_write_text(path, text)


def read_json_if_exists(path: Path) -> Any | None:
    return read_json(path) if Path(path).exists() else None


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

_SCHEMA_CACHE: dict[tuple[str, str], dict[str, Any]] = {}


def load_schema(schema_name: str, schema_dir: Path | None = None) -> dict[str, Any]:
    if schema_name not in SCHEMA_FILES:
        raise KeyError(f"unknown schema {schema_name!r}; known: {sorted(SCHEMA_FILES)}")
    sdir = Path(schema_dir) if schema_dir else SCHEMA_DIR
    key = (str(sdir), schema_name)
    if key not in _SCHEMA_CACHE:
        _SCHEMA_CACHE[key] = read_json(sdir / SCHEMA_FILES[schema_name])
    return _SCHEMA_CACHE[key]


def _format_error(err: jsonschema.ValidationError) -> str:
    path = "/".join(str(p) for p in err.absolute_path) or "<root>"
    return f"{path}: {err.message}"


def validate_against_schema(obj: Any, schema_name: str, schema_dir: Path | None = None) -> list[str]:
    """Return a sorted list of human-readable schema violations (empty = valid)."""
    schema = load_schema(schema_name, schema_dir)
    validator = jsonschema.Draft202012Validator(schema, format_checker=None)
    errors = sorted(
        validator.iter_errors(obj),
        key=lambda e: (list(map(str, e.absolute_path)), e.message),
    )
    return [f"[{schema_name}] {_format_error(e)}" for e in errors]


def schema_hashes(schema_dir: Path | None = None) -> dict[str, str]:
    sdir = Path(schema_dir) if schema_dir else SCHEMA_DIR
    return {name: prefixed_sha256(sha256_file(sdir / fname)) for name, fname in sorted(SCHEMA_FILES.items())}


# ---------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------

MATTER_ID_RE = re.compile(r"^M[0-9]{3}$")
QUESTION_ID_RE = re.compile(r"^(M[0-9]{3})-Q([0-9]{2})$")
REF_ID_RE = re.compile(r"\b(AUTH|PR|CL)-M[0-9]{3}(?:-Q[0-9]{2})?-[0-9]{3}\b")
LEDGER_ID_RE = re.compile(r"\b(FACT|FLD|DOC)-M[0-9]{3}-[0-9]{3}\b")


def check_matter_id(matter_id: str) -> str:
    if not MATTER_ID_RE.match(matter_id):
        raise ValueError(f"bad matter id {matter_id!r}")
    return matter_id


def question_number(question_id: str) -> str:
    m = QUESTION_ID_RE.match(question_id)
    if not m:
        raise ValueError(f"bad question id {question_id!r}")
    return m.group(2)


def authority_id(matter_id: str, n: int) -> str:
    return f"AUTH-{check_matter_id(matter_id)}-{n:03d}"


def claim_id(matter_id: str, question: str | int, n: int) -> str:
    if isinstance(question, str) and "-" in question:
        qq = question_number(question)
    else:
        qq = f"{int(question):02d}"
    return f"CL-{check_matter_id(matter_id)}-Q{qq}-{n:03d}"


def predicate_id(matter_id: str, n: int) -> str:
    return f"PR-{check_matter_id(matter_id)}-{n:03d}"


def document_id(matter_id: str, n: int) -> str:
    return f"DOC-{check_matter_id(matter_id)}-{n:03d}"


def field_id(matter_id: str, n: int) -> str:
    return f"FLD-{check_matter_id(matter_id)}-{n:03d}"


def fact_id(matter_id: str, n: int) -> str:
    return f"FACT-{check_matter_id(matter_id)}-{n:03d}"


class StableIds:
    """Order-deterministic ID generators for one matter.

    Each kind counts from 1 in the order `next_*` is called, so building the
    same artifact from the same ordered inputs always yields the same IDs.
    Claim IDs count per question.
    """

    def __init__(self, matter_id: str) -> None:
        self.matter_id = check_matter_id(matter_id)
        self._counters: dict[str, int] = {}

    def _next(self, kind: str) -> int:
        self._counters[kind] = self._counters.get(kind, 0) + 1
        return self._counters[kind]

    def next_authority(self) -> str:
        return authority_id(self.matter_id, self._next("AUTH"))

    def next_claim(self, question_id: str) -> str:
        qq = question_number(question_id)
        return claim_id(self.matter_id, question_id, self._next(f"CL-{qq}"))

    def next_predicate(self) -> str:
        return predicate_id(self.matter_id, self._next("PR"))

    def next_document(self) -> str:
        return document_id(self.matter_id, self._next("DOC"))

    def next_field(self) -> str:
        return field_id(self.matter_id, self._next("FLD"))

    def next_fact(self) -> str:
        return fact_id(self.matter_id, self._next("FACT"))


def id_sequence(kind: str, matter_id: str, count: int, question_id: str | None = None) -> list[str]:
    """`count` IDs of one kind in order. Kinds: AUTH, CL (needs question_id), PR, DOC, FLD, FACT."""
    makers = {
        "AUTH": lambda n: authority_id(matter_id, n),
        "PR": lambda n: predicate_id(matter_id, n),
        "DOC": lambda n: document_id(matter_id, n),
        "FLD": lambda n: field_id(matter_id, n),
        "FACT": lambda n: fact_id(matter_id, n),
    }
    if kind == "CL":
        if not question_id:
            raise ValueError("claim IDs need a question_id")
        return [claim_id(matter_id, question_id, n) for n in range(1, count + 1)]
    if kind not in makers:
        raise ValueError(f"unknown id kind {kind!r}")
    return [makers[kind](n) for n in range(1, count + 1)]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def normalize_ws(text: str | None) -> str:
    return " ".join(str(text).split()) if text is not None else ""


def is_ws_substring(needle: str | None, haystack: str | None) -> bool:
    n = normalize_ws(needle)
    return bool(n) and n in normalize_ws(haystack)


NIC_OLD_RE = re.compile(r"\b\d{9}[VvXx]\b")
NIC_NEW_RE = re.compile(r"\b\d{12}\b")
PHONE_RE = re.compile(r"\b0\d{9}\b")
LABEL_LEAK_RE = re.compile(r"(gold|relevant|distractor|decisive|indispensable|answer)", re.IGNORECASE)


def find_pii(text: str) -> list[str]:
    hits: list[str] = []
    for label, rx in (("nic_old", NIC_OLD_RE), ("nic_new", NIC_NEW_RE), ("phone", PHONE_RE)):
        for m in rx.finditer(text):
            hits.append(f"{label}:{m.group(0)}")
    return hits


def iter_strings(obj: Any, path: str = "") -> Iterator[tuple[str, str]]:
    """Yield (json_path, string) for every string value in a JSON-like tree."""
    if isinstance(obj, str):
        yield path or "<root>", obj
    elif isinstance(obj, dict):
        for k in obj:
            yield from iter_strings(obj[k], f"{path}/{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from iter_strings(item, f"{path}[{i}]")


def dates_non_decreasing(earlier: str | None, later: str | None) -> bool:
    """Compare ISO-ish dates at the coarser granularity of the pair.

    '1990' and '1990-06-12' are compatible; '1991' after '1990-06-12' is fine;
    '1990-05' after '1990-06-12' is not.
    """
    if not earlier or not later:
        return True
    a, b = normalize_ws(earlier), normalize_ws(later)
    n = min(len(a), len(b))
    return a[:n] <= b[:n]


def is_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))


def local_source_path(path: str, root: Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(root) / p


TEXT_SUFFIXES = {".txt", ".md", ".json", ".html", ".htm"}


def source_text_for_excerpt_check(path: Path) -> str | None:
    """Text to search an excerpt in, or None when the file is binary/unsupported."""
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    raw = read_text(path)
    if path.suffix.lower() == ".json":
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        return json.dumps(obj, ensure_ascii=False) + "\n" + raw
    return raw


def report(matter: str, errors: list[str], warnings: list[str], **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        "matter": matter,
        "passed": not errors,
        "status": "unverified",
        "errors": list(errors),
        "warnings": list(warnings),
    }
    out.update(extra)
    return out


def source_texts(source: dict[str, Any]) -> list[str]:
    """Every past-paper text a ledger quote may be read from, in a stable order."""
    texts: list[str] = []
    bg = source.get("matter_background") or {}
    for key in ("original", "normalized"):
        if bg.get(key):
            texts.append(bg[key])
    for q in source.get("questions") or []:
        for key in (
            "question_original", "question_normalized", "effective_background_original",
            "effective_background_normalized", "source_quote",
        ):
            if q.get(key):
                texts.append(q[key])
        ctx = q.get("question_specific_context") or {}
        for key in ("group_background", "own_background"):
            if ctx.get(key):
                texts.append(ctx[key])
        for item in ctx.get("prior_background") or []:
            if isinstance(item, str):
                texts.append(item)
    for q in source.get("flat_questions") or []:
        for key in ("background_original", "background_normalized", "question_original", "question_normalized", "source_quote"):
            if q.get(key):
                texts.append(q[key])
    return texts


def source_question_ids(source: dict[str, Any]) -> list[str]:
    return [q["benchmark_question_id"] for q in source.get("questions") or []]
