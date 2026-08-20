"""Find where each exam paper starts in the OCR'd Law College past-paper bundle.

`preprocess-pdf.pdf` is a stack of Conveyancing (LW 307) past papers scanned end
to end, so "which paper is this page from" has no answer until the boundaries are
recovered. Every paper opens with the same header block -- college, the
ATTORNEYS-AT-LAW FINAL YEAR EXAMINATION line and its session, the subject and
course code, the three-hour limit, and the "answer SIX questions" rubric -- and
that block is what this script looks for.

It scores rather than pattern-matches because the scans are uneven. The header
survives OCR intact on a good page and arrives as "IRNEYS-AT-LAW FINAL YEAR
EXAMINATION" or "CONVEYAN W 30" on a bad one, so requiring any single line would
miss real starts, and requiring only one would fire on body text. Several
independent signals, weighted and thresholded, degrade the way the scans do.

Question numbering would be the natural second signal -- every paper restarts at
Question No. 01 -- but it does not survive: the headings come through as
"QuestiNoo. 0n8", "uestioNno.0:" and "Sestin No.03", and a regex loose enough to
catch those also matches sub-question numbers and mark allocations. It is not
used, and the boundaries it would have confirmed are reported as unconfirmed
instead.

What that leaves is a gap check. The papers run to a steady length, so a stretch
of pages far longer than the rest means a header that did not survive. Those are
reported as suspected starts with no page number attached, because the evidence
says a boundary exists in there without saying where. Nothing here is a verified
boundary: it is OCR output about OCR output, and it stays status=unverified until
someone opens the PDF and looks.

Usage:
    uv run python data/evaluvation/find_paper_starts.py
    uv run python data/evaluvation/find_paper_starts.py --min-score 4 --csv papers.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_PDF = HERE / "preprocess-pdf.pdf"
DEFAULT_CSV = HERE / "papers.csv"
DEFAULT_OVERRIDES = HERE / "paper-starts-overrides.csv"

# The header sits at the top of the page. Body text mentioning a deed dated "1st
# May 2013" is not a session line, and reading the whole page for one is how you
# get a paper dated 1998 out of a 2019 sitting.
HEADER_LINES = 8

MONTHS = (
    "JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER"
)

# Weights say how much a signal narrows things down, not how visible it is. The
# rubric line is worth as much as the college name because it survives damage
# that flattens the letterhead, and it is the only thing left on the worst starts.
SIGNALS: tuple[tuple[str, str, int], ...] = (
    ("college", r"LAW\s*COLL\w*", 2),
    ("attorneys", r"[A-Z]{0,3}RNEYS\s*-?\s*AT\s*-?\s*LAW", 2),
    ("examination", r"EXAMINATION", 1),
    ("subject", r"CONVEYAN\w*", 1),
    ("code", r"\(?\s*L\s*W\s*3?\s*0?\s*7?\s*\)?", 0),  # scored separately, see below
    ("time", r"TI\w{0,3}\W{0,4}3?\s*M?\s*HOUR", 1),
    ("rubric", r"legibl|[Ii]llegibl|penali[sz]|handwriting", 2),
    ("answer_six", r"(?:[Aa]nswer|swer|r)\s+(?:SIX|Six|six)\b", 2),
    ("compulsory", r"compulsor|is\s+com\b|compn\b", 1),
    # The mark split appears only in the header, and it is what is left on the
    # worst starts -- page 44 keeps "carries 25 / other question carries 15"
    # after losing the letterhead, the session and the subject line entirely.
    ("marks_split", r"carr(?:ies|y)\s*(?:twenty[\s-]*five|25)|other\s+question\s+carr", 2),
)

# The course code is too short and too mangled to match loosely without firing on
# body text, so it only counts when it appears intact.
CODE_PATTERN = re.compile(r"LW\s*307", re.I)

# [\W_] rather than \W: the dash between month and year comes through as an
# underscore often enough ("APRIL_2019") that treating _ as a word character
# silently drops the session on an otherwise perfectly readable header.
SESSION_PATTERN = re.compile(rf"({MONTHS})[\W_]{{0,3}}((?:19|20)\d{{2}})", re.I)


@dataclass
class PageScan:
    page_no: int
    score: int
    signals: list[str]
    session: str
    header: str


@dataclass
class Override:
    page: int
    session: str
    note: str


@dataclass
class Paper:
    paper_no: int
    start_page: int
    end_page: int
    session: str
    score: int
    signals: list[str]
    note: str = ""
    source: str = "ocr"

    @property
    def pages(self) -> int:
        return self.end_page - self.start_page + 1


@dataclass
class Findings:
    papers: list[Paper] = field(default_factory=list)
    suspected: list[tuple[int, int]] = field(default_factory=list)


def read_overrides(path: Path) -> dict[int, Override]:
    """Load boundaries and sessions read off the rendered scan by a human.

    Some headers are perfectly legible on the page and still come through as
    noise -- page 18's letterhead is sharp to the eye and scores 0. Rather than
    loosen the patterns until noise scores as a header, those readings are
    recorded here and merged in, tagged `eye` so the output never claims the OCR
    found something it did not. Delete the file to see the unaided detector.
    """
    if not path.is_file():
        return {}
    overrides: dict[int, Override] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            page = int(row["page"])
            overrides[page] = Override(page, row["session"].strip(), row["note"].strip())
    return overrides


def read_pages(pdf_path: Path) -> list[str]:
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        # U+FFFD stands in for the em dashes and curly quotes the OCR could not
        # map; blanking it keeps them from splitting words the patterns need whole.
        return [(page.extract_text() or "").replace("�", " ") for page in pdf.pages]


def header_of(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:HEADER_LINES])


def find_session(header: str) -> str:
    """Read the sitting off the EXAMINATION line, keeping both halves of "OCTOBER 2021/APRIL 2022".

    Confining this to the one line that names the examination is what keeps deed
    and decree dates out. A header short enough to leave body text inside the
    window will otherwise date a 2019 sitting to 2006, since the first question
    on these papers is invariably about a decree entered decades ago.
    """
    lines = header.splitlines()
    candidates = [ln for ln in lines if re.search(r"EXAMINATION|EXAM\w*\s*-", ln, re.I)]
    if not candidates:
        # No examination line survived; the first date in the header is the best
        # guess available, and the caller sees the low score that comes with it.
        candidates = lines[:1] if lines else []

    seen: list[str] = []
    for line in candidates:
        for match in SESSION_PATTERN.finditer(line):
            item = f"{match.group(1).upper()} {match.group(2)}"
            if item not in seen:
                seen.append(item)
    return " / ".join(seen)


def scan_page(page_no: int, text: str) -> PageScan:
    header = header_of(text)
    score, signals = 0, []
    for name, pattern, weight in SIGNALS:
        if name == "code":
            continue
        if re.search(pattern, header, re.I):
            score += weight
            signals.append(name)
    if CODE_PATTERN.search(header):
        score += 1
        signals.append("code")
    return PageScan(page_no, score, signals, find_session(header), header)


def apply_overrides(
    scans: list[PageScan], overrides: dict[int, Override], min_score: int
) -> None:
    """Merge the eye-read boundaries into the scan results, in place."""
    for scan in scans:
        override = overrides.get(scan.page_no)
        if not override:
            continue
        scan.score = max(scan.score, min_score)
        scan.session = override.session or scan.session
        if "eye" not in scan.signals:
            scan.signals.append("eye")


def group_papers(scans: list[PageScan], total: int, min_score: int) -> Findings:
    starts = [s for s in scans if s.score >= min_score]
    findings = Findings()
    if not starts:
        return findings

    # A header repeating the session of the paper already open is a second cover
    # for that paper -- these bundles carry a Sinhala-medium one -- not a new
    # paper. It is folded in, and the reason is recorded on the paper it joins.
    kept: list[PageScan] = []
    for scan in starts:
        if kept and scan.session and scan.session == kept[-1].session:
            kept[-1] = PageScan(
                kept[-1].page_no,
                max(kept[-1].score, scan.score),
                kept[-1].signals,
                kept[-1].session,
                kept[-1].header,
            )
            findings.suspected.append((-scan.page_no, -scan.page_no))  # marker, resolved below
            continue
        kept.append(scan)

    duplicate_pages = {-a for a, _ in findings.suspected if a < 0}
    findings.suspected = [pair for pair in findings.suspected if pair[0] > 0]

    for index, scan in enumerate(kept):
        end = (kept[index + 1].page_no - 1) if index + 1 < len(kept) else total
        note = ""
        folded = sorted(p for p in duplicate_pages if scan.page_no < p <= end)
        if folded:
            note = f"repeat header on p{', p'.join(str(p) for p in folded)} (same session)"
        findings.papers.append(
            Paper(
                paper_no=index + 1,
                start_page=scan.page_no,
                end_page=end,
                session=scan.session or "unreadable",
                score=scan.score,
                signals=scan.signals,
                note=note,
                source="eye" if "eye" in scan.signals else "ocr",
            )
        )
    return findings


def flag_long_papers(findings: Findings) -> None:
    """Mark any paper much longer than the rest as hiding a start whose header was lost."""
    lengths = sorted(p.pages for p in findings.papers)
    if len(lengths) < 3:
        return
    typical = lengths[len(lengths) // 2]
    for paper in findings.papers:
        if paper.pages >= typical * 2:
            paper.note = (
                (paper.note + "; ") if paper.note else ""
            ) + f"{paper.pages} pages vs typical {typical}: likely an unreadable header inside"
            findings.suspected.append((paper.start_page + typical, paper.end_page))


def write_csv(path: Path, findings: Findings) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "paper_no", "start_page", "end_page", "pages", "session",
                "source", "score", "signals", "note",
            ]
        )
        for paper in findings.papers:
            writer.writerow(
                [
                    paper.paper_no,
                    paper.start_page,
                    paper.end_page,
                    paper.pages,
                    paper.session,
                    paper.source,
                    paper.score,
                    ";".join(paper.signals),
                    paper.note,
                ]
            )


def report(findings: Findings, total: int) -> None:
    print(f"{'#':>3} {'pages':>9} {'n':>3}  {'session':<26} {'from':<4} {'score':>5}  note")
    print("-" * 100)
    for paper in findings.papers:
        span = f"{paper.start_page}-{paper.end_page}"
        print(
            f"{paper.paper_no:>3} {span:>9} {paper.pages:>3}  {paper.session:<26}"
            f" {paper.source:<4} {paper.score:>5}  {paper.note}"
        )
    print("-" * 100)
    covered = sum(p.pages for p in findings.papers)
    by_eye = sum(1 for p in findings.papers if p.source == "eye")
    print(
        f"{len(findings.papers)} papers over {covered}/{total} pages"
        f" ({len(findings.papers) - by_eye} from OCR, {by_eye} read off the scan by eye)"
    )
    if findings.suspected:
        print("\nsuspected boundaries with no readable header (page ranges to check by eye):")
        for lo, hi in findings.suspected:
            print(f"  somewhere in pages {lo}-{hi}")
    print(
        "\nstatus=unverified: rows marked `ocr` are inferred from OCR text and have not"
        "\nbeen checked against the scan; rows marked `eye` were read off the rendered"
        "\npage. Neither has been signed off by a lawyer."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF, help="OCR'd bundle to scan")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="where to write papers.csv")
    parser.add_argument(
        "--min-score",
        type=int,
        default=3,
        help=(
            "header score a page needs to count as a start (default: 3). Tuned on "
            "this bundle, where intact headers score 8-13 and the worst surviving "
            "ones score 3-4, against a continuation-page ceiling of 1"
        ),
    )
    parser.add_argument(
        "--overrides",
        type=Path,
        default=DEFAULT_OVERRIDES,
        help="boundaries read off the scan by eye (default: paper-starts-overrides.csv)",
    )
    parser.add_argument(
        "--show-scores", action="store_true", help="print every page's score and signals"
    )
    args = parser.parse_args()

    if not args.pdf.is_file():
        print(f"error: no such PDF: {args.pdf}", file=sys.stderr)
        return 1

    pages = read_pages(args.pdf)
    scans = [scan_page(i, text) for i, text in enumerate(pages, 1)]

    if args.show_scores:
        for scan in scans:
            if scan.score:
                print(f"{scan.page_no:>3} score={scan.score:<3} {scan.session:<26} {','.join(scan.signals)}")
        print()

    overrides = read_overrides(args.overrides)
    if overrides:
        print(f"merging {len(overrides)} eye-read boundaries from {args.overrides.name}\n")
        apply_overrides(scans, overrides, args.min_score)

    findings = group_papers(scans, len(pages), args.min_score)
    if not findings.papers:
        print(f"no page scored {args.min_score} or better; try --show-scores --min-score 3")
        return 1

    flag_long_papers(findings)
    write_csv(args.csv, findings)
    report(findings, len(pages))
    print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
