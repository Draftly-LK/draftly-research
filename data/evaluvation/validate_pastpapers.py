"""Validate a past-paper extraction and split it into metadata and questions.

Replaces the first version, which reported "41/41 verbatim, 0 rejections" on an
extraction that had silently dropped four question stems. That was not a lucky
miss: a substring check can only prove text was not INVENTED. It cannot prove
text was not MISSING, because a truncated quote is still a perfect substring.

So this version adds the check that actually catches that class of error:

  coverage - every line of question text on the page must be accounted for by
  some node in the extraction. Anything left over is a dropped stem, and it is
  reported per line so it can be read against the source.

Plus two checks the first version lacked:

  quote completeness - a quote must match whole source lines, not a fragment of
  one, so `quote` cannot silently degrade into a shortened paraphrase of `text`.
  structure - a part that has items must still carry its own text, and group
  marks stay on the part rather than migrating onto its first item.

Output is split, because a preprocessing-adjacent artifact and a content
artifact have different lifetimes and different owners:

  paper-NN.metadata.json   paper identity, source, OCR confidence, provenance
  paper-NN.questions.json  the question tree and nothing else

Paper metadata is derived deterministically here (papers.csv plus regex over the
printed header), not asked of the model. There is no reason to spend model
judgement on a line that says "CONVEYANCING (LW 307)".

Passing these checks means the extraction faithfully reflects the OCR text, not
that the OCR is correct or that anyone has signed it off. The output files no
longer carry a status field, so that caveat is printed on every run instead.

Usage:
    uv run python data/evaluvation/validate_pastpapers.py --paper 3
    uv run python data/evaluvation/validate_pastpapers.py --paper 3 --show-coverage
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

PAGES_DIR = HERE / "2-documentai-outputs" / "pages"
MANIFEST = HERE / "2-documentai-outputs" / "manifest.csv"
PAPERS_CSV = HERE / "papers.csv"
SOURCE_PDF = HERE / "preprocess-pdf.pdf"
OUT_DIR = HERE / "parsed-pastpapers"
RAW_DIR = OUT_DIR / "raw"
# One directory per artifact kind. The three outputs have different audiences -
# questions are the deliverable, metadata is reference, reports are run output -
# and 48 files in one flat directory made it hard to see which was which.
QUESTIONS_DIR = OUT_DIR / "questions"
METADATA_DIR = OUT_DIR / "metadata"
REPORTS_DIR = OUT_DIR / "reports"

SCHEMA_VERSION = 2

# Lines that are page furniture, not question text. Anything matching these is
# excluded from the coverage denominator.
FURNITURE = [
    re.compile(r"^page\s+\d+\s+of\s+\d+$", re.I),
    re.compile(r"^scanned\s+with$", re.I),
    re.compile(r"^camscanner$", re.I),
    re.compile(r"^\(?\d{1,3}\s*marks?\)?$", re.I),
    re.compile(r"^\(?total\s*[:=]?\s*\d{1,3}\s*marks?\)?\.?$", re.I),
    # Papers annotate the allocation rather than just printing a number:
    # "(3 marks for a complete answer)", "(3 marks for each method - 6 marks
    # for a complete answer)". Still furniture, still not question text.
    re.compile(r"^\(?\d{1,3}(\.\d)?\s*marks?\b[^?]*\)?\.?$", re.I),
    re.compile(r"^sri\s+lanka\s+law\s+college$", re.I),
    re.compile(r"^attorneys?\s*[-–]?\s*at\s*[-–]?\s*law.*examination.*$", re.I),
    re.compile(r"^conveyancing\b.*$", re.I),
    re.compile(r"^time\s*[-–:]?\s*\d+\s*hours?$", re.I),
    re.compile(r"^(please\s+)?write\s+your\s+answers?\s+legibly.*$", re.I),
    re.compile(r"^answer\s+six.*$", re.I),
    # OCR renders this as "Evey" on at least one paper, so the word is matched
    # loosely. Furniture patterns run against scanned text, not clean copy.
    # The "other questions carry N marks" rubric appears in at least four
    # wordings across the 16 papers ("Every other question carries", "All other
    # questions carry", "Evey other question carries" from an OCR typo), and OCR
    # wraps it so the line often starts mid-sentence with the tail of the
    # previous one. Matching the invariant middle beats chasing each variant.
    re.compile(r"^.{0,12}?\b(ev\w*y|all|other)\b.*other\s+questions?\s+carr(y|ies).*$", re.I),
    re.compile(r"^.{0,12}?other\s+questions?\s+carr(y|ies).*$", re.I),
    # OCR can split the rubric mid-word ("...All ot" / "questions carry 15
    # marks."), leaving a tail with no "other" in it at all.
    re.compile(r"^questions?\s+carr(y|ies)\s+\d{1,3}\s*marks?\.?$", re.I),
]

# Below this a leftover line is student handwriting or a page number artifact
# rather than a dropped question, so it is not counted against coverage.
MIN_COVERAGE_LINE = 25

# Page 35 is the Sinhala version of paper 8 and Document AI transcribed it as
# garbled Latin ("gab ww (6) ma 045 88q6 wywaln"), not as Sinhala script. It is
# the only such page in the corpus: its common-word ratio is 0.068 against a
# median of 0.336, and the next-worst page is three times higher. An extractor
# is right to skip those lines, so counting them as dropped questions would
# blame the extraction for an OCR limitation. Lines are judged individually
# because the page still carries a readable English header.
COMMON_WORDS = set(
    "the of and to in is a for what are be by any or on that with as under "
    "this shall not from he she his her it its you your".split()
)
MIN_ENGLISH_RATIO = 0.10


def english_ratio(text: str) -> float:
    tokens = re.findall(r"[A-Za-z]+", text.lower())
    if not tokens:
        return 0.0
    return sum(1 for t in tokens if t in COMMON_WORDS) / len(tokens)


def is_unreadable_page(text: str) -> bool:
    """True when a whole page is OCR noise rather than readable English.

    Judged per page, not per line. A line-level test cannot work here: real
    question lines are often short and function-word free ("ii. Street Line
    Certificate" scores 0.0), so any threshold strict enough to catch the noise
    also discards genuine questions. Whole pages are unambiguous - page 35
    scores 0.068 against a corpus median of 0.336, and the next-worst page is
    three times higher.
    """
    return len(re.findall(r"[A-Za-z]+", text)) >= 40 and english_ratio(text) < MIN_ENGLISH_RATIO


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def is_furniture(line: str) -> bool:
    stripped = _norm(line)
    if not stripped:
        return True
    return any(pattern.match(stripped) for pattern in FURNITURE)


# ── inputs ───────────────────────────────────────────────────────────────────
def load_paper_row(paper_no: int) -> dict:
    with PAPERS_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if int(row["paper_no"]) == paper_no:
                return row
    raise SystemExit(f"error: paper {paper_no} is not in {PAPERS_CSV.name}")


def load_pages(start: int, end: int) -> dict[int, str]:
    pages = {}
    for page_no in range(start, end + 1):
        path = PAGES_DIR / f"page-{page_no:03d}.txt"
        if not path.is_file():
            raise SystemExit(f"error: missing OCR text for page {page_no}: {path}")
        pages[page_no] = path.read_text(encoding="utf-8")
    return pages


def load_confidence() -> dict[int, float]:
    if not MANIFEST.is_file():
        return {}
    out = {}
    with MANIFEST.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                out[int(row["page_no"])] = float(row["confidence"])
            except (KeyError, TypeError, ValueError):
                continue
    return out


# ── metadata, derived not asked ──────────────────────────────────────────────
def derive_metadata(paper_no: int, row: dict, pages: dict[int, str], confidence: dict[int, float]) -> dict:
    first = pages[min(pages)]
    lines = [_norm(l) for l in first.splitlines() if _norm(l)]

    def find(pattern: str) -> str | None:
        rx = re.compile(pattern, re.I)
        return next((l for l in lines if rx.search(l)), None)

    subject_line = find(r"conveyancing")
    code = None
    if subject_line:
        match = re.search(r"\(([A-Z]{2}\s*\d{3})\)", subject_line)
        code = match.group(1).replace(" ", "") if match else None

    rubric_parts = [l for l in lines if re.search(r"answer\s+six|every other question carries", l, re.I)]
    page_conf = {p: confidence[p] for p in pages if p in confidence}

    return {
        "schema_version": SCHEMA_VERSION,
        "paper_no": paper_no,
        "session": (row.get("session") or "").strip(),
        "subject": subject_line,
        "code": code,
        "time_allowed": find(r"^time\s*[-–:]?\s*\d+\s*hours?$"),
        "rubric": " ".join(rubric_parts) or None,
        "pdf_pages": {"start": min(pages), "end": max(pages), "count": len(pages)},
        "source": {
            "pdf": SOURCE_PDF.name,
            "ocr_text_dir": str(PAGES_DIR.relative_to(HERE)),
            "ocr_engine": "google-document-ai",
            "paper_index": PAPERS_CSV.name,
            "paper_index_source": (row.get("source") or "").strip(),
        },
        "ocr_confidence": {
            "per_page": page_conf,
            "mean": round(sum(page_conf.values()) / len(page_conf), 4) if page_conf else None,
            "min": round(min(page_conf.values()), 4) if page_conf else None,
        },
        "extraction": {
            "model": "claude-haiku-4-5",
            "pass": "structure-only",
            "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    }


# ── checks ───────────────────────────────────────────────────────────────────
def walk_nodes(raw: dict):
    """Yield (label, node) for every text-bearing node in the tree."""
    for question in raw.get("questions", []) or []:
        q_no = question.get("question_no")
        # stem and fact_pattern are both question-level lead-ins and are kept
        # apart on purpose: an instruction ("Write notes on the following")
        # belongs in a composed retrieval query, a scenario full of names and
        # dates does not. Collapsing them would lose that distinction, and
        # having neither is what silently dropped 8 stems across the corpus.
        stem = question.get("stem")
        if isinstance(stem, dict):
            yield f"Q{q_no}.stem", stem
        fact = question.get("fact_pattern")
        if isinstance(fact, dict):
            yield f"Q{q_no}.fact_pattern", fact
        for part in question.get("parts", []) or []:
            label = f"Q{q_no}.{part.get('part_id')}"
            yield label, part
            for item in part.get("items", []) or []:
                yield f"{label}.{item.get('item_id')}", item


def quote_status(quote: str, pages: dict[int, str]) -> str:
    """'complete' | 'reassembled' | 'truncated' | 'absent'.

    'reassembled' exists because the OCR scrambles reading order on 14 of the
    67 pages: a "(1 mark)" line is printed above the item it belongs to rather
    than after it. An extractor that pairs them correctly produces a quote whose
    lines are each verbatim but are not adjacent in the file.

    Requiring contiguity was a proxy for the property actually worth enforcing,
    which is that no text was invented. Two extraction runs failed to honour the
    contiguity rule even when told explicitly, because the model reasonably
    prefers the correct pairing over the printed order. So contiguity is
    reported rather than required: every line must still be verbatim, and a
    reassembled quote is flagged so the reading-order damage stays visible.

    complete  - the quote covers whole source lines
    truncated - the quote is inside a line but is materially shorter than it,
                which is how `quote` silently degraded into a short fragment
    absent    - not in the source at all
    """
    q = _norm(quote)
    if not q:
        return "absent"
    source_lines = [_norm(l) for page in pages.values() for l in page.splitlines() if _norm(l)]
    joined = " ".join(source_lines)
    if q not in joined:
        return "absent"
    if q in source_lines:
        return "complete"
    # Multi-line spans: a run of consecutive whole lines joined together.
    for size in range(2, 8):
        for start in range(len(source_lines) - size + 1):
            if _norm(" ".join(source_lines[start:start + size])) == q:
                return "complete"
    containing = [l for l in source_lines if q in l]
    if containing and min(len(l) for l in containing) - len(q) > 12:
        return "truncated"
    return "complete"


def quote_lines_verbatim(quote: str, pages: dict[int, str]) -> bool:
    """Every line of the quote appears verbatim somewhere in the source.

    The anti-hallucination guarantee, independent of line ordering.
    """
    source_lines = [_norm(l) for page in pages.values() for l in page.splitlines() if _norm(l)]
    joined = " ".join(source_lines)
    parts = [_norm(l) for l in (quote or "").splitlines() if _norm(l)]
    return bool(parts) and all(p in joined for p in parts)


def coverage(raw: dict, pages: dict[int, str]) -> list[tuple[int, str]]:
    """Source question lines not accounted for by any extracted node.

    This is the check that catches a dropped stem. Everything else in this file
    verifies what the model DID emit; only this one asks what it did not.
    """
    per_node = [
        _norm(node.get("quote", "")) + " " + _norm(node.get("text", ""))
        for _label, node in walk_nodes(raw)
    ]
    claimed = " ".join(per_node)
    # Lines a human has judged to be handwriting rather than printed exam text.
    # Recorded per line in the extraction with a reason, so the decision is
    # visible and reviewable, instead of being absorbed by a looser rule that
    # would also stop catching real drops.
    excluded = {
        _norm(entry.get("line", ""))
        for entry in raw.get("excluded_lines", []) or []
        if isinstance(entry, dict)
    }

    missing = []
    for page_no, text in pages.items():
        if is_unreadable_page(text):
            continue
        for line in text.splitlines():
            stripped = _norm(line)
            if is_furniture(stripped) or len(stripped) < MIN_COVERAGE_LINE:
                continue
            if stripped in excluded:
                continue
            core = re.sub(r"^\(?[0-9a-zA-Z]{1,3}[.)]\s*", "", stripped)
            core = re.sub(r"\(?\d{1,3}\s*marks?\)?$", "", core).strip()
            if len(core) < MIN_COVERAGE_LINE:
                continue
            if core in claimed:
                continue
            # Partial credit for a wrapped line with noise stuck to it. The
            # student's handwriting merges into the OCR of a continuation line
            # ("...at the Land Registry. Read of Rechaza"), so the line never
            # matches exactly even though its question text was captured. A long
            # contiguous run shared with the extraction proves that; common words
            # scattered across the page would not, which is why this measures the
            # longest single block rather than word overlap.
            # Matched against ONE node at a time, never the concatenation of all
            # of them. Against the blob, a deleted part can borrow credit from a
            # similarly worded sibling - deleting "Specify items that should be
            # included in an attestation" went undetected because another
            # question reads "Specify 10 items that should be included in a
            # Condominium Declaration". Per node, that borrowing is impossible.
            #
            # autojunk=False matters too: on a long string the default heuristic
            # treats any character appearing in more than 1% of it as junk, which
            # is every letter, and the longest match collapses to a few chars.
            #
            # The floor sits below MIN_COVERAGE_LINE because a genuine item can
            # be shorter than that once its trailing handwriting is stripped
            # ("Management Corporation" under "(ii) Management Corporation st").
            # The match must also be ANCHORED at the start of the line. A wrapped
            # or noise-suffixed line begins with its real text and degrades at
            # the end ("...at the Land Registry. Read of Rechaza"). Borrowed
            # credit does not: deleting "Specify items that should be included in
            # an attestation" was absorbed by "Specify 10 items that should be
            # included in a Condominium Declaration" through a 35-character block
            # starting eight characters in. Requiring the shared run to start at
            # the beginning separates the two without loosening the threshold.
            need = max(15, int(len(core) * 0.5))
            covered = False
            for text in per_node:
                match = difflib.SequenceMatcher(
                    None, core, text, autojunk=False
                ).find_longest_match(0, len(core), 0, len(text))
                if match.size >= need and match.a <= 3:
                    covered = True
                    break
            if covered:
                continue
            missing.append((page_no, stripped))
    return missing


def normalize_lead_ins(raw: dict) -> list[str]:
    """Coerce a string `stem`/`fact_pattern` into the {text, quote} object shape.

    Six of the sixteen extractions returned `stem` as a bare string rather than
    the object the schema asks for. walk_nodes only yielded dicts, so those
    stems were skipped, and coverage then reported the very line they contained
    as dropped text. The stems were there the whole time; the validator was
    blind to them because it silently ignored a shape it did not expect.

    Coercing is safe - a bare string is unambiguously the text, and it doubles
    as its own quote - but it is reported rather than done quietly, because a
    field arriving in the wrong shape is worth knowing about.
    """
    coerced: list[str] = []
    for question in raw.get("questions", []) or []:
        for key in ("stem", "fact_pattern"):
            value = question.get(key)
            if isinstance(value, str) and value.strip():
                question[key] = {
                    "text": value.strip(),
                    "quote": value.strip(),
                    "pdf_page": (question.get("pdf_pages") or [None])[0],
                }
                coerced.append(f"Q{question.get('question_no')}.{key}")
    return coerced


@dataclass
class Report:
    paper_no: int
    questions: int = 0
    parts: int = 0
    items: int = 0
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    uncovered: list[tuple[int, str]] = field(default_factory=list)
    # Nodes whose marks were read off a line the OCR printed out of position.
    # The value is still usable; it just is not evidenced by the node's quote,
    # so it is counted rather than hidden.
    marks_reconstructed: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems and not self.uncovered


def validate(raw: dict, paper_no: int, pages: dict[int, str]) -> Report:
    report = Report(paper_no=paper_no)
    allowed = set(pages)

    for label, node in walk_nodes(raw):
        text, quote = node.get("text"), node.get("quote")
        if not _norm(text or ""):
            # A container with a bare label and no text of its own is legitimate:
            # paper 16 prints "A. 1.When is a notary exempted..." where "A." is
            # only a grouping label. Whether text was actually dropped is
            # answered by the coverage check, not by this one.
            if not (node.get("items") or []):
                report.problems.append(f"{label}: empty text")
            continue
        status = quote_status(quote or "", pages)
        if status == "absent" and quote_lines_verbatim(quote or "", pages):
            # Every line is real, they are just not adjacent in the file.
            status = "reassembled"
            report.marks_reconstructed.append(label)
        if status == "absent":
            report.problems.append(f"{label}: quote not in source: {_norm(quote)[:60]!r}")
        elif status == "truncated":
            report.warnings.append(f"{label}: quote is a fragment of its source line")
        page = node.get("pdf_page")
        if page is not None and page not in allowed:
            report.problems.append(f"{label}: pdf_page {page} outside paper range")
        if node.get("marks") is not None and node.get("marks_adjacent") is False:
            report.marks_reconstructed.append(label)

    for question in raw.get("questions", []) or []:
        report.questions += 1
        q_no = question.get("question_no")
        fact = question.get("fact_pattern")
        if isinstance(fact, dict) and re.match(r"^(write notes|answer|state)\b", _norm(fact.get("text", "")), re.I):
            report.warnings.append(f"Q{q_no}: fact_pattern looks like an instruction, not a scenario")

        for part in question.get("parts", []) or []:
            report.parts += 1
            part_id = str(part.get("part_id", ""))
            items = part.get("items") or []
            report.items += len(items)

            # The exact failure that produced "2a"/"2b" and lost the stem.
            if re.match(r"^[0-9ivx]+[a-d]$", part_id, re.I):
                report.problems.append(
                    f"Q{q_no}.{part_id}: flattened part id; the part's own stem was probably dropped"
                )
            if items and not _norm(part.get("text") or ""):
                # A warning, not a problem: some papers print a bare label with
                # no text of its own ("A. 1.When is a notary exempted..."), so an
                # empty part is legitimate there. Whether text was actually
                # dropped is answered by the coverage check, not by this one.
                report.warnings.append(f"Q{q_no}.{part_id}: part has items but no text of its own")

            # Group marks must stay on the part, not migrate to its first item.
            item_marks = [i.get("marks") for i in items]
            if items and part.get("marks") is None and any(m is not None for m in item_marks):
                if sum(1 for m in item_marks if m is not None) == 1:
                    report.warnings.append(
                        f"Q{q_no}.{part_id}: only one item carries marks; group marks may be misplaced"
                    )

        marks = [p.get("marks") for p in question.get("parts", []) or []]
        if question.get("marks") and marks and all(isinstance(m, int) for m in marks):
            total = sum(marks)
            if total != question["marks"]:
                report.warnings.append(
                    f"Q{q_no}: part marks sum to {total}, question states {question['marks']}"
                )

    numbers = [q.get("question_no") for q in raw.get("questions", []) or []]
    numbers = [n for n in numbers if isinstance(n, int)]
    if numbers:
        missing = sorted(set(range(1, max(numbers) + 1)) - set(numbers))
        if missing:
            report.warnings.append(f"question numbers missing: {missing}")

    report.uncovered = coverage(raw, pages)
    return report


# ── output ───────────────────────────────────────────────────────────────────
def write_outputs(paper_no: int, metadata: dict, raw: dict, report: Report) -> None:
    for directory in (QUESTIONS_DIR, METADATA_DIR, REPORTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    (METADATA_DIR / f"paper-{paper_no:02d}.metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    # The questions file carries the paper's identity as well as its number, so
    # a single file is self-describing without having to be joined back to
    # metadata to find out which sitting it belongs to.
    questions = {
        "schema_version": SCHEMA_VERSION,
        "paper_no": paper_no,
        "session": metadata.get("session"),
        "subject": metadata.get("subject"),
        "code": metadata.get("code"),
        "pdf_pages": metadata.get("pdf_pages"),
        "questions": raw.get("questions", []),
    }
    (QUESTIONS_DIR / f"paper-{paper_no:02d}.questions.json").write_text(
        json.dumps(questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (REPORTS_DIR / f"paper-{paper_no:02d}.report.json").write_text(
        json.dumps(
            {
                "paper_no": paper_no,
                "ok": report.ok,
                "counts": {
                    "questions": report.questions,
                    "parts": report.parts,
                    "items": report.items,
                },
                "problems": report.problems,
                "warnings": report.warnings,
                "marks_from_displaced_line": report.marks_reconstructed,
                "uncovered_lines": [{"pdf_page": p, "line": l} for p, l in report.uncovered],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def run(args: argparse.Namespace) -> int:
    raw_path = args.raw or (RAW_DIR / f"paper-{args.paper:02d}.extract.json")
    if not raw_path.is_file():
        print(f"error: no extraction at {raw_path}", file=sys.stderr)
        return 1
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_path.read_text(encoding="utf-8").strip())
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"error: {raw_path.name} is not valid JSON: {exc}", file=sys.stderr)
        return 1

    row = load_paper_row(args.paper)
    pages = load_pages(int(row["start_page"]), int(row["end_page"]))
    confidence = load_confidence()

    coerced = normalize_lead_ins(raw)
    report = validate(raw, args.paper, pages)
    if coerced:
        report.warnings.append(
            f"lead-in returned as a string, coerced to object shape: {', '.join(coerced)}"
        )
    metadata = derive_metadata(args.paper, row, pages, confidence)
    write_outputs(args.paper, metadata, raw, report)

    print(f"paper {args.paper} ({metadata['session']}), pages "
          f"{metadata['pdf_pages']['start']}-{metadata['pdf_pages']['end']}")
    print(f"  questions {report.questions} | parts {report.parts} | items {report.items}")
    if report.problems:
        print(f"  PROBLEMS {len(report.problems)}:")
        for problem in report.problems:
            print(f"    {problem}")
    if report.uncovered:
        print(f"  UNCOVERED source lines {len(report.uncovered)} (dropped text):")
        for page_no, line in report.uncovered[: (None if args.show_coverage else 8)]:
            print(f"    p{page_no}: {line[:96]}")
    if report.marks_reconstructed:
        print(f"  marks read off a displaced line: {len(report.marks_reconstructed)}"
              f" ({', '.join(report.marks_reconstructed[:6])})")
    if report.warnings:
        print(f"  warnings {len(report.warnings)}:")
        for warning in report.warnings:
            print(f"    {warning}")
    if report.ok:
        print("  clean: every source question line is accounted for")
    print("  unverified: matches the OCR text; the OCR itself is not verified "
          "and no lawyer has signed this off.")
    print(f"  output: {OUT_DIR}")
    return 0 if report.ok else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--paper", type=int, required=True)
    parser.add_argument("--raw", type=Path, default=None)
    parser.add_argument("--show-coverage", action="store_true", help="list every uncovered line")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
