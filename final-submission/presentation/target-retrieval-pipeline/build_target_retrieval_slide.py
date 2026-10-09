"""Build one standalone, editable slide for Draftly's target retriever.

This script creates a new PowerPoint and never opens or changes the main deck.
"""

from pathlib import Path
import sys

from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build_ppt import (
    BLUE,
    BLUE_PALE,
    GREY2,
    GREY3,
    INK,
    PAPER,
    WHITE,
    H,
    W,
    chip,
    line,
    logo,
    rect,
    txt,
)


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "Draftly-Target-Hybrid-Retrieval-Pipeline.pptx"


def box(slide, heading, detail, x, y, w, h, active=False):
    rect(slide, x, y, w, h, fill=BLUE if active else WHITE, line=None if active else GREY2)
    color = WHITE if active else INK
    txt(slide, heading, x + 0.14, y + 0.11, w - 0.28, 0.31,
        size=15.5, color=color, bold=True, align=PP_ALIGN.CENTER)
    txt(slide, detail, x + 0.15, y + 0.45, w - 0.30, h - 0.54,
        size=11.9, color=color, align=PP_ALIGN.CENTER)


def arrow(slide, x, y, w=0.24):
    txt(slide, "→", x, y, w, 0.30, size=20, color=BLUE, align=PP_ALIGN.CENTER)


def channel_card(slide, x, title, subtitle):
    y, w, h = 3.13, 5.84, 1.42
    rect(slide, x, y, w, h, fill=BLUE_PALE)
    txt(slide, title, x + 0.15, y + 0.11, 3.30, 0.27,
        size=12.7, color=BLUE, bold=True)
    txt(slide, subtitle, x + 3.20, y + 0.11, 2.45, 0.27,
        size=10.9, color=GREY3, align=PP_ALIGN.RIGHT)
    for offset, name in ((0.15, "BM25 lexical"), (2.99, "Dense embeddings")):
        rect(slide, x + offset, y + 0.55, 2.70, 0.68, fill=WHITE, line=GREY2)
        txt(slide, name, x + offset + 0.09, y + 0.71, 2.52, 0.35,
            size=16.0, color=INK, align=PP_ALIGN.CENTER)


def build():
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    rect(slide, 0, 0, W, H, fill=PAPER)
    txt(slide, "PART II · SOFTWARE ENGINEERING", 0.58, 0.27, 8.7, 0.24,
        size=9.5, color=BLUE, bold=True)
    txt(slide, "Target hosted retrieval: query rewrite + hybrid search",
        0.58, 0.64, 11.20, 0.73, size=28.5, color=INK)
    logo(slide)

    chip(slide, "TEAM ROLLOUT IN PROGRESS  ·  TARGET PIPELINE", 0.62, 1.53, 12.07, 0.42,
         fill=BLUE, color=WHITE, size=12.7)

    box(slide, "Lawyer question", "Original wording retained", 0.65, 2.17, 2.10, 0.78, active=True)
    arrow(slide, 2.85, 2.41)
    box(slide, "Bounded rewrite", "Search terms; no new citations", 3.18, 2.17, 2.76, 0.78)
    txt(slide, "The rewrite adds recall without discarding the lawyer's terms.",
        6.33, 2.38, 6.25, 0.36, size=15.5, color=INK)

    channel_card(slide, 0.65, "ORIGINAL QUERY", "preserve exact legal terms")
    channel_card(slide, 6.84, "SANITIZED REWRITE", "additional search language")

    # Both query paths enter the first rank fusion stage.
    line(slide, 3.57, 4.55, 3.57, 4.81, color=BLUE, width=1.4)
    line(slide, 9.76, 4.55, 9.76, 4.81, color=BLUE, width=1.4)
    line(slide, 3.57, 4.81, 9.76, 4.81, color=BLUE, width=1.4)
    line(slide, 6.66, 4.81, 6.66, 5.04, color=BLUE, width=1.4)

    steps = [
        ("RRF fusion", "combine ranked lists"),
        ("Graph expansion", "typed statutory links"),
        ("Final RRF", "rank cited sections"),
        ("Answer gate", "citations or insufficient authority"),
    ]
    x_positions = [0.65, 3.58, 6.51, 9.44]
    widths = [2.70, 2.70, 2.70, 3.23]
    for i, ((heading, detail), x, w) in enumerate(zip(steps, x_positions, widths)):
        box(slide, heading, detail, x, 5.12, w, 0.88, active=i == 3)
        if i < 3:
            arrow(slide, x + w + 0.08, 5.40)

    # The vertical join lands on the first fusion box. It is a single native
    # connector group, so the pipeline remains editable in PowerPoint.
    line(slide, 6.66, 5.04, 2.00, 5.04, color=BLUE, width=1.4)
    line(slide, 2.00, 5.04, 2.00, 5.12, color=BLUE, width=1.4)

    rect(slide, 0.65, 6.23, 12.02, 0.52, fill=BLUE_PALE)
    txt(slide, "Selection evidence: hybrid led average R@20 in the paper; a separate rewrite pilot improved C@20.",
        0.80, 6.31, 11.72, 0.32, size=12.2, color=BLUE, bold=True)
    txt(slide, "The exact combined target needs deployment and evaluation on the same question set.",
        0.65, 6.84, 12.02, 0.24, size=11.2, color=GREY3)

    line(slide, 0.58, 7.14, 12.77, 7.14, color=GREY2, width=0.6)
    txt(slide, "DRAFTLY  /  UNIVERSITY OF MORATUWA", 0.58, 7.20, 6.0, 0.17,
        size=8.3, color=GREY3)
    txt(slide, "STANDALONE INSERT SLIDE", 10.55, 7.20, 2.21, 0.17,
        size=8.3, color=GREY3, align=PP_ALIGN.RIGHT)

    slide.notes_slide.notes_text_frame.text = (
        "Target hosted statutory retrieval pipeline. The team intends to deploy "
        "hybrid retrieval with embeddings and bounded query rewriting. The lawyer's "
        "original question remains in the search: original and sanitized rewritten "
        "queries each run through BM25 lexical and dense embedding channels. "
        "Reciprocal rank fusion combines them; typed statutory graph expansion "
        "adds candidates; a final fusion ranks cited sections. The research "
        "answer gate returns a grounded response or insufficient authority. "
        "The rewrite is search text, never a citation or legal answer. "
        "Research motivation: in the paper's seven-system comparison, hybrid "
        "had the highest average R@20, 0.546. A separate offline rewrite pilot "
        "recorded C@20 0.391 on all 40 test questions versus 0.344 for its "
        "hybrid reference. That pilot used a different research retriever and "
        "replaced the query rather than fusing original and rewritten paths. "
        "Its result therefore is not a measured score for this exact target "
        "pipeline. Labels remain agent-proposed. Deployment and an end-to-end "
        "evaluation are still required. Direct Matter Agent search is a "
        "separate integration. Sources: research-paper/tables/main.tex; "
        "docs/retrieval/HYBRID_QUERY_REWRITE_IMPLEMENTATION.md, sections 2-4."
    )

    prs.save(OUTPUT)
    print(OUTPUT)
    print(f"slides={len(prs.slides)}")


if __name__ == "__main__":
    build()
