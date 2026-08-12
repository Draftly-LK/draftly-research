"""Offline checks for the LawLanka structural parsers.

The HTML below is shaped on the link format recorded in the earlier Civil
Procedure Code extract (`consSelectedSection?chapterid=2001Y4V101C&sectionno=1`)
and on the heading samples quoted in `statue-plans.md`. Running these does not
touch the network, so the parsers can be checked before the sweep is authorised.

    python scripts/lawlanka-section-index/test_parse_index.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import parse_index as P

SAMPLE = """
<html><body>
<h2>Civil Procedure Code</h2>
<p>Ordinance No. 2 of 1889, Act No. 79 of 1980, No. 14 of 1997, 43 of 2024</p>
<table>
  <tr><td><a href="consSelectedSection?chapterid=2001Y4V101C&amp;sectionno=1">s.1</a></td>
      <td>This Ordinance may be cited as the Civil Procedure Code.</td></tr>
  <tr><td><a href="consSelectedSection?chapterid=2001Y4V101C&amp;sectionno=4">s.4
      Where no provision is made special directions to be given by Court of Appeal.</a></td></tr>
  <tr><td><a href="consSelectedSection?chapterid=2001Y4V101C&amp;sectionno=8">s.8
      Procedure of action to be ordinarily regular. [2, 53 of 1980].</a></td></tr>
  <tr><td><a href="consSelectedSection?chapterid=2001Y4V101C&amp;sectionno=9">s.9
      Institution of actions: in what court. [3, 43 of 2024].</a></td></tr>
  <tr><td><a href="consSelectedSection?chapterid=2001Y4V101C&amp;sectionno=247">247</a></td>
      <td>Action by party claiming right.</td></tr>
  <tr><td><a href="consSelectedSection?chapterid=2001Y4V101C&amp;sectionno=756">s.756
      Security to be by bond and with surety. [50, 79 of 1980] [50, 79 of 1988] [12, 14 of 1997]</a></td></tr>
  <tr><td><a href="consSelectedSection?chapterid=2001Y4V101C&amp;sectionno=756">s.756
      Security to be by bond and with surety. [50, 79 of 1980] [50, 79 of 1988] [12, 14 of 1997]</a></td></tr>
  <tr><td><a href="someOtherPage?x=1">not a section link</a></td></tr>
</table></body></html>
"""

AZ_SAMPLE = """
<html><body>
<a href="consShortTitleView?actcode=CPC1889">Civil Procedure Code</a>
<a href="consShortTitleView?actcode=RRA1948">Rent Restriction Act</a>
<a href="consShortTitleView?actcode=RRA1948">Rent Restriction Act</a>
<a href="viewNlrVolumeWise?y=1950">New Law Reports</a>
</body></html>
"""


def check(label: str, got, want) -> bool:
    ok = got == want
    print(f"  [{'ok ' if ok else 'FAIL'}] {label}: {got!r}"
          + ("" if ok else f"  (expected {want!r})"))
    return ok


def main() -> int:
    print("parse_section_index")
    secs = P.parse_section_index(SAMPLE)
    by = {s["section"]: s for s in secs}
    fails = 0

    for s in secs:
        marks = " ".join(f"[s.{m['amending_section']} of {m['amending_act']}]"
                         for m in s["markers"])
        print(f"    s.{s['section']:<5} {s['heading']}  {marks}")
    print()

    fails += not check("6 sections, duplicate collapsed", len(secs), 6)
    fails += not check("heading from the sibling cell (s.1)",
                       by["1"]["heading"],
                       "This Ordinance may be cited as the Civil Procedure Code")
    fails += not check("heading from the sibling cell (s.247)",
                       by["247"]["heading"], "Action by party claiming right")
    fails += not check("section label stripped from heading (s.4)",
                       by["4"]["heading"],
                       "Where no provision is made special directions to be "
                       "given by Court of Appeal")
    fails += not check("single marker parsed (s.8)",
                       [(m["amending_section"], m["amending_act"])
                        for m in by["8"]["markers"]], [("2", "53 of 1980")])
    fails += not check("marker text removed from heading (s.8)",
                       by["8"]["heading"],
                       "Procedure of action to be ordinarily regular")
    fails += not check("three-step version chain (s.756)",
                       [(m["amending_section"], m["amending_act"])
                        for m in by["756"]["markers"]],
                       [("50", "79 of 1980"), ("50", "79 of 1988"),
                        ("12", "14 of 1997")])
    fails += not check("chapterid captured", by["1"]["chapterid"], "2001Y4V101C")
    fails += not check("non-section link ignored",
                       any("someOtherPage" in s["href"] for s in secs), False)

    print("\nparse_amending_instruments")
    inst = P.parse_amending_instruments(SAMPLE)
    print(f"    {inst}")
    fails += not check("header instruments, body markers excluded", inst,
                       ["Ordinance No. 2 of 1889", "Act No. 79 of 1980",
                        "No. 14 of 1997", "43 of 2024"])

    print("\nparse_consolidation_index")
    az = P.parse_consolidation_index(AZ_SAMPLE)
    print(f"    {az}")
    fails += not check("2 statutes, duplicate collapsed", len(az), 2)
    fails += not check("act code captured", az[0]["act_code"], "CPC1889")
    fails += not check("law-report link ignored",
                       any("Nlr" in a["href"] for a in az), False)

    print("\nsummarise")
    summ = P.summarise(secs)
    print(f"    {summ}")
    fails += not check("highest section", summ["highest_section"], 756)
    fails += not check("every section has a heading", summ["headings_missing"], 0)
    fails += not check("marker total", summ["n_amendment_markers"], 5)

    print()
    if fails:
        print(f"{fails} check(s) FAILED")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
