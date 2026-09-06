"""Turn parsed Law College past papers into a gold-authoring worksheet.

The papers in data/evaluvation/parsed-pastpapers/ are exam questions, not
retrieval questions. Most parts cannot be answered by statute retrieval at all
-- "draw up the pedigree", "draft a deed of transfer" -- and of the ones that
can, many name a statute the corpus does not hold. Handing someone 589 raw
parts and asking for gold provision IDs would waste most of their time on parts
that were never going to produce any.

So this sorts them first, into three buckets:

  A  retrievable now   -- names a statute the corpus holds, or names no statute
                          but is a legal-rule question. Gold provision IDs are
                          expected. These extend Recall and MRR measurement.

  B  evidence absent   -- names a statute the corpus does not hold. Gold is the
                          fact of absence: no provision IDs, corpus_coverage
                          'absent'. These are worth more than they look. Every
                          existing evaluation question has complete coverage,
                          which makes the answerability check unmeasurable --
                          a claim of "complete" is never wrong when the evidence
                          is always there. Bucket B is what gives that metric a
                          negative class. It also doubles as the ranked backlog
                          for corpus ingestion.

  C  not retrieval     -- drafting, pedigree drawing, arithmetic, or advice with
                          no statutory rule to find. Excluded, with the reason
                          recorded rather than silently dropped.

The bucket is a SUGGESTION from a regex over the question text. It is wrong
often enough that a human must confirm every row; the worksheet has a separate
column for the confirmed bucket so the suggestion and the decision stay
distinct and disagreements can be counted.

Two subcommands:

    triage   read the papers, write worksheet.csv and a summary
    build    read a filled-in worksheet, emit questions.jsonl and gold.jsonl
             in the format the experiment already consumes

Free, offline, no API calls.

Usage:
    uv run python experiments/HiREC-inspired-retrieval/pastpaper_triage.py triage
    uv run python experiments/HiREC-inspired-retrieval/pastpaper_triage.py build
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hirec_config as config  # noqa: E402
import hirec_index  # noqa: E402

PAPERS_DIR = (config.ROOT / "data" / "evaluvation" / "parsed-pastpapers"
              / "questions")
OUTPUT_DIR = config.ROOT / "data" / "evaluvation" / "pastpaper-triage"

BUCKET_A = "A-retrievable"
BUCKET_B = "B-evidence-absent"
BUCKET_C = "C-not-retrieval"

# Names as the papers write them, mapped to the act_title the corpus uses.
# Deliberately explicit rather than fuzzy-matched: "Registration of Documents
# Ordinance" and "Registration of Old Deeds and Instruments Ordinance" are
# different statutes and a fuzzy match would happily conflate them.
ALIASES = {
    "registration of title act": "Registration of Title Act",
    "title registration act": "Registration of Title Act",
    "land (restriction on alienation) act": "Land (Restrictions on Alienation) Act",
    "land (restrictions on alienation) act": "Land (Restrictions on Alienation) Act",
    "apartment ownership law": "Apartment Ownership Law",
    "matrimonial rights and inheritance ordinance":
        "Matrimonial Rights and Inheritance Ordinance",
    "jaffna matrimonial rights and inheritance ordinance":
        "Jaffna Matrimonial Rights and Inheritance Ordinance",
    "kandyan succession ordinance": "Kandyan Succession Ordinance",
    "muslim intestate succession ordinance": "Muslim Intestate Succession Ordinance",
    "wills ordinance": "Wills Ordinance",
    "companies act": "Companies Act",
    "survey act": "Survey Act",
    "urban development authority act": "Urban Development Authority Act",
    "national housing act": "National Housing Act",
    "thesawalamai pre-emption ordinance": "Thesawalamai Pre-emption Ordinance",
    "nindagama lands act": "Nindagama Lands Act",
    "buddhist temporalities ordinance": "Buddhist Temporalities Ordinance",
    "state land (claims) ordinance": "State Land (Claims) Ordinance",
    "land grants (special provisions) act": "Land Grants (Special Provisions) Act",
    "registration of old deeds and instruments ordinance":
        "Registration of Old Deeds and Instruments Ordinance",
    "land registers (reconstructed folios) ordinance":
        "Land Registers (Reconstructed Folios) Ordinance",
    "deeds and documents (execution before public officers) ordinance":
        "Deeds and Documents (Execution before Public Officers) Ordinance",
    "tea and rubber estates (control of fragmentation) act":
        "Tea and Rubber Estates (Control of Fragmentation) Act",
    # The corpus grew from 21 to 39 acts after this list was first written
    # (see paper-01/paper-02 review notes in worksheet.csv); these eight were
    # on KNOWN_ABSENT below and are now present. Moved here, not deleted from
    # KNOWN_ABSENT's history -- if the corpus is ever queried at an older
    # fingerprint, check this list's date against it before trusting either.
    "registration of documents ordinance": "Registration of Documents Ordinance",
    "prevention of frauds ordinance": "Prevention of Frauds Ordinance",
    "mortgage act": "Mortgage Act",
    "land development ordinance": "Land Development Ordinance",
    "trusts ordinance": "Trusts Ordinance",
    "stamp duty act": "Stamp Duty Act",
    "civil procedure code": "Civil Procedure Code",
    "state lands ordinance": "State Lands Ordinance",
}

# Statute names that appear in the papers and are known NOT to be in the
# corpus. Listing them explicitly means bucket B is a positive identification
# rather than "the alias table did not match", which would also catch typos.
#
# Verify against the corpus before trusting this list -- it has already gone
# stale twice (paper-01 review: prevention of frauds ordinance, mortgage act,
# stamp duty act, state lands ordinance; paper-02 review: registration of
# documents ordinance, land development ordinance, trusts ordinance, civil
# procedure code). Re-check with:
#   python -c "import json; acts={json.loads(l)['act_title'] for l in
#   open('experiments/koblex-inspired-retrieval/data/statute.jsonl',
#   encoding='utf-8')}; print(sorted(acts))"
KNOWN_ABSENT = [
    "notaries ordinance",
    "partition act",
    "partition law",
    "crown lands ordinance",
    "land acquisition act",
    "condominium management authority law",
    "rent act",
    "agrarian development act",
]

# Verbs that mark a part as a drafting or computation exercise rather than a
# question about what the law says.
NOT_RETRIEVAL_MARKERS = [
    "draw up the pedigree", "draw the pedigree", "draft ", "prepare a deed",
    "prepare the deed", "write out", "engross", "compute the", "calculate the",
    "draw up a", "prepare an", "attestation clause for",
]

STATUTE_RE = re.compile(
    r"\b([A-Z][A-Za-z()'\-]*(?:\s+(?:of|and|on|before|the|to)\s+|\s+|\([A-Za-z ]+\)\s*)"
    r"{0,7}?(?:Act|Ordinance|Law|Code))\b")
SECTION_RE = re.compile(r"\bsections?\s+(\d+[A-Za-z]?)"
                        r"(?:\s*(?:to|-|and)\s*(\d+[A-Za-z]?))?", re.I)


def normalise(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip().lower()
    name = re.sub(r"^(the|our|said|amended)\s+", "", name)
    return name


def find_statutes(text: str) -> list[str]:
    """Statute names in the text, matched against the curated lists first.

    An earlier version captured names with a generic regex and then tried to
    trim the question words it swept up ("Will the provisions of Partition
    Act"). Trimming at the last " of " destroyed every legitimate name that
    contains one: "Registration of Title Act" became "title act", so two of the
    corpus's own statutes were reported as absent. Matching known names as
    whole strings cannot make that mistake, and the corpus title list plus the
    known-absent list already cover almost everything these papers cite.

    The generic regex is still run afterwards, to surface statutes on neither
    list, but only over the spans no known name claimed.
    """
    haystack = normalise(text)
    if not haystack:
        return []

    found: list[str] = []
    spans: list[tuple[int, int]] = []
    # Longest first, so "jaffna matrimonial rights and inheritance ordinance"
    # wins over "matrimonial rights and inheritance ordinance".
    for name in sorted(set(ALIASES) | set(KNOWN_ABSENT), key=len, reverse=True):
        start = haystack.find(name)
        if start == -1:
            continue
        end = start + len(name)
        if any(s < end and start < e for s, e in spans):
            continue
        spans.append((start, end))
        found.append(name)

    for match in STATUTE_RE.finditer(text or ""):
        if any(s < match.end() and match.start() < e for s, e in spans):
            continue
        name = normalise(match.group(1))
        # Strip only a leading question fragment, never an internal " of ".
        name = re.sub(
            r"^(?:will|what|which|why|how|discuss|explain|state|describe)\b"
            r"[\w\s]*?\b(?:of|under|by|in)\s+", "", name)
        if len(name) > 4:
            found.append(name)

    return list(dict.fromkeys(found))


def find_sections(text: str) -> list[str]:
    out = []
    for match in SECTION_RE.finditer(text or ""):
        first, last = match.group(1), match.group(2)
        out.append(f"{first}-{last}" if last else first)
    return list(dict.fromkeys(out))


def classify(text: str, statutes: list[str]) -> tuple[str, str]:
    """Returns (suggested_bucket, why)."""
    lowered = (text or "").lower()

    for marker in NOT_RETRIEVAL_MARKERS:
        if marker in lowered:
            return BUCKET_C, f"drafting/computation task ({marker.strip()!r})"

    in_corpus = [s for s in statutes if s in ALIASES]
    absent = [s for s in statutes
              if any(a in s or s in a for a in KNOWN_ABSENT)]

    if in_corpus and not absent:
        return BUCKET_A, f"names corpus statute(s): {', '.join(in_corpus)}"
    if in_corpus and absent:
        return BUCKET_A, (f"names both: in corpus {', '.join(in_corpus)}; "
                          f"absent {', '.join(absent)} -- split or mark partial")
    if absent:
        return BUCKET_B, f"names statute(s) not in corpus: {', '.join(absent)}"
    if statutes:
        return BUCKET_B, f"names unrecognised statute(s): {', '.join(statutes)}"
    return BUCKET_C, "no statute named; confirm whether a legal rule is sought"


WORKSHEET_COLUMNS = [
    # generated -- do not edit
    "part_uid", "paper_no", "question_no", "part_id", "marks",
    "suggested_bucket", "why_suggested", "named_statutes", "named_sections",
    "question_text", "fact_pattern",
    # filled in by the reviewer
    "bucket", "gold_provisions", "citations", "question_type", "n_hops",
    "corpus_coverage", "answer", "notes", "verified_by", "verified_date",
]

GENERATED_COLUMNS = 11


def _text_of(value) -> str:
    """stem and fact_pattern are both {text, quote, pdf_page} or null."""
    if isinstance(value, dict):
        return value.get("text") or ""
    return value or ""


def load_parts() -> list[dict]:
    rows = []
    for path in sorted(PAPERS_DIR.glob("*.questions.json")):
        paper = json.loads(path.read_text(encoding="utf-8"))
        for question in paper["questions"]:
            fact = _text_of(question.get("fact_pattern"))
            stem = _text_of(question.get("stem"))
            background = " ".join(p for p in (stem, fact) if p).strip()
            for part in question.get("parts") or []:
                text = part.get("text") or ""
                # The stem carries the governing statute for a whole question
                # ("Write notes on the following according to the Apartment
                # Ownership Law"), so a part read alone would look statute-less.
                statutes = (find_statutes(text) or find_statutes(stem)
                            or find_statutes(fact))
                bucket, why = classify(text, statutes)
                rows.append({
                    "part_uid": (f"paper-{paper['paper_no']:02d}"
                                 f"/q{question['question_no']}/{part['part_id']}"),
                    "paper_no": paper["paper_no"],
                    "question_no": question["question_no"],
                    "part_id": part["part_id"],
                    "marks": part.get("marks") or "",
                    "suggested_bucket": bucket,
                    "why_suggested": why,
                    "named_statutes": "; ".join(statutes),
                    "named_sections": "; ".join(find_sections(text)),
                    "question_text": text,
                    "fact_pattern": background,
                })
    return rows


def cmd_triage(args) -> int:
    if not PAPERS_DIR.is_dir():
        print(f"missing {PAPERS_DIR}", file=sys.stderr)
        return 1
    rows = load_parts()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    worksheet = OUTPUT_DIR / "worksheet.csv"

    if worksheet.exists() and not args.overwrite:
        print(f"{config.display_path(worksheet)} already exists. It may contain "
              f"reviewed rows.\nPass --overwrite only if you are certain that "
              f"work is saved elsewhere.", file=sys.stderr)
        return 1

    with worksheet.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WORKSHEET_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({**{c: "" for c in WORKSHEET_COLUMNS}, **row})

    counts = Counter(r["suggested_bucket"] for r in rows)
    by_paper = Counter(r["paper_no"] for r in rows)
    absent_named = Counter()
    for row in rows:
        if row["suggested_bucket"] == BUCKET_B:
            for name in row["named_statutes"].split("; "):
                if name:
                    absent_named[name] += 1

    summary = {
        "parts": len(rows),
        "papers": len(by_paper),
        "suggested_buckets": dict(counts),
        "most_named_absent_statutes": absent_named.most_common(15),
        "note": (
            "Buckets are suggestions from a regex and must each be confirmed by "
            "a human. Bucket B is not waste: it is the negative class the "
            "answerability metric currently lacks, and the ranked backlog for "
            "corpus ingestion."),
    }
    config.write_json(summary, OUTPUT_DIR / "triage-summary.json")

    print(f"parts        : {len(rows)} across {len(by_paper)} papers")
    for bucket in (BUCKET_A, BUCKET_B, BUCKET_C):
        print(f"  {bucket:20s}: {counts.get(bucket, 0)}")
    print()
    print("most-named statutes the corpus does not hold:")
    for name, count in absent_named.most_common(10):
        print(f"  {count:3d}  {name}")
    print()
    print(f"wrote {config.display_path(worksheet)}")
    print(f"wrote {config.display_path(OUTPUT_DIR / 'triage-summary.json')}")
    return 0


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #

def cmd_build(args) -> int:
    worksheet = args.worksheet
    if not worksheet.is_file():
        print(f"missing {worksheet}; run the triage subcommand first",
              file=sys.stderr)
        return 1

    with worksheet.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    reviewed = [r for r in rows if (r.get("bucket") or "").strip()]
    if not reviewed:
        print("no rows have a confirmed `bucket`; nothing to build.",
              file=sys.stderr)
        return 1

    try:
        index = hirec_index.Bm25Index(args.db)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    with index:
        corpus_ids = index.node_ids()

    questions, gold, problems = [], [], []
    for row in reviewed:
        bucket = row["bucket"].strip()
        if bucket.startswith("C"):
            continue
        uid = row["part_uid"]
        qid = uid.replace("/", "-")
        provisions = [p.strip() for p in
                      (row.get("gold_provisions") or "").split(";") if p.strip()]
        coverage = (row.get("corpus_coverage") or "").strip()

        if bucket.startswith("A"):
            if not provisions:
                problems.append(f"{uid}: bucket A but no gold_provisions")
                continue
            unknown = [p for p in provisions if p not in corpus_ids]
            if unknown:
                problems.append(f"{uid}: gold_provisions do not exist: {unknown}")
                continue
            coverage = coverage or "complete"
        elif bucket.startswith("B"):
            if provisions:
                problems.append(
                    f"{uid}: bucket B (evidence absent) but gold_provisions "
                    f"were given: {provisions}")
                continue
            coverage = coverage or "absent"
        else:
            problems.append(f"{uid}: unrecognised bucket {bucket!r}")
            continue

        if not (row.get("verified_by") or "").strip():
            problems.append(f"{uid}: no verified_by; every row needs an owner")
            continue

        try:
            n_hops = int(row.get("n_hops") or (len(provisions) or 1))
        except ValueError:
            problems.append(f"{uid}: n_hops {row.get('n_hops')!r} is not a number")
            continue

        questions.append({
            "question_id": qid,
            "paper_id": uid.split("/")[0],
            "background": row.get("fact_pattern") or "",
            "question": row.get("question_text") or "",
        })
        gold.append({
            "question_id": qid,
            "question_type": (row.get("question_type") or "application").strip(),
            "answer": row.get("answer") or "",
            "relevant_provisions": provisions,
            "citations": [c.strip() for c in
                          (row.get("citations") or "").split(";") if c.strip()],
            "n_hops": n_hops,
            "corpus_coverage": coverage,
        })

    if problems:
        print(f"{len(problems)} row(s) could not be built:", file=sys.stderr)
        for line in problems:
            print(f"  x {line}", file=sys.stderr)
        print("\nNothing was written. Fix the rows above and run again.",
              file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.write_jsonl(questions, OUTPUT_DIR / "pastpaper_questions.jsonl")
    config.write_jsonl(gold, OUTPUT_DIR / "pastpaper_gold.jsonl")

    coverage_counts = Counter(g["corpus_coverage"] for g in gold)
    print(f"reviewed rows : {len(reviewed)}")
    print(f"built         : {len(questions)} questions")
    print(f"coverage      : {dict(coverage_counts)}")
    print(f"wrote {config.display_path(OUTPUT_DIR / 'pastpaper_questions.jsonl')}")
    print(f"wrote {config.display_path(OUTPUT_DIR / 'pastpaper_gold.jsonl')}")
    print()
    print("Now validate them:")
    print("  uv run python experiments/HiREC-inspired-retrieval/"
          "validate_dataset.py \\")
    print(f"      --questions {config.display_path(OUTPUT_DIR / 'pastpaper_questions.jsonl')} \\")
    print(f"      --gold {config.display_path(OUTPUT_DIR / 'pastpaper_gold.jsonl')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    triage = sub.add_parser("triage", help="write the authoring worksheet")
    triage.add_argument("--overwrite", action="store_true")
    triage.set_defaults(func=cmd_triage)

    build = sub.add_parser("build", help="turn a filled worksheet into datasets")
    build.add_argument("--worksheet", type=Path,
                       default=OUTPUT_DIR / "worksheet.csv")
    build.add_argument("--db", type=Path, default=config.INDEX_DB_PATH)
    build.set_defaults(func=cmd_build)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
