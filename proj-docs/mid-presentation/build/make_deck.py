# -*- coding: utf-8 -*-
"""Build the Draftly mid-evaluation deck from the beige/brown template."""
import sys
from pptx import Presentation
from pptx.oxml.ns import qn

import kit
import deck_part1
import deck_part2

OUT = r"..\Draftly - Mid Evaluation.pptx"


def strip_slides(prs):
    sldIdLst = prs.slides._sldIdLst
    for sldId in list(sldIdLst):
        rId = sldId.get(qn('r:id'))
        prs.part.drop_rel(rId)
        sldIdLst.remove(sldId)


def main():
    prs = Presentation(kit.TEMPLATE)
    strip_slides(prs)
    p = deck_part1.build(prs)
    p = deck_part2.build(prs, p)
    prs.save(OUT)
    print("slides:", p, "->", OUT)
    if kit.WARNINGS:
        print("\nOVERFLOW WARNINGS (%d):" % len(kit.WARNINGS))
        for w in kit.WARNINGS:
            print("  -", w)
    else:
        print("no overflow warnings")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
