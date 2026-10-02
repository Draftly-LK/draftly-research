---
pretty_name: Draftly Statutory Retrieval Benchmark
language:
  - en
task_categories:
  - text-retrieval
configs:
  - config_name: benchmark_v1
    data_files:
      - split: development
        path: benchmark_v1/development.jsonl
      - split: test
        path: benchmark_v1/test.jsonl
  - config_name: source_papers
    data_files:
      - split: source
        path: source_papers/data.jsonl
  - config_name: atomic_question_pool
    data_files:
      - split: source
        path: atomic_question_pool/data.jsonl
---

# Draftly Statutory Retrieval Benchmark

The team reports permission to redistribute the Sri Lanka Law College question text. This release includes only past-paper-derived questions and research labels; it contains no client documents from `data/raw/`. The card does not assign a licence to the Law College's underlying paper text.

The evaluated `benchmark_v1` configuration contains 50 scenario questions in 40 matters from Sri Lanka Law College conveyancing examinations. Development has 10 questions; test has 40. Questions from one matter stay in one split. The task is to rank statutory section IDs for each question.

**These labels are pending lawyer validation.** The section IDs are proposed gold (provisional reference labels), produced and checked by research agents. They are not lawyer-approved answers or legal advice. The paper measures retrieval, not answer generation.

`source_papers` contains structured questions from 16 exam papers. `atomic_question_pool` contains 667 extracted question records. These are source and curation collections, not the evaluated benchmark. Most have no section labels. `benchmark_v1/lineage.jsonl` connects scored questions to atomic records.

The release includes `evaluation/evaluate.py`, a prediction schema, and example predictions. It computes complete-indispensable recall at 20 (`C@20`) and Indispensable Recall@20 per question, averages questions within each matter, then averages matters. Open labels allow evaluation and inspection. Full reproduction of the paper's retrieval scores also requires the frozen section corpus or its verified reconstruction and equivalent retrieval implementations. The Act link index alone does not provide these.

To score a complete development or test split, supply one JSON Lines prediction per question. Each row needs `benchmark_question_id` and an ordered `ranked_section_ids` list. The evaluator rejects missing or duplicate predictions. Its example predictions cover the development split and include expected output. The paper's reported `C@20` and Indispensable Recall@20 use matter macro means; the standalone evaluator was checked against the paper's S5 test results.

Only reviewed question text and provisional section IDs belong in this package. It excludes source PDFs, draft legal answers, lawyer workbooks, internal notes, retrieval code and private client documents. The source collection may contain OCR or parsing errors. The original paper text requires a separate redistribution decision; no blanket open licence is asserted here.

Planned versions: `v1.0-paper-provisional` preserves the paper snapshot; `v1.1-corrections` records fixes; `v2.0-lawyer-validated` is reserved for a future lawyer-approved set. The main 50-question set is frozen for the paper. Open test labels make it unsuitable as a hidden challenge.

For provenance and corrections, use the `source_atomic_id` in `benchmark_v1` and the `benchmark_v1/lineage.jsonl` file. The `release-manifest.json` file lists SHA-256 hashes of the uploaded files. Report suspected label errors through the repository's community discussion page; corrections belong in a new version.
