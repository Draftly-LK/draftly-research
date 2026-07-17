"""Download the research papers relevant to Draftly into papers/.

For each arXiv id: fetch metadata from the arXiv API, confirm it resolves,
download the PDF, and flag any whose title doesn't match the expected topic
(so a wrong/recalled id can't silently drop an unrelated paper in). Also handles
a few non-arXiv PDFs (ACL Anthology). Writes papers/download-index.csv +
papers/README.md.
"""

from __future__ import annotations

import csv
import re
import time
import urllib.request
from pathlib import Path

OUT = Path("papers")
OUT.mkdir(exist_ok=True)
(OUT / "ocr").mkdir(exist_ok=True)
(OUT / "data").mkdir(exist_ok=True)


def subdir(cat: str) -> str:
    return "ocr" if cat == "6-ocr-sinhala" else "data"
UA = "DraftlyResearch/0.1 (academic paper collection)"
DELAY = 3.2  # arXiv asks for ~3s between API calls

# (arxiv_id, category, expected-keyword-in-title-lowercased)
ARXIV = [
    ("2005.11401", "1-rag-foundations", "retrieval-augmented"),
    ("2112.04426", "1-rag-foundations", "retrieving"),
    ("2208.03299", "1-rag-foundations", "atlas"),
    ("2310.11511", "1-rag-foundations", "self-rag"),
    ("2401.18059", "2-hierarchical-tree", "tree-organized"),
    ("2310.05029", "2-hierarchical-tree", "memory maze"),
    ("2512.03413", "2-hierarchical-tree", "bookrag"),
    ("2405.14831", "3-graph-retrieval", "hipporag"),
    ("2404.16130", "3-graph-retrieval", "local to global"),
    ("2410.05779", "3-graph-retrieval", "lightrag"),
    ("2310.08560", "4-agent-memory", "operating system"),
    ("2504.01840", "5-legal-rag-kg-eval", "legal"),
    ("2406.17186", "5-legal-rag-kg-eval", "legal"),
    ("2511.00268", "5-legal-rag-kg-eval", "statute"),
    ("2505.20743", "5-legal-rag-kg-eval", "case retrieval"),
    ("2602.23371", "5-legal-rag-kg-eval", "legal"),
    ("2506.22165", "5-legal-rag-kg-eval", "citation"),
    ("2505.00039", "5-legal-rag-kg-eval", "legal"),
    ("2606.09724", "5-legal-rag-kg-eval", "legal"),
    ("2502.20364", "5-legal-rag-kg-eval", "legal"),
    ("2507.18264", "6-ocr-sinhala", "ocr"),
    ("2606.29378", "6-ocr-sinhala", "sinhala"),
    ("2603.04854", "6-ocr-sinhala", "sinhala"),
    ("2510.04124", "6-ocr-sinhala", "sri lanka"),
    ("2412.16119", "6-ocr-sinhala", "low-resource"),
]
DIRECT = [
    # (url, category, filename, expected-keyword)
    ("https://aclanthology.org/2025.nllp-1.11.pdf", "5-legal-rag-kg-eval",
     "2025.nllp-1.11-nyaygraph-legal-statute-kg.pdf", None),
]


def get(url: str, timeout: int = 60) -> bytes:
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout).read()


def arxiv_title(aid: str) -> str | None:
    try:
        xml = get(f"http://export.arxiv.org/api/query?id_list={aid}", 30).decode("utf-8", "ignore")
    except Exception:
        return None
    ent = re.search(r"<entry>(.*?)</entry>", xml, re.S)
    if not ent:
        return None
    t = re.search(r"<title>(.*?)</title>", ent.group(1), re.S)
    return re.sub(r"\s+", " ", t.group(1)).strip() if t else None


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:55]


rows = []
for aid, cat, kw in ARXIV:
    title = arxiv_title(aid)
    time.sleep(DELAY)
    if not title:
        print(f"[NO-META] {aid}")
        rows.append({"id": aid, "category": cat, "title": "", "file": "", "status": "no-metadata"})
        continue
    status = "ok" if (kw is None or kw in title.lower()) else "REVIEW-title-mismatch"
    sub = subdir(cat)
    fn = OUT / sub / f"{aid}-{slug(title)}.pdf"
    if not fn.exists():
        try:
            pdf = get(f"https://arxiv.org/pdf/{aid}")
            time.sleep(DELAY)
            if pdf[:4] != b"%PDF":
                status = "not-pdf"
            else:
                fn.write_bytes(pdf)
        except Exception as e:  # noqa: BLE001
            status = f"download-failed"
            print(f"[FAIL] {aid}: {e}")
    rows.append({"id": aid, "category": cat, "title": title,
                 "file": f"{sub}/{fn.name}" if fn.exists() else "", "status": status})
    print(f"[{status[:4].upper()}] {aid} | {title[:68]}")

for url, cat, fname, kw in DIRECT:
    sub = subdir(cat)
    fn = OUT / sub / fname
    try:
        if not fn.exists():
            data = get(url)
            if data[:4] == b"%PDF":
                fn.write_bytes(data)
        rows.append({"id": url.rsplit("/", 1)[-1], "category": cat,
                     "title": fname, "file": f"{sub}/{fn.name}" if fn.exists() else "", "status": "ok"})
        print(f"[OK ] {fname}")
        time.sleep(DELAY)
    except Exception as e:  # noqa: BLE001
        rows.append({"id": url, "category": cat, "title": fname, "file": "", "status": "download-failed"})
        print(f"[FAIL] {url}: {e}")

# index csv
with (OUT / "download-index.csv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "category", "title", "file", "status"])
    w.writeheader()
    w.writerows(rows)

ok = sum(1 for r in rows if r["status"] == "ok" and r["file"])
print(f"\nDONE: {ok}/{len(rows)} downloaded cleanly. See papers/download-index.csv")
