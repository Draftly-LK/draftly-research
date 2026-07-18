# Draftly Evaluation Framework

This folder defines the evaluation layer for Draftly's retrieval engine and the
past-paper-derived question set. The goal is to measure whether the system can
retrieve the correct Sri Lankan legal sources, cases, and evidence for lawyer
workflows, without treating generated text as authority.

## What The Past Papers Give Us

The Sri Lanka Law College papers in `past-papers/` are useful because they are
real legal problem prompts. They can become retrieval-test questions such as:

- Which statute sections are needed to answer this problem?
- Which cases should be retrieved?
- Does the answer cite only sources that exist in the closed corpus?
- Does the answer distinguish current law, amended law, and historical law?

They are not answer keys. A past-paper question becomes gold data only after a
lawyer or subject expert labels the expected statutes, sections, cases, and
reasoning points.

## Evaluation Layers

| Layer | What is measured | Main data |
| --- | --- | --- |
| Document extraction | Can we read and split the paper into subject/question units? | `past-paper-source-queue.csv`, `past-paper-question-queue.csv` |
| Retrieval | Can the engine return the expected statutes, gazettes, amendments, and cases? | `retrieval-gold.csv` |
| Answer grounding | Does the produced answer cite real, supporting evidence and abstain when needed? | `answer-eval-rubric.csv` |
| Lawyer review | Are retrieved authorities and drafts useful to a reviewer? | Future reviewed run sheets |

## Gold Data Lifecycle

1. Run the queue builder:

   ```powershell
   uv run python scripts\build_past_paper_eval_queue.py
   ```

2. OCR scanned papers where `extraction_status=needs_ocr`.
3. Review extracted question rows and assign workflow/topic labels.
4. Add expected legal authorities to `retrieval-gold.csv`.
5. Run retrieval experiments and compare:
   - no retrieval baseline
   - topic routing only
   - BM25 only
   - graph expansion
   - authority-aware ranking
   - temporal filtering
6. Keep unverified labels out of production answers until reviewed.

## BM25 Baseline Notebook

Run `notebooks/01_bm25_retrieval_baseline.ipynb` from top to bottom for the
first lexical retrieval baseline. It builds a persistent SQLite FTS5 BM25 index
from `data/processed/`, executes the available gold questions, and writes
predictions, per-question scores, aggregate metrics, and the run configuration
under `evaluation/runs/bm25-v1/`.

Set `DRAFTLY_RETRIEVAL_SMOKE=1` when executing the notebook to verify the
pipeline against a small corpus sample without replacing the full-run outputs.

## Retrieval Gold Schema

Each gold row should represent one answerable legal retrieval task.

| Column | Meaning |
| --- | --- |
| `question_id` | Stable ID from the past-paper queue or manual lawyer question |
| `question_text` | The legal problem or lookup question |
| `workflow` | `conveyancing`, `litigation`, or another supported workflow |
| `topic_ids` | Semicolon-separated curated topic IDs |
| `matter_date` | Optional date for point-in-time law |
| `target_court` | Optional court context for authority ranking |
| `expected_source_ids` | Statutes, amendments, gazettes, or guides that must be found |
| `expected_sections` | Expected section identifiers or section numbers |
| `expected_case_ids` | Expected case records where known |
| `expected_case_citations` | Human-readable citations where IDs are not mapped yet |
| `must_include_terms` | Legal concepts that should appear in a grounded answer |
| `gold_status` | `draft`, `reviewed`, `lawyer_verified`, or `retired` |
| `reviewer_notes` | Why the label is correct or uncertain |

## Core Metrics

Retrieval metrics:

- `Recall@k`: whether each expected authority appears in the top k.
- `MRR`: how high the first correct authority appears.
- `nDCG@10`: ranking quality when some authorities are more important.
- `All-Recall@k`: whether all required authorities appear for multi-source
  questions.
- `Authority precision`: whether Supreme Court, Court of Appeal, High Court,
  and unreported materials are ranked and labelled correctly.
- `Temporal accuracy`: whether the in-force version is selected for the matter
  date.

Answer-grounding metrics:

- `Citation precision`: cited authorities resolve inside Draftly's corpus.
- `Citation false positives`: citations that do not exist in the closed corpus.
- `Evidence support`: cited passages actually support the claim.
- `Abstention quality`: the system refuses or asks for review when the corpus
  cannot support the answer.

## Current Caveat

The Final Year papers are partly scanned. The current `pdftotext` pass extracts
text from only some bundles; scanned bundles must go through OCR before they can
produce reliable LW 307 Conveyancing question rows.
