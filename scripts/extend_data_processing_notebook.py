"""Idempotently add the production-store stage to the processing notebook."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/data_processing_pipeline.ipynb"
TAG = "production-processed-store"


def lines(text: str) -> list[str]:
    values = text.strip().splitlines()
    return [line + "\n" for line in values[:-1]] + [values[-1]]


def markdown_cell(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {"tags": [TAG]},
        "source": lines(text),
    }


def code_cell(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"tags": [TAG]},
        "outputs": [],
        "source": lines(text),
    }


def main() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    notebook["cells"][0]["source"] = lines("""
# Draftly Legal Corpus Processing Pipeline

This notebook keeps the original exploratory case-index stages and finishes
with the production, file-based legal corpus under `data/processed/`.

The canonical retrieval store contains normalized Markdown for statutes,
amendments, gazettes, institution guides, and case law; provenance records;
case records; deterministic topic tables; section-specific citation edges; an
unresolved-citation queue; and a lawyer-verification sample.

No database is required. Generated legal-authority links remain `unverified`
until a lawyer signs them off.

**Stages**

0. Validate inputs and build the complete discovery index.
1. Select usable conveyancing text and audit extraction quality.
2. Extract exploratory statute mentions and nearby section references.
3. Attach curated conveyancing topics.
4. Write exploratory case-index records and quality summaries.
5. Create a blank, reviewer-owned retrieval-evaluation template.
6. Build and verify the canonical `data/processed/` retrieval store.
""")
    notebook["cells"][19]["source"] = lines("""
## What to improve next

The normalized corpus and deterministic section-link pass are complete. The
next work is review and retrieval evaluation:

1. Have a lawyer complete `verification-sample.csv` and calculate precision by
   confidence method before treating links as retrieval authority.
2. Prioritize `unresolved_citations.csv` by repeated passage, source, and
   conveyancing topic; add deterministic aliases before considering a bounded
   model-assisted review pass.
3. Segment authoritative statute Markdown into stable section nodes and connect
   verified case edges to those nodes.
4. Curate historical statute short names and spelling variants to improve recall
   without weakening deterministic provenance.
5. Build a lawyer-approved retrieval question set and report precision@k and
   recall@k for the topic-to-statute-to-case walk.
6. Continue repairing flagged encoding damage while retaining original text and
   conversion provenance.
""")
    notebook["cells"] = [
        cell for cell in notebook["cells"]
        if TAG not in cell.get("metadata", {}).get("tags", [])
    ]
    notebook["cells"].extend([
        markdown_cell("""
## Stage 6 - Canonical normalized retrieval store

The exploratory output above remains useful for analysis. Production retrieval
uses only `data/processed/`. The scripts below repair the CommonLII manifest
join, normalize every available source into Markdown, create section-specific
case links, preserve unresolved mentions, and generate a 30-edge lawyer review
sheet. OCR is deliberately not invoked from the notebook because cloud use must
remain an explicit operator decision.
"""),
        code_cell("""
import subprocess
import sys

PRODUCTION = ROOT / "data/processed"
required_outputs = [
    "documents.csv",
    "cases.jsonl",
    "topics.csv",
    "topic-sources.csv",
    "topics.json",
    "case_statute_section_links.csv",
    "unresolved_citations.csv",
    "verification-sample.csv",
]

REBUILD_PRODUCTION_STORE = not all(
    (PRODUCTION / filename).exists() for filename in required_outputs
)

if REBUILD_PRODUCTION_STORE:
    pending_ocr = pd.read_csv(MANIFESTS / "conversion-registry.csv", dtype=str).fillna("")
    pending_ocr = pending_ocr[
        ~pending_ocr["status"].isin(["converted", "fallback", "fallback-pdftotext"])
    ]
    if not pending_ocr.empty:
        raise RuntimeError(
            "OCR outputs are incomplete. Run scripts/convert_to_text.py explicitly "
            "before rebuilding the production store."
        )
    commands = [
        [sys.executable, str(ROOT / "scripts/repair_commonlii_index.py")],
        [sys.executable, str(ROOT / "scripts/build_processed_store.py"), "--require-complete"],
        [sys.executable, str(ROOT / "scripts/build_case_citation_links.py"), "--write-unresolved"],
        [sys.executable, str(ROOT / "scripts/build_verification_sample.py")],
    ]
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)

missing_outputs = [
    filename for filename in required_outputs
    if not (PRODUCTION / filename).is_file()
]
if missing_outputs:
    raise FileNotFoundError(f"Missing production outputs: {missing_outputs}")

documents = pd.read_csv(PRODUCTION / "documents.csv", dtype=str).fillna("")
links = pd.read_csv(PRODUCTION / "case_statute_section_links.csv", dtype=str).fillna("")
unresolved = pd.read_csv(PRODUCTION / "unresolved_citations.csv", dtype=str).fillna("")
verification = pd.read_csv(PRODUCTION / "verification-sample.csv", dtype=str).fillna("")
with (PRODUCTION / "cases.jsonl").open(encoding="utf-8") as handle:
    production_cases = [json.loads(line) for line in handle if line.strip()]

document_ids = set(documents["doc_id"])
assert documents["doc_id"].is_unique
assert len(production_cases) == len({case["case_id"] for case in production_cases})
assert all(case["doc_id"] in document_ids for case in production_cases)
assert all((ROOT / path).is_file() for path in documents["text_path"])
assert len(documents[documents["source"] == "commonlii"]) == len(common_matches)
assert links["section"].ne("").all() and links["evidence_snippet"].ne("").all()
assert links["review_status"].eq("unverified").all()
assert len(verification) == 30
assert verification["extraction_status"].eq("unverified").all()

production_summary = {
    "documents": len(documents),
    "cases": len(production_cases),
    "commonlii_conveyancing_joined": len(documents[documents["source"] == "commonlii"]),
    "section_links": len(links),
    "unresolved_mentions": len(unresolved),
    "lawyer_verification_rows": len(verification),
}
print(json.dumps(production_summary, indent=2))
"""),
    ])
    NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Updated {NOTEBOOK} with {len(notebook['cells'])} cells")


if __name__ == "__main__":
    main()
