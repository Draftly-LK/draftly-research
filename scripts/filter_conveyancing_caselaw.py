"""Score harvested IA law-report volumes for conveyancing relevance.

Reads the plain-text volumes downloaded by harvest_ia_caselaw.py, counts hits
for each conveyancing topic's catchwords, and writes a relevance index so the
team knows which volumes (and roughly where) the conveyancing material sits.

These are OCR'd historical volumes without clean case boundaries, so this is a
keyword relevance map, not a per-case splitter (segmentation is a later step).
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

IA_DIR = Path("data/legal-sources/library/case-law/internet-archive")
MANIFEST = Path("data/legal-sources/manifests/case-law-ia-manifest.csv")
OUT = Path("data/legal-sources/manifests/case-law-ia-conveyancing.csv")

# Conveyancing topics → catchword regexes (word-boundary, case-insensitive).
TOPICS: dict[str, list[str]] = {
    "prescription": [r"prescripti\w+", r"adverse possession"],
    "servitudes": [r"servitude", r"right of way", r"easement"],
    "fidei_commissum": [r"fidei[\s-]?commiss\w+"],
    "deeds_instruments": [r"\bdeed\b", r"\bdeeds\b", r"conveyanc\w+", r"instrument"],
    "notaries_attestation": [r"notar\w+", r"attest\w+"],
    "partition": [r"partition"],
    "gift": [r"donation", r"deed of gift", r"\bgift\b"],
    "mortgage": [r"mortgage", r"hypothec\w*", r"\bbond\b"],
    "sale_vendor_purchaser": [r"vendor", r"purchaser", r"sale of land"],
    "title_ownership": [r"\btitle\b", r"ownership", r"possession"],
    "co_ownership": [r"co-?owner\w*", r"undivided", r"common elements"],
    "trusts": [r"\btrust\b", r"trustee"],
    "wills": [r"last will", r"testament\w*", r"codicil", r"executor", r"intestate"],
    "power_of_attorney": [r"power of attorney", r"attorney"],
    "state_land": [r"crown land", r"state land"],
    "registration": [r"registrat\w+", r"registrar", r"registered"],
}
COMPILED = {t: [re.compile(p, re.I) for p in pats] for t, pats in TOPICS.items()}


def load_manifest() -> list[dict]:
    with MANIFEST.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def score(text: str) -> tuple[dict[str, int], int]:
    per = {}
    for topic, regexes in COMPILED.items():
        per[topic] = sum(len(rx.findall(text)) for rx in regexes)
    return per, sum(per.values())


def main() -> None:
    rows = load_manifest()
    out_rows = []
    grand_total = 0
    for r in rows:
        tf = r.get("text_file", "")
        if not tf or not Path(tf).exists():
            continue
        text = Path(tf).read_text(encoding="utf-8", errors="ignore")
        per, total = score(text)
        grand_total += total
        top = sorted(per.items(), key=lambda kv: kv[1], reverse=True)[:4]
        top_str = "; ".join(f"{k}:{v}" for k, v in top if v)
        out_rows.append({
            "identifier": r["identifier"],
            "title": r["title"][:70],
            "year": r["year"],
            "conveyancing_hits": total,
            "top_topics": top_str,
            **{f"t_{k}": v for k, v in per.items()},
        })

    out_rows.sort(key=lambda x: x["conveyancing_hits"], reverse=True)
    fields = ["identifier", "title", "year", "conveyancing_hits", "top_topics"] + [
        f"t_{k}" for k in TOPICS
    ]
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    print(f"Volumes scored: {len(out_rows)} | total conveyancing keyword hits: {grand_total}")
    print(f"Index: {OUT}\n")
    print("Top volumes by conveyancing relevance:")
    for x in out_rows[:12]:
        print(f"  {x['conveyancing_hits']:>6} hits | {x['year']:4} | {x['identifier']} | {x['top_topics']}")


if __name__ == "__main__":
    main()
