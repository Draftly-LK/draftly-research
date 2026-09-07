# Phase 0 inventory: authority sources available to legal-qa-v1

Run `2026-09-05-pilot-01`. Compiled 2026-09-05 from the repository files named
below. Nothing listed here is lawyer-verified; every status field observed in
the corpus reads `unverified` unless stated otherwise.

## Benchmark input

- `data/evaluvation/parsed-pastpapers/benchmark/selected-matters.jsonl` (44 matters)
  and `selected-questions.jsonl` (84 questions), built by
  `scripts/pastpaper-dataset/build_selected_matters.py`. Not modified by this run.

## Statute sources

| Source | Path | Count | Verification signal |
| --- | --- | --- | --- |
| Canonical statute trees | `data/processed/canonical-statutes/*.json` | 52 files, 1,521 sections | `verification_status`: 44 unverified, 7 structurally_verified, 1 needs_structural_review |
| Canonical amendment trees | `data/processed/canonical-amendments/*.json` | 127 files | all unverified; `amends` often empty |
| Finalized trees | `data/legal-sources/library/finalized/` | 39 statute dirs, 63 JSON | same key set as canonical copies |
| Finalized source packages | `data/legal-sources/library/finalized-sources/*/manifest.json` | 28 statutes | only place with per-file sha256 and role/edition |
| Source registry | `data/legal-sources/manifests/source-registry.csv` | 90 rows (57 statutes, 18 amendments, 7 gazettes) | `status` is acquisition state only; sha256 on 79 rows |
| Section index | `data/legal-sources/manifests/statute-section-index.json` | 75 statutes, 6,169 sections | headings only, no locator, no text |
| Library PDFs/HTML | `data/legal-sources/library/statutes/`, `amendments/` | 38 statute PDFs, 55 HTML; 166 amendment PDFs | 41 of 90 preferred URLs are lankalaw.net (private republisher) |

Structurally verified trees: Registration of Title Act 21/1998 (SRC011),
Land (Restrictions on Alienation) Act 38/2014 (SRC021), Companies Act 7/2007
(SRC031), Survey Act 17/2002, Kandyan Succession Ordinance, Muslim Intestate
Succession Ordinance, Nindagama Lands Act.

Official-issuer files present: Inland Revenue Department PDFs for the Stamp Duty
Act 43/1982 and Stamp Duty (Special Provisions) Act 12/2006 (cover note
disclaims statutory-copy status), rgd.gov.lk PDFs for the Notaries Ordinance
and its 2022 and 2024 amendments and for the Land (Restrictions on Alienation)
Act, documents.gov.lk and parliament.lk files, and one Government Printer
Survey Act.

## Temporal data

| File | Rows | What it gives | What it cannot give |
| --- | --- | --- | --- |
| `data/processed/section_versions.jsonl` | 7,034 | version intervals per section, `is_current`, `text_available` | superseded wording (`text_available` false for all old versions) |
| `data/processed/actions.csv` | 872 | which amending Act touched which section | what changed (`operation` unknown on 853 rows) |
| `data/processed/amendment-chains.csv` | 281 | instruments folded into each consolidation | section-level effect |
| `data/processed/statute_commencement.csv` | 62 | commencement of the principal enactment (srilankalaw.lk) | commencement of later versions (year-keyed only) |

Consequence for this run: `applicable_version_for_matter_date` can usually be
stated only as `current_text_applicable` when no amendment is recorded after the
matter date, or `history_unknown` when one is. The verifier must read the
amending Act PDF itself to do better.

## Case-law sources

| Source | Path | Count | Notes |
| --- | --- | --- | --- |
| Case metadata | `data/processed/cases.jsonl` | 9,177 | metadata only; `text_path` points to judgment markdown |
| Judgment text | `data/processed/docs/case-law/{commonlii,courts,internet-archive}/` | 9,210 markdown files | CommonLII HTML strip (NLR/SLR to about 2001), court PDFs (text layer), 33 OCR volumes |
| Extracted rules | `scripts/case-law-information-extraction/output/rules.csv` | 4,161 | Track A `Held:` blocks and Track B LLM rules; grounding-gated; all unverified |
| Case-to-section links | `data/processed/case_statute_section_links.csv` | 14,665 | citation-mention detection; all `review_status=unverified` |
| Resolved links | `scripts/case-law-statute-linking/output/resolved_links.csv` | 762 | 462 `verified` band by resolver agreement, not by a lawyer |
| Modern SLR | `data/legal-sources/manifests/slr-modern-cases.csv` | 631 | index only, no local text |

There is no case-law full-text search index. Candidate cases come from the link
tables and rules file and must then be read in the judgment markdown.

## Retrieval capabilities

- `uv run python -m draftly.retrieval search "<query>" [--source-id SRCnnn]`:
  reciprocal-rank fusion of BM25, Gemini dense (key present) and graph
  expansion over 57 statutes and 18 amendments; direct Act plus section lookup
  when the query names the title or source id and a section number.
- No case-law retrieval beyond CSV lookup and grep.
- Experimental statute retrievers under `experiments/koblex-inspired-retrieval/`
  and `experiments/HiREC-inspired-retrieval/` (statute corpus only).

## Document templates

- No deed, mortgage bond, lease, power of attorney or affidavit templates exist.
- `docs/RTA_notes/sample-*.doc[x]` hold Registration of Title Act sample
  instruments and a gift attestation clause (not opened in this run).
- `data/matters/` holds real client files. Off limits for benchmark content.
- Synthetic documents in this run are therefore rendered from templates defined
  inside the pipeline scripts, with `template_id` recorded per document.

## Validation utilities

- `jsonschema` 4.26 is installed (transitive dependency).
- Existing checkers are hand-rolled: `data/evaluvation/validate_pastpapers.py`,
  `scripts/verify_processed_store.py`, `scripts/audit_corpus.py`.
- This run adds `scripts/legal-qa-pipeline/` with schema-driven validators.

## Missing source packages and gaps relevant to the 44 matters

- No servitude or Roman-Dutch common-law source of any kind. Matter M038
  (right of way) cannot be researched from this corpus.
- Stamp Duty Act rates schedule was not extracted (about 11 percent of the PDF
  unmatched); Stamp Duty (Special Provisions) Act 12/2006 exists only as an
  amendment tree with empty `amends`. Stamp-duty computations (16 questions
  across the 44 matters) are at risk of `blocked_missing_authority`.
- Partition Law 21/1977: index headings only, no tree.
- Notaries, Powers of Attorney, Prevention of Frauds, Wills, Trusts and
  Apartment Ownership amendments exist as PDFs without trees.
- No per-section locator in any tree; this run uses JSON pointers into the
  tree file plus the file sha256, and PDF page numbers where pdftotext resolves.
- Two registries disagree (`data/processed/source-registry.csv` is a stale
  2026-07-16 copy of the manifests file).

## Pilot selection

- M022 (paper 11, October 2020): two-notary execution of a company lease and
  the contents of the first notary's attestation. One enactment, the Notaries
  Ordinance, with a live temporal question because two amendments post-date
  the exam. Chosen as the statute-driven pilot.
- M001 (paper 1, April 2026): partition decree, deed of gift subject to life
  interest, revocation of life interest, three deaths, intestate shares and a
  foreign-citizen heir under the Land (Restrictions on Alienation) Act 38/2014.
  Multiple provisions, multiple instruments and a rich document bundle. Chosen
  as the complex pilot. The one structurally verified conveyancing tree in the
  corpus (SRC021) is exercised here.
- Rejected: M038 (no servitude source), stamp-duty-only matters (rates
  schedule missing), pedigree-only matters (near-duplicates of M001's issue).
