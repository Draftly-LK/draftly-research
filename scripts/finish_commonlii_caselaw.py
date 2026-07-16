"""Finish + consolidate the CommonLII harvest.

The main harvest (harvest_commonlii_caselaw.py) completed LKSC fully and LKCA
through 2000 before its background run was stopped. This script:

  A. Harvests the remaining LKCA years (>= 2001) — fetch each case, save
     conveyancing matches (skips cases already saved).
  B. Rebuilds the COMPLETE index CSV (every case) from year-index pages only
     (cheap — no per-case fetch).
  C. Rebuilds the conveyancing CSV from the saved .txt files, joined to the
     index for citation/title.

Idempotent and safe to re-run.
"""

from __future__ import annotations

import csv
import importlib.util
import re
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "h", "scripts/harvest_commonlii_caselaw.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)

OUT_TEXT = Path("data/legal-sources/library/case-law/commonlii")
IDX_CSV = Path("data/legal-sources/manifests/case-law-commonlii-index.csv")
CONV_CSV = Path("data/legal-sources/manifests/case-law-commonlii-conveyancing.csv")


def harvest_remaining_lkca(from_year: int = 2001) -> int:
    saved = 0
    years = [y for y in h.year_links("LKCA") if y >= from_year]
    h.log(f"[finish] LKCA remaining years: {years}")
    for y in years:
        for url, title in h.case_links("LKCA", y):
            cno = re.search(r"/(\d+)\.html?$", url).group(1)
            dest = OUT_TEXT / "LKCA" / str(y) / f"{cno}.txt"
            if dest.exists():
                continue
            import time as _t
            _t.sleep(h.DELAY)
            page = h.get(url)
            if not page:
                continue
            text = h.strip_html(page)
            if len(h.STRONG.findall(text)) >= h.THRESHOLD:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(text, encoding="utf-8")
                saved += 1
        h.log(f"[finish] LKCA {y} done | new saved={saved}")
    return saved


def build_index() -> dict[tuple[str, int, str], dict]:
    """Full citation index from year-index pages (no per-case fetch)."""
    rows: dict[tuple[str, int, str], dict] = {}
    for db in ("LKSC", "LKCA"):
        for y in h.year_links(db):
            for url, title in h.case_links(db, y):
                cno = re.search(r"/(\d+)\.html?$", url).group(1)
                cit = h.CIT.search(title)
                rows[(db, y, cno)] = {
                    "db": db, "year": y, "case_no": cno,
                    "citation": cit.group(0).strip() if cit else "",
                    "title": title[:300], "url": url,
                }
        h.log(f"[index] {db}: indexed so far {len(rows)}")
    return rows


def main() -> None:
    new = harvest_remaining_lkca()
    h.log(f"[finish] new conveyancing files saved: {new}")

    index = build_index()
    with IDX_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["db", "year", "case_no", "citation", "title", "url"])
        w.writeheader()
        w.writerows(index.values())
    h.log(f"[index] wrote {len(index)} rows -> {IDX_CSV}")

    # Conveyancing CSV from saved text files, joined to index.
    conv = []
    for tf in OUT_TEXT.rglob("*.txt"):
        db = tf.parts[-3]
        year = int(tf.parts[-2])
        cno = tf.stem
        meta = index.get((db, year, cno), {})
        text = tf.read_text(encoding="utf-8", errors="ignore")
        conv.append({
            "db": db, "year": year, "case_no": cno,
            "citation": meta.get("citation", ""),
            "title": meta.get("title", ""),
            "hits": len(h.STRONG.findall(text)),
            "chars": len(text),
            "url": meta.get("url", ""),
            "text_file": str(tf).replace("\\", "/"),
        })
    conv.sort(key=lambda r: (r["db"], r["year"], int(r["case_no"])))
    with CONV_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "db", "year", "case_no", "citation", "title", "hits", "chars", "url", "text_file"])
        w.writeheader()
        w.writerows(conv)
    h.log(f"[conv] wrote {len(conv)} conveyancing rows -> {CONV_CSV}")

    # CommonLII's year landing pages occasionally omit historical years that
    # were harvested earlier. Recover those local judgments after every rebuild
    # so the complete index remains a superset of the conveyancing manifest.
    from repair_commonlii_index import repair

    missing_before, missing_after, blank_metadata = repair()
    h.log(
        "[repair] locally harvested rows missing from year indexes: "
        f"{missing_before} -> {missing_after}; blank metadata={blank_metadata}"
    )
    if missing_after or blank_metadata:
        raise RuntimeError("CommonLII local-index repair did not reach full coverage")
    print(f"DONE-FINISH total_index={len(index)} conveyancing={len(conv)} new_files={new}")


if __name__ == "__main__":
    main()
