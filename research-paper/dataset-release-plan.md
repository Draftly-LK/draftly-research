# Public dataset release plan

Status: two datasets are public under `lanka-legal-nlp` and tagged. The team reports Law College redistribution permission.

## Local implementation

Run `python scripts/dataset-release/build_release.py` to build the two review packages under the Git-ignored `tmp/hf-release/` directory. The builder exports `benchmark_v1`, `source_papers`, `atomic_question_pool`, lineage, the evaluation package, an Act metadata/link index, draft dataset cards and file-hash manifests. See `scripts/dataset-release/README.md`.

The current build has 50 benchmark questions, 16 structured papers, 667 atomic questions and 112 Act rows. The Act index has 52 recorded source URLs, 16 registry URL candidates and 44 rows without a URL. An HTTP check found 58 reachable linked rows and 10 unreachable linked rows; it did not verify edition identity. The team reports permission to redistribute Law College question text. No licence for the underlying question text has been inferred from that permission.

Public repositories: [statutory retrieval benchmark](https://huggingface.co/datasets/lanka-legal-nlp/draftly-statutory-retrieval) tagged `v1.0-paper-provisional`, and [Act source index](https://huggingface.co/datasets/lanka-legal-nlp/draftly-sri-lanka-act-sources) tagged `v1.0-paper-corpus-links`. Remote file hashes were checked against the local packages before transfer. Both repos were transferred to the `lanka-legal-nlp` organization; their commit IDs and public visibility were verified afterward. All four dataset configurations loaded through the Hugging Face `datasets` library before transfer.

## Decision

Publish two related resources under the team's Hugging Face organisation:

1. A versioned **open statutory retrieval benchmark** with scenario questions, matter-level development and test splits, openly available proposed gold (provisional reference labels; pending lawyer validation), a small evaluation package, and separate source collections for the structured past-paper JSON and atomic questions.
2. A **Sri Lankan Act source index** starting with the 112 documents in the paper corpus. It can contain enactment metadata and source-edition URLs without uploading PDFs or extracted statutory text. Keep the parsed Act corpus internal for now; add wider coverage in a later version.

Use separate repositories so that the source index can be corrected as URLs and editions change without silently changing the frozen benchmark. Link each repository from the other's dataset card.

## What exists now

- The main benchmark has 50 questions in 40 matters: 10 development questions and 40 test questions. The 73-question extended set is a separate research pool, not the main scored benchmark.
- All 50 main gold rows have `lawyer_validation_status: pending`. The paper measures retrieval of indispensable statutory sections, not generated-answer accuracy. The public name and card must say this plainly.
- The source collection has 16 structured past-paper question JSON files and 667 atomic question records. These are provenance and future-curation material. Only the 50-question subset has the paper's proposed section gold; the other 617 atomic records must not appear to be evaluated benchmark items.
- The frozen corpus contains 112 documents: 52 principal enactments and 60 amending Acts. Its `acts.jsonl` has no URL field. The 52 principal records can currently be matched to a source URL in their finalized source document or the source registry; the 60 amendment records need URL matching before a complete link index can be claimed. These counts describe the current files, not live-link validation.
- The wider source registry has 90 rows across statutes, amendments and other source types. Reconcile it with the 112-document corpus and other Act inventories to expand the index, deduplicating by enactment and edition. Do not describe the resulting list as all Sri Lankan legislation.
- Some recorded source editions are hosted by LankaLaw or other third parties. Preserve the publisher and edition type for each row. Do not describe every link as an official source.

Source files: `data/evaluvation/statutory-qa-v1/README.md`, `benchmark/`, `corpus/manifest.json`, `corpus/acts.jsonl`, `data/evaluvation/parsed-pastpapers/questions/`, `data/evaluvation/parsed-pastpapers/atomic/atomic-questions.jsonl`, `data/legal-sources/manifests/source-registry.csv`, and `data/legal-sources/library/finalized/`.

## Phase 1: settle the release boundary

1. Confirm the team or organisation account, repository names and dataset citation. Suggested names: `draftly-statutory-retrieval` and `draftly-sri-lanka-act-sources`. Freeze the paper snapshot as `v1.0-paper-provisional`; reserve `v1.1-corrections` for documented fixes and `v2.0-lawyer-validated` for a future lawyer-approved release. Never overwrite the paper snapshot.
2. Check whether the Law College permits redistribution of the exam question text and fact patterns, including the 16 structured JSON files and verbatim source quotes. Public availability of an exam PDF does not, by itself, establish a redistribution licence. If permission is unavailable, release a metadata and source-link index first, then add question text only after permission or a reviewed rewrite.
3. Review question text for personal details, property addresses, deed numbers and other identifiers, even where they appear to be exam hypotheticals. Publish no material from `data/raw/` or lawyer review workbooks.
4. Choose a licence only for material the team has the right to license. Record source-specific rights and any excluded fields in the dataset card. Do not assign a blanket open licence to linked third-party Acts or exam papers.

## Phase 2: prepare the benchmark package locally

1. Export from the frozen `public-input.jsonl`, `private-gold.jsonl` and split ID files. Preserve `benchmark_matter_id` and `benchmark_question_id` so related questions cannot cross splits. Use the existing 10-question development and 40-question test split; do not generate a new split.
2. Publish development and test section labels openly as **proposed gold (provisional reference labels; pending lawyer validation)**, with `lawyer_validation_status: pending`, provision verification status and a versioned correction path. Open test labels support transparent evaluation and inspection of the paper's reference labels. Full reproduction of the reported retrieval scores additionally requires the frozen statutory corpus, its verified reconstruction, and equivalent retrieval implementations. Open test labels also make this test set unsuitable as a hidden challenge, so any later challenge needs a new held-out set.
3. Use three visibly distinct dataset configurations: `benchmark_v1` for the 50 scored questions and labels, `source_papers` for reviewed exports from the 16 `paper-XX.questions.json` files, and `atomic_question_pool` for the 667 atomic question records. Preserve `paper_no`, session, question number, page and atomic ID. Add a public lineage table from each scored benchmark question to its source atomic ID without copying answer labels into input fields. Only `benchmark_v1` is the evaluated benchmark; the other configurations carry no paper-score claim.
4. Strip local file paths, OCR internals and duplicate verbatim quote fields from the public source-paper export unless they are needed and approved. Record extraction status and known OCR or parsing defects; do not describe the entire 667-question pool as clean or lawyer reviewed.
5. Keep the 73-question extended pool out of the main benchmark configuration until its separate status and legal-review issues are documented.
6. Exclude agent research notes, draft answers, review packets, workbooks, raw rankings, local paths, caches and source PDFs from the public package unless separately reviewed. A release manifest should list every included file and its hash.
7. Include a small, independently runnable evaluation package: prediction-file schema, `C@20` and Indispensable Recall@20 implementations matching the paper's matter-level aggregation, a matter-split validator, and example predictions with expected metric output. Keep retrieval systems, prompts and Draftly product code outside this release.
8. Write a dataset card covering source papers, extraction and enrichment, annotation and verification roles, split policy, intended retrieval task, limitations, licensing, privacy review and the exact relation to the accepted workshop paper. Display this sentence prominently: **These labels are pending lawyer validation.** Distinguish evaluating submitted predictions from reproducing the paper's complete experiments.

## Phase 3: build the Act link index

1. Export one row per corpus `act_id` with title, number, year, principal/amendment kind, edition kind, publisher, source URL, source host, source ID where present, corpus fingerprint and a link-check date. Keep `source_url` empty when unknown; never invent or silently substitute a different edition.
2. Match the 60 amendments to their source registry entries or authoritative publication pages by enactment number, year and title. Prefer a stable official publication URL when the edition matches; retain a third-party URL with its publisher label where an official match is unavailable.
3. Check each URL resolves and points to the intended enactment and edition. Record redirects, inaccessible sources and alternate URLs. A source landing-page URL is acceptable when no stable direct PDF URL exists.
4. Publish coverage counts for the 112 paper-corpus documents: linked, unresolved and link-checked. Label the index **partial** while links remain unresolved. Stabilize this subset before expanding the index.
5. In a later index version, reconcile the wider source registry and other documented Act inventories. Add `in_paper_corpus`, `coverage_topic`, `source_status` and `edition_status` fields so the expansion does not change what the paper evaluated. Do not describe this wider list as all Sri Lankan legislation.
6. Explain that a URL index is a discovery aid. External pages can change, and a linked edition may not match the normalized sections used in the paper. Full reproduction needs the frozen corpus, a verified reconstruction and equivalent retrieval implementations. The link index alone does not provide these.

## Phase 4: publish and maintain

1. Stage the benchmark package in a private Hugging Face dataset repository and inspect its file list and dataset viewer. Keep it private until permission to redistribute the Law College question text is resolved and the record-level review is complete. The reviewed Act metadata/link index can be released separately when its own checks pass.
2. Run schema, split-disjointness, record-count, metric-example, hash, URL and prohibited-file checks against the staged exports. Have a team member review the actual staged rows, evaluation package and card.
3. Make approved repositories public under immutable `v1.0-paper-provisional` tags. Add dataset URLs and versions to the camera-ready paper if timing and workshop rules permit.
4. Publish corrections under `v1.1-corrections` and later lawyer-approved labels under `v2.0-lawyer-validated`. Preserve the provisional reference-label snapshot used for the paper and document every correction.

## Release gates

| Resource | Ready for public release when |
| --- | --- |
| Act source index | The first release covers only the 112 paper-corpus documents; each published row has checked provenance; missing URLs and third-party editions are labelled; no Act PDFs or extracted text are included. |
| Past-paper JSON | Redistribution rights and record-level privacy review cover the source questions and quotes; each file has provenance and extraction status; unannotated questions are distinct from the scored set. |
| Benchmark questions | Redistribution rights and the record-level privacy review are complete; the published split, lineage and card match the frozen study. |
| Proposed gold | Every provisional reference label is marked pending lawyer validation; development and test labels are open; limitations and correction policy are in the card. |
| Evaluation package | Prediction schema, both metrics, split validator and example predictions pass checks against the frozen benchmark. |

Hugging Face documentation: [uploading datasets](https://huggingface.co/docs/hub/datasets-adding), [dataset cards](https://huggingface.co/docs/hub/datasets-cards), and [data file configuration](https://huggingface.co/docs/hub/datasets-data-files-configuration).
