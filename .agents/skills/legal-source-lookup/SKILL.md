---
name: legal-source-lookup
description: Answer a Sri Lankan conveyancing question using the curated legal-source library in data/legal-sources/, and return the answer with exact citations (Act/Ordinance name, number, year, section). Use this skill whenever a question concerns Sri Lankan conveyancing, deeds, notaries, registration of documents or title, stamp duty, condominium/apartment property, powers of attorney, wills, trusts, state lands, or local-authority/UDA regulations.
version: 0.1.0
license: MIT
compatibility: Any AI coding assistant that supports the agentskills.io SKILL.md format (Claude Code, Codex, Cursor, VS Code Copilot, OpenHands, etc.). Requires read access to the repository and a file-search tool (grep/ripgrep) and file reader. No external APIs.
metadata:
  author: Draftly
  tags: legal retrieval conveyancing citations sri-lanka
  agentskills_spec: "1.0"
---

# Legal Source Lookup

Answer a legal question about Sri Lankan conveyancing **only** from the curated
corpus in `data/legal-sources/`, and always cite the source. Never invent
statutes, sections, case names, dates, or legal claims — if the corpus does not
support an answer, say so.

## The corpus you work from

- `data/legal-sources/manifests/source-registry.csv` — the **index of record**.
  Columns: `source_id`, `official_title`, `act_or_ordinance_no`, `year`,
  `source_type` (statute | amendment | gazette | case-law | institution-guide),
  `topics` (semicolon-separated topic numbers), `preferred_source_url`,
  `local_pdf_path`, `local_markdown_path`, `status`, `sha256`, `download_date`,
  `notes`.
- `data/legal-sources/topics/<NN-topic-name>/manifest.md` — 20 curriculum
  topics; each lists the `source_id`s relevant to that topic and their role.
- `data/legal-sources/library/…` — the actual PDFs (and extracted markdown when
  present), grouped as `statutes/`, `amendments/`, `case-law/`, `gazettes/`,
  `institution-guides/`.

## Procedure

1. **Classify the question into topic(s).** Match it to one or more of the 20
   topics under `data/legal-sources/topics/`. If unsure, scan the topic
   `manifest.md` "Purpose" sections.
2. **Resolve candidate sources.** From the matched topic manifest(s), collect
   the `source_id`s. Cross-check against `source-registry.csv` — filter by the
   `topics` column and `source_type`.
3. **Account for amendments (in-force check).** A statute is rarely the whole
   story. For every candidate statute, look for related rows where
   `source_type = amendment` that touch the same subject, and prefer the
   consolidated/most-recent text. State clearly which version you relied on and
   its date. Do **not** assert something is "current law" unless the registry
   supports it.
4. **Locate and read the text.** Open `local_markdown_path` if present;
   otherwise read `local_pdf_path`. Search within for the relevant section
   using the question's key terms.
5. **Answer with citations.** Every legal claim must carry: official title +
   `No. X of YYYY` + section/article, and the `source_id`. Example:
   *"Prevention of Frauds Ordinance No. 7 of 1840, s. 2 (SRC001)."*
6. **Report gaps honestly.** If the corpus lacks the source, or the source is a
   public consolidation rather than an official gazette (see the `notes`
   column), say so. Distinguish "the corpus says X" from "X is the law."

## Hard rules

- **No invention.** No fabricated sections, cases, dates, or holdings. Ground
  every statement in a cited source row.
- **Privacy.** `data/raw/` holds private client matters. Do not surface real
  names, NICs, or addresses from it in any public-facing output. This skill
  reads the *library*, not `data/raw/`, unless the task explicitly scopes a
  matter and the output stays internal.
- **Provenance over fluency.** A precise citation with a caveat beats a
  confident paraphrase. When unsure, retrieve more; do not guess.

## Output shape

Return: (1) a direct answer, (2) the citations behind it as a short list of
`source_id → title, section`, and (3) any caveats about version/in-force status
or missing sources.
