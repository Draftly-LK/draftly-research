"""Side-by-side page overlays: original page next to each engine's detected boxes.

Reads the word boxes already cached by doctr_trial.ipynb, so it runs in seconds
and never re-invokes an OCR engine. Output goes to runs/overlays/, which is
gitignored — these are renders of real client pages and must not be committed,
pasted into tickets, or used in demos.

    uv run python ocr-benchmark/make_overlays.py
    uv run python ocr-benchmark/make_overlays.py --doc survey-plan --pages 1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import config
import contract
import render
import viz

DPI = 200
VARIANT = "original"
# doctr/rapidocr cache under "words"; dots.ocr caches layout regions under
# "elements", each carrying a category. Both resolve to the same bbox contract.
ENGINES = ["doctr", "rapidocr", "dots"]
CACHE_DIR_FOR = {"doctr": "doctr", "rapidocr": "rapidocr", "dots": "dotsocr"}
OUT = config.RUNS / "overlays"
CACHE = config.RENDERS / "engine-cache"

# Detection boxes read as fill-plus-edge, like a layout-analysis dump. Low alpha
# so the underlying glyphs stay legible and a fragmented box is visibly narrow.
BOX_FILL = "#2a78d6"
FILL_ALPHA = 0.30


def cache_dir(engine: str, doc_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_." else "-" for c in doc_id)
    return CACHE / CACHE_DIR_FOR[engine] / safe


def load_boxes(engine: str, doc_id: str, page_no: int) -> list[dict] | None:
    """Cached regions for one page, or None when that engine never ran it."""
    path = cache_dir(engine, doc_id) / f"p{page_no:04d}@{DPI}-{VARIANT}.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("elements") if engine == "dots" else payload.get("words")


def draw(ax, image, boxes: list[dict] | None, title: str) -> None:
    """Category-coloured and labelled when the engine supplies categories."""
    ax.imshow(image, cmap="gray")
    if boxes:
        w, h = image.size
        categories = sorted({b["category"] for b in boxes if "category" in b})
        palette = {c: viz.SERIES[i % len(viz.SERIES)] for i, c in enumerate(categories)}
        for box in boxes:
            x0, y0, x1, y1 = contract.bbox_to_pixels(box["bbox"], w, h)
            colour = palette.get(box.get("category"), BOX_FILL)
            ax.add_patch(Rectangle(
                (x0, y0), x1 - x0, y1 - y0,
                facecolor=colour, alpha=FILL_ALPHA,
                edgecolor=colour, linewidth=0.6,
            ))
            if "category" in box:
                ax.text(x0, y0 - 4, box["category"], fontsize=6, color=colour)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.set_title(title, fontsize=10, color=viz.INK_2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matter", default="platform-case-001")
    parser.add_argument("--doc", default=None, help="substring of the filename")
    parser.add_argument("--pages", type=int, default=2, help="pages per document")
    parser.add_argument("--engines", default=",".join(ENGINES),
                        help=f"comma-separated subset of {','.join(ENGINES)}")
    args = parser.parse_args()

    engines = [e.strip() for e in args.engines.split(",") if e.strip()]
    unknown = [e for e in engines if e not in CACHE_DIR_FOR]
    if unknown:
        raise SystemExit(f"unknown engine(s): {', '.join(unknown)}")

    viz.use_style()
    OUT.mkdir(parents=True, exist_ok=True)

    cases = [c for c in config.case_dirs() if c.name == args.matter]
    if not cases:
        raise SystemExit(f"no matter named {args.matter} under {config.INPUTS}")
    documents = [
        d for d in config.case_documents(cases[0])
        if args.doc is None or args.doc in d.name
    ]
    if not documents:
        raise SystemExit(f"no document matching {args.doc!r}")

    written = 0
    missing: set[str] = set()
    for doc in documents:
        doc_id = f"{doc.parent.name}/{doc.name}"
        pages = render.render_doc(doc, dpi=DPI, variant=VARIANT, page_limit=args.pages)
        for page in pages:
            per_engine = {e: load_boxes(e, doc_id, page.page_no) for e in engines}
            missing.update(e for e, v in per_engine.items() if v is None)
            if all(v is None for v in per_engine.values()):
                page.image.close()
                continue

            w, h = page.size
            cols = 1 + len(engines)
            fig, axes = plt.subplots(1, cols, figsize=(5.2 * cols, 5.2 * h / w))
            draw(axes[0], page.image, None, "original page")
            for ax, engine in zip(axes[1:], engines):
                boxes = per_engine[engine]
                label = (
                    f"{engine} — never run" if boxes is None
                    else f"{engine} — {len(boxes)} boxes"
                )
                draw(ax, page.image, boxes, label)

            fig.suptitle(f"{doc.name}  ·  page {page.page_no}", fontsize=11, color=viz.INK)
            fig.tight_layout()
            out = OUT / f"{doc.stem}-p{page.page_no:02d}.png"
            fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=viz.SURFACE)
            plt.close(fig)
            page.image.close()
            written += 1
            print(f"  {out.name}")

    print(f"\n{written} overlay(s) in {OUT}")
    if missing:
        print(f"no cached results for: {', '.join(sorted(missing))} "
              "— those panels are empty because the engine never ran, which is "
              "not a finding about the engine.")
    print("Real client pages. Gitignored on purpose — do not commit or share.")


if __name__ == "__main__":
    main()
