"""Offline checks for the CommonLII parser.

The fixture reproduces the *structure* of a CommonLII judgment page -- <h1>
court, breadcrumb with neutral citation, <h2> case name, paragraphs, closing
<hr>, then site footer -- including the malformed nesting these 1990s pages
carry (`<i><p>`, `<b>88 </p></b>`). The judgment wording is invented; only the
markup shape is real.

Runs without network access, so the parser can be fixed and re-verified while
the site is unreachable.

    python scripts/1901-crawler/test_parse_case.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import parse_case as P

URL = "https://www.commonlii.org/lk/cases/LKSC/1906/3.html"

FIXTURE = """
<html><body>
<h1>Supreme Court of Ceylon</h1>
<p>CommonLII &gt; Databases &gt; LKSC &gt; 1906 &gt; [1906] LKSC 3</p>
<h2>Silva v. Perera - NLR - 300 of 8 [1906] LKSC 3; (1906) 8 NLR 300</h2>
<!-- source: printed report -->
<p>The plaintiff sued upon a deed of transfer dated 1899, claiming
prescriptive title to the land described in the schedule.</p>
<i><p>
<b>88 </p>
</b><p>Counsel referred to Andris v. Juanis, 2 NLR 74, and to
Balthazar v. Baba Appu, 3 NLR 63.</p>
<p>Under section 2 of the Prevention of Frauds Ordinance a notarial
instrument is required. See also section 440 of the Criminal Procedure Code.</p>
<hr>
<p>Home | Databases | WorldLII | Search | Feedback</p>
</body></html>
"""


def check(label, got, want) -> bool:
    ok = got == want
    print(f"  [{'ok ' if ok else 'FAIL'}] {label}: {got!r}"
          + ("" if ok else f"  (expected {want!r})"))
    return ok


def main() -> int:
    rec = P.parse_case(FIXTURE, URL, retrieved_at="2026-08-12T00:00:00Z")
    fails = 0

    print("identity from the URL")
    fails += not check("case_id", rec["case_id"], "LKSC-1906-3")
    fails += not check("database", rec["database"], "LKSC")
    fails += not check("year", rec["year"], 1906)

    print("\nheadings")
    fails += not check("court", rec["court"], "Supreme Court of Ceylon")
    fails += not check("neutral citation", rec["neutral_citation"], "[1906] LKSC 3")

    print("\nbody extraction")
    # 4 real paragraphs; the footer after <hr> must be excluded, and the
    # <b>88</b> page-number fragment must not become its own paragraph.
    fails += not check("paragraph count", rec["n_paragraphs"], 4)
    fails += not check("footer excluded",
                       any("WorldLII" in p for p in rec["paragraphs"]), False)
    fails += not check("first paragraph starts the judgment",
                       rec["paragraphs"][0].startswith("The plaintiff sued"), True)

    print("\ncitations")
    fails += not check("report citations found",
                       "(1906) 8 NLR 300" in rec["report_citations"], True)
    legis = {(l["title"], l["section"]) for l in rec["cited_legislation"]}
    fails += not check("Prevention of Frauds s.2 linked",
                       ("Prevention of Frauds Ordinance", "2") in legis, True)
    fails += not check("Criminal Procedure Code s.440 linked",
                       ("Criminal Procedure Code", "440") in legis, True)

    print("\nprovenance")
    fails += not check("content hash present",
                       rec["content_hash"].startswith("sha256:"), True)
    fails += not check("status", rec["status"], "unverified")

    # --- the real page, with the structure the flat .txt corpus destroyed ----
    fixture = Path(__file__).resolve().parent / "fixtures" / "LKHC-1901-1.html"
    if not fixture.exists():
        print("\n(fixtures/LKHC-1901-1.html missing, skipping structure checks)")
        return 1 if fails else 0

    r = P.parse_case(fixture.read_text(encoding="utf-8"),
                     "https://www.commonlii.org/lk/cases/LKHC/1901/1.html")

    print("\nHTML-comment metadata (absent from the .txt corpus)")
    fails += not check("decision date from <!--sino date-->",
                       r["decision_date"], "1901-01-01")
    fails += not check("report series from <!--make_docs-->",
                       r.get("report_series"), "NLR")
    fails += not check("report volume", r.get("report_volume"), 5)
    fails += not check("report page", r.get("report_page"), 87)

    print("\nreport structure")
    fails += not check("originating court", r["registry"]["court"], "P. C.")
    fails += not check("originating place", r["registry"]["place"], "Ratnapura")
    fails += not check("originating case number", r["registry"]["number"], "20,026")
    fails += not check("catchword count", len(r["catchwords"]), 3)
    fails += not check("printed page breaks recorded",
                       [p["page"] for p in r["printed_pages"]], ["87", "88"])

    print("\nreporter matter vs the court's own words")
    fails += not check("judgment boundary found", r["has_judgment_boundary"], True)
    fails += not check("judgment author", r["judgment_author"], "MONCREIFF J")
    fails += not check("counsel", r["counsel"],
                       [{"name": "Bawa", "role": "for appellants"}])
    fails += not check("headnote separated from judgment",
                       bool(r["headnote"]) and "I therefore think" not in r["headnote"],
                       True)
    fails += not check("judgment text excludes counsel submission",
                       "for appellants" not in r["judgment_text"], True)

    print("\ncitation graph")
    fails += not check("cited cases",
                       [c["case"] for c in r["cited_cases"]],
                       ["Andris v. Juanis", "Balthazar v. Baba Appu"])
    fails += not check("legislation deduplicated to the fuller title",
                       [(l["title"], l["section"]) for l in r["cited_legislation"]],
                       [("Criminal Procedure Code", "440")])

    print(f"\n  paragraphs parsed: {rec['n_paragraphs']}, "
          f"chars: {rec['n_chars']}, legislation refs: {len(rec['cited_legislation'])}")
    print()
    if fails:
        print(f"{fails} check(s) FAILED")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
