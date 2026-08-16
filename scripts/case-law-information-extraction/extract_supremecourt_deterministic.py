"""Deterministic (no-LLM, no-network) extraction of case data from the
downloaded Supreme Court judgment PDFs (data/supremecourt.lk/SCLR/) into one
CSV: data/supremecourt.lk/case_data.csv.

Everything here is regex/structure-based over the PDF's own text layer plus
the scrape's manifest.csv. It deliberately does NOT attempt to identify the
court's ratio decidendi (that's a language-understanding judgment call, not
a pattern match — see extract_supremecourt_pdfs.py, the separate LLM-based
pipeline, for that). `principle_statement` and `final_order_paragraph` here
are honest, clearly-labeled proxies: a marker-phrase scan for explicit
rule-signaling language, and the verbatim final operative paragraph. Neither
is a verified legal rule.

No cell in the output is ever an empty string. Every field has a documented,
literal fallback value (see the plan / README) instead — real coverage is
reported via the `extraction_flags` column and the end-of-run summary, not
hidden behind a blank.

Usage:
  python extract_supremecourt_deterministic.py --limit 30   # smoke test
  python extract_supremecourt_deterministic.py               # full corpus
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import pypdfium2 as pdfium

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import build_case_citation_links as bcl  # noqa: E402
import harvest_courts_caselaw as hcc  # noqa: E402 -- reuses its proven conveyancing keyword gate

MANIFEST = REPO_ROOT / "data" / "supremecourt.lk" / "manifest.csv"
PDF_ROOT = REPO_ROOT / "data" / "supremecourt.lk"
TEXT_CACHE = Path(__file__).resolve().parent / "output" / "supremecourt-lk" / "text-cache"
OUT_CSV = REPO_ROOT / "data" / "supremecourt.lk" / "case_data.csv"
TEXT_CACHE.mkdir(parents=True, exist_ok=True)

FIELDS = [
    "case_id", "case_no", "case_type", "court", "year", "date", "parties",
    "judge_primary", "coram", "lower_court_reference", "disposition",
    "disposition_evidence", "statutes_cited", "principle_statement",
    "final_order_paragraph", "pdf_url", "filename", "sha256", "text_chars",
    "is_conveyancing", "conveyancing_signal", "extraction_flags",
]

# Conveyancing classifier: statute-citation signal OR keyword signal.
#
# Statute citation alone over-counts: the closed catalogue includes general
# procedural statutes (Evidence Ordinance, Civil Procedure Code, Companies
# Act) that get cited in nearly every civil appeal regardless of subject
# matter -- measured 331/424 "statute cited, no keyword hit" cases cited
# ONLY these. Excluded here so a citation only counts when it's to a
# substantive conveyancing statute.
GENERIC_STATUTES = {"SRC029", "SRC030", "SRC031", "SRC032"}  # Evidence Ord., CPC, Companies Act x2

# Keyword signal: reused harvest_courts_caselaw.STRONG/THRESHOLD, scanned over
# the FULL judgment text. Tested restricting this to just the caption/opening
# (first 2.5-4K chars): hit rate collapsed from 35.9% to 10-19%, because the
# substantive legal issue is usually developed in the reasoning, not announced
# in the caption -- so the full-text scan is kept, not narrowed.

# ---------------------------------------------------------------- patterns

DISPOSITION_PATTERNS = [
    (r"leave\s+to\s+appeal\s+is\s+(?:hereby\s+)?granted", "leave-granted"),
    (r"leave\s+to\s+appeal\s+is\s+(?:hereby\s+)?refused", "leave-refused"),
    (r"appeal\s+is\s+(?:hereby\s+)?allowed", "allowed"),
    (r"appeal\s+is\s+(?:hereby\s+)?dismissed", "dismissed"),
    (r"application\s+is\s+(?:accordingly\s+)?(?:hereby\s+)?dismissed", "dismissed"),
    (r"application\s+is\s+(?:accordingly\s+)?(?:hereby\s+)?allowed", "allowed"),
    (r"application\s+is\s+(?:accordingly\s+)?refused", "refused"),
    (r"conviction.{0,30}(?:set\s+aside|quashed)", "set-aside"),
    (r"set\s+aside", "set-aside"),
    (r"remitted|sent\s+back", "remitted"),
    (r"(?:is|is\s+thus|is\s+hereby)\s+affirmed", "affirmed"),
    (r"judgment.{0,20}affirmed|affirmed", "affirmed"),
    (r"acquitted", "acquitted"),
    (r"no\s+violation\s+of\s+.{0,40}fundamental\s+rights?", "dismissed"),
    (r"fundamental\s+rights?.{0,60}(?:has|have)\s+been\s+violated", "relief-granted"),
    (r"(?:direct|order|award).{0,100}(?:pay|compensation)", "relief-granted"),
    (r"(?:a\s+)?further\s+sum\s+of.{0,80}(?:costs?|compensation)", "relief-granted"),
]

PRINCIPLE_MARKERS = [
    r"it\s+is\s+(?:now\s+)?(?:well\s+)?settled\s+(?:law\s+)?that",
    r"it\s+is\s+trite\s+law\s+that",
    r"the\s+(?:established\s+)?(?:law|principle|position)\s+(?:in\s+law\s+)?is\s+that",
    r"the\s+established\s+principle\s+is",
    r"this\s+court\s+has\s+(?:consistently\s+)?held\s+that",
    r"it\s+has\s+been\s+held\s+(?:by\s+this\s+court\s+)?(?:in\s+a\s+(?:long\s+)?(?:line|series)\s+of\s+cases\s+)?that",
    r"the\s+applicable\s+(?:test|principle)\s+(?:in\s+(?:this|such)\s+(?:a\s+)?case\s+)?is",
    r"the\s+correct\s+(?:position|test)\s+in\s+law\s+is",
    r"the\s+principle\s+applicable\s+(?:to|in)\s+(?:this|such)\s+(?:a\s+)?cases?\s+is",
    r"it\s+is\s+a\s+well[\s-]established\s+principle\s+that",
    r"the\s+test\s+to\s+be\s+applied\s+is",
    r"it\s+is\s+a\s+cardinal\s+principle\s+(?:of\s+law\s+)?that",
    r"the\s+law\s+(?:on\s+this\s+point|in\s+this\s+regard|is\s+this\s+regard)\s+is\s+(?:well\s+)?settled",
    r"the\s+onus\s+(?:of\s+proof\s+)?(?:lies|rests|is)\s+(?:on|with|upon)",
    r"the\s+burden\s+of\s+proof\s+(?:lies|rests)\s+(?:on|with|upon)",
]

CASE_TYPE_RX = re.compile(r"^SC/([A-Z]+(?:/[A-Z]+)*)", re.I)


def case_type_from_case_no(case_no: str) -> str:
    cleaned = case_no.split(",")[0].strip().upper().replace(" ", "")
    m = CASE_TYPE_RX.match(cleaned)
    return m.group(1).replace("/", "-") if m else "OTHER"


def extract_coram(text: str) -> list[str]:
    lines = text.splitlines()
    names: list[str] = []
    for i, line in enumerate(lines):
        if re.search(r"judge\s+of\s+the\s+supreme\s+court", line, re.I):
            for nxt in lines[i + 1: i + 4]:
                nxt = nxt.strip()
                if not nxt or re.match(r"^(i\s+agree\.?|sgd\.?\d*|\d+)$", nxt, re.I):
                    continue
                if len(nxt) < 4 or not re.search(r"[A-Za-z]{3,}", nxt):
                    continue
                names.append(nxt)
                break
    seen: set[str] = set()
    out = []
    for name in names:
        key = name.lower()
        if key not in seen:
            seen.add(key)
            out.append(name)
    return out


def classify_disposition(text: str) -> tuple[str, str, bool]:
    tail = text[-6000:].lower()
    for pat, label in DISPOSITION_PATTERNS:
        m = re.search(pat, tail)
        if m:
            evidence = tail[max(0, m.start() - 150): m.end() + 50]
            return label, re.sub(r"\s+", " ", evidence).strip(), False
    return "unclassified", re.sub(r"\s+", " ", tail[-300:]).strip(), True


def extract_principle_statement(text: str, max_candidates: int = 3) -> str:
    spans: list[tuple[int, int]] = []
    candidates: list[str] = []
    for pat in PRINCIPLE_MARKERS:
        for m in re.finditer(pat, text, re.I):
            start, end = bcl.sentence_bounds(text, m.start(), m.end(), radius=700)
            # pull in the following sentence too, for context beyond the marker clause
            next_period = text.find(". ", end, end + 400)
            if 0 <= next_period < end + 400:
                end = next_period + 1
            if any(abs(start - s) < 60 for s, _ in spans):
                continue  # same passage already captured via another marker
            spans.append((start, end))
            candidates.append(re.sub(r"\s+", " ", text[start:end]).strip())
            if len(candidates) >= max_candidates:
                return " || ".join(candidates)
    return " || ".join(candidates)


def extract_final_order(text: str) -> str:
    m = re.search(r"judge\s+of\s+the\s+supreme\s+court", text, re.I)
    body = text[: m.start()] if m else text
    tail = body[-900:]
    idx = tail.find(". ")
    if 0 <= idx < 300:
        tail = tail[idx + 2:]
    return re.sub(r"\s+", " ", tail).strip()


def extract_lower_court_reference(text: str) -> str:
    head = text[:1800]
    for line in head.splitlines():
        line_s = line.strip()
        if not line_s or "SUPREME" in line_s.upper():
            continue
        if re.search(r"\b(D\.?\s?C\.?|H\.?\s?C\.?|C\.?\s?A\.?|M\.?\s?C\.?|L\.?\s?T\.?|HCCA|HCALT)\b.{0,15}\d", line_s, re.I):
            return re.sub(r"\s+", " ", line_s)
    return ""

# ------------------------------------------------------------- statute citations (reused)


def build_identity_map() -> dict[tuple[str, str], list[dict]]:
    identity_map: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in bcl.read_csv(bcl.PROCESSED / "source-registry.csv"):
        number = row.get("act_or_ordinance_no", "").strip()
        year = row.get("year", "").strip()
        if row["source_type"] in bcl.LAW_TYPES and number and year and year != "0":
            identity_map[(number, year)].append(row)
    return identity_map


def statutes_cited_for_text(text: str, law_matchers: list[dict], identity_map: dict) -> list[str]:
    law_mentions = []
    folded = text.casefold()
    for matcher in law_matchers:
        if matcher["anchor"] not in folded:
            continue
        for m in matcher["title_rx"].finditer(text):
            law_mentions.append({"start": m.start(), "end": m.end(),
                                 "group": matcher["group"], "candidates": matcher["candidates"]})
    for identity in bcl.LAW_IDENTITY_RX.finditer(text):
        candidates = identity_map.get((identity.group(1), identity.group(2)), [])
        if candidates:
            law_mentions.append({"start": identity.start(), "end": identity.end(),
                                 "group": f"identity-{identity.group(1)}-{identity.group(2)}",
                                 "candidates": candidates})
    found: set[str] = set()
    for section in bcl.SECTION_RX.finditer(text):
        mention, _method, _reason = bcl.choose_law_mention(text, section, law_mentions)
        if mention is None:
            continue
        context = text[max(0, mention["start"] - 250): min(len(text), mention["end"] + 250)]
        law, _reason2 = bcl.resolve_law(mention["candidates"], context)
        if law is None:
            continue
        for number in bcl.section_numbers(section):
            found.add(f"{law['source_id']}-s{number}")
    return sorted(found)


def classify_conveyancing(text: str, statutes: list[str]) -> tuple[bool, str]:
    """conveyancing = substantive statute citation OR keyword threshold.
    Returns (is_conveyancing, signal_label) -- see the module-level comment
    by GENERIC_STATUTES for why each half is defined the way it is."""
    substantive = any(ref.split("-s")[0] not in GENERIC_STATUTES for ref in statutes)
    keyword = len(hcc.STRONG.findall(text)) >= hcc.THRESHOLD if text else False
    if substantive and keyword:
        return True, "statute+keyword"
    if keyword:
        return True, "keyword-only"
    if substantive:
        return True, "statute-only"
    return False, "none"

# ---------------------------------------------------------------- io helpers


def load_manifest_rows(source: str = "SCLR") -> list[dict]:
    with MANIFEST.open(encoding="utf-8") as fh:
        return [row for row in csv.DictReader(fh)
                if row.get("source") == source and row.get("status") == "ok"]


def pdf_to_text(row: dict) -> str:
    cache_file = TEXT_CACHE / (row["filename"] + ".txt")
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="ignore")
    pdf_path = PDF_ROOT / "SCLR" / row["year"] / row["filename"]
    try:
        doc = pdfium.PdfDocument(str(pdf_path))
        text = "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] pdf parse {pdf_path}: {exc}")
        return ""
    cache_file.write_text(text, encoding="utf-8")
    return text


def build_row(row: dict, law_matchers: list[dict], identity_map: dict) -> dict:
    flags: list[str] = []
    text = pdf_to_text(row)
    if not text:
        flags.append("text=empty")

    case_id = f"sc-{row['year']}-{Path(row['filename']).stem}"
    case_type = case_type_from_case_no(row["case_no"])

    coram = extract_coram(text) if text else []
    if not coram:
        coram = [row["judge"] or "not-stated"]
        flags.append("coram=fallback-manifest")

    disposition, evidence, was_fallback = classify_disposition(text) if text else ("unclassified", "not-stated", True)
    if was_fallback:
        flags.append("disposition=unclassified")
    evidence = evidence or "not-stated"

    statutes = statutes_cited_for_text(text, law_matchers, identity_map) if text else []
    statutes_str = "; ".join(statutes) if statutes else "none"
    is_conveyancing, conveyancing_signal = classify_conveyancing(text, statutes)

    principle = extract_principle_statement(text) if text else ""
    if not principle:
        principle = "not-stated"
        flags.append("principle_statement=not-stated")

    final_order = extract_final_order(text) if text else ""
    if not final_order:
        final_order = "not-stated"
        flags.append("final_order_paragraph=not-stated")

    lower_ref = extract_lower_court_reference(text) if text else ""
    if not lower_ref:
        lower_ref = "not-stated"
        flags.append("lower_court_reference=not-stated")

    parties = row["parties"].strip() or "not-stated"
    if parties == "not-stated":
        flags.append("parties=not-stated")

    return {
        "case_id": case_id,
        "case_no": row["case_no"],
        "case_type": case_type,
        "court": "Supreme Court",
        "year": row["year"],
        "date": row["date"] or "not-stated",
        "parties": parties,
        "judge_primary": row["judge"] or "not-stated",
        "coram": "; ".join(coram),
        "lower_court_reference": lower_ref,
        "disposition": disposition,
        "disposition_evidence": evidence,
        "statutes_cited": statutes_str,
        "principle_statement": principle,
        "final_order_paragraph": final_order,
        "pdf_url": row["pdf_url"],
        "filename": row["filename"],
        "sha256": row["sha256"],
        "text_chars": str(len(text)),
        "is_conveyancing": str(is_conveyancing),
        "conveyancing_signal": conveyancing_signal,
        "extraction_flags": "; ".join(flags) if flags else "none",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0, help="max cases (0=all)")
    ap.add_argument("--year", action="append", help="restrict to one or more years; repeatable")
    args = ap.parse_args()

    rows = load_manifest_rows("SCLR")
    if args.year:
        wanted = set(args.year)
        rows = [r for r in rows if r["year"] in wanted]
    if args.limit:
        rows = rows[: args.limit]

    law_matchers = bcl.build_law_matcher()
    identity_map = build_identity_map()

    out_rows = []
    flag_counts: dict[str, int] = defaultdict(int)
    for i, row in enumerate(rows, 1):
        rec = build_row(row, law_matchers, identity_map)
        out_rows.append(rec)
        for flag in rec["extraction_flags"].split("; "):
            if flag != "none":
                flag_counts[flag.split("=")[0]] += 1
        if i % 200 == 0:
            print(f"  processed {i}/{len(rows)}", flush=True)

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)

    blanks = sum(1 for rec in out_rows for v in rec.values() if v == "")
    print(f"\nWrote {len(out_rows)} rows -> {OUT_CSV}")
    print(f"Empty-string cells: {blanks} (should be 0)")
    print("Fallback rate per field (out of total rows):")
    for field, count in sorted(flag_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {field}: {count}/{len(out_rows)} ({count / len(out_rows):.1%})" if out_rows else f"  {field}: {count}")


if __name__ == "__main__":
    main()
