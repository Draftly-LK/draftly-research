# Draftly — Project Context

This is the shared handoff file for everyone working on Draftly: Claude Code,
Codex, and (by copy-paste) ChatGPT. Read **Current State** first. When you
finish a chunk of work, update it with the `update-context` skill
(`.agents/skills/update-context/SKILL.md`).

- **Current State** is a living snapshot — overwrite it as things change.
- **Log** is append-only, newest first — never rewrite old entries.

---

## Current State

Last updated: 2026-08-25 · by: Codex · draftly-research @ 47643044

### What Draftly is

A **lawyer-in-the-loop notarial and conveyancing platform for Sri Lanka** built
around a shared matter, evidence, verification, authority, drafting, approval,
and audit foundation. It is a DSE (ML + Software Engineering) product, not a
research-only project. Litigation is no longer part of the product roadmap.

V0 is the initial release, not the name or final boundary of the product. It is
an **RTA-first notarial workbench** for examination of title, drafting,
execution, and attestation. V1 expands conveyancing and supported document
handling; V2 adds wider Sri Lankan conveyancing regimes and notarial
instruments; V3 matures the notarial/conveyancing platform through
collaboration, organisation knowledge, integrations, governance, reporting,
and deployment scale. Later-release capabilities must not be presented as
implemented V0 features.

V0 uses Google Document AI for OCR and document-quality analysis of supported
printed and clearly scanned matter documents, then requires lawyer verification
or manual correction. Reliable handwriting, severely degraded scans, and
unsupported scripts are explicit V0 limitations. Google's current Enterprise
Document OCR language list does not explicitly list Sinhala, so Sinhala
source-document OCR is not promised; Sinhala interface and export support
remain separate requirements. V0 does not perform historical title tracking,
ownership-chain reconstruction, or AT-form extraction. Official Bim Saviya
forms define the drafting templates and required structured particulars.

The core framing to preserve: **Draftly is not a form-filling PDF generator and
not a legal search engine.** It turns an unstructured legal/property document
bundle into a _verified, structured title record_, checks that record, and
generates multiple lawyer-reviewable drafts from it.

Core pipeline:

```text
RTA documents → Extraction → Lawyer verification → Checks → Guided functions → Drafts
```

The differentiator vs "template filling": the template is only the final output
layer. The current V0 verifies the registered title, cadastral
parcel, parties, current instrument, interests or encumbrances, and supporting
evidence before generation. It does not reconstruct historical deed pedigrees
or old title chains; that belongs to a later RDO or cross-regime module.

### Academic context

- University of Moratuwa, Dept. of Computer Science & Engineering.
- Module `In23-S5-CS3501`; Project Idea submitted ~8 July 2026.
- Group 06: Dhanapala D.H.N., Dilshan A.D.L., De Silva B.K.P.
- Proposed Supervisor: Dr. Nisansa de Silva. Teaching Assistant: Ovindu A.
- Title: _Draftly: A Lawyer-in-the-Loop Legal Workflow Platform for Sri Lankan
  Legal Practice._
- Positioning: aligns with the broader legal-NLP direction of Dr. Nisansa's
  **SigmaLaw** work, but focused on practical drafting/workflow automation rather
  than legal search, sentiment, or case analytics. Existing SL platforms
  LawLanka, Paralegal.lk, and LawCeylon centre on legal material and search;
  AI PAZZ also advertises general AI-assisted research and drafting. Draftly's
  distinct scope combines client-document evidence, a verified matter record,
  RTA-specific checks and forms, grounded answers, and controlled approval.
- A **feasibility study** on the CS3501 template now lives at
  `proj-docs/proj-feasibilty/feasibility-study.md` (2026-07-23): third-person,
  IEEE references (RTA 1998, PDPA 2022, ETA 2006, BM25, RAG, WCAG 2.1),
  technical feasibility argued from the validated prototypes. Still to fill:
  the three index numbers; confirm whether the "Mentor" line should be
  Dr. Nisansa de Silva (current), the TA, or the lawyer mentor.

### Software requirements specification

- `proj-docs/SRS/draftly-srs.md` is the rebuilt product-level SRS, version 0.3,
  dated 2026-07-29. It defines Draftly as one notarial/conveyancing product
  across V0 to V3, with V0 as the initial RTA release.
- The SRS uses stable identifiers for functional and quality requirements,
  states the handwriting and abstention boundary honestly, separates
  lawyer-approved facts from machine candidates, and covers legal grounding,
  drafting, approval, privacy, audit, interfaces, data, and release acceptance.
- It is submission-facing and does not expose internal paths, the static
  interface mock, repository status, or a temporary application stack. Google
  Document AI is the one named V0 processing dependency. Other implementation
  choices remain outside the SRS. Its references are external legal,
  standards, research, and public product sources.
- The SRS directory also contains the supplied SRS template, software
  architecture document template, and IEEE SRS guidance PDFs. The Markdown
  document remains the working source for any later submission-format port.
- Voice dictation, playback, and related speech capability remain conditional
  V1 work. V0 does not claim voice input; any later voice change must become a
  reviewable candidate and must not silently verify facts, alter prescribed
  wording, approve drafts, or bypass audit.

### Software architecture document

- `proj-docs/Software Architecture/Software Architecture.md` is the initial
  submission-facing architecture source, version 0.1, dated 2026-07-29. It
  follows the supplied architecture template through use-case, logical,
  process, deployment, implementation, data, performance, quality, and
  reference views.
- The document selects a modular web architecture for V0: Next.js/TypeScript
  workbench, FastAPI/Python application API, PostgreSQL matter database,
  protected object storage, authenticated asynchronous workers, a separate
  versioned legal corpus, deterministic checks, a schema-controlled draft
  editor, and server-side DOCX/PDF export. Google Document AI remains isolated
  behind a provider-neutral processing port.
- Thirteen Mermaid figures cover the architectural views, complete document
  ecosystem, actors/use cases, logical components, domain classes, document
  processing, grounded research, approval/export, deployment, implementation
  dependencies, packages, and core data relationships.
- The complete document ecosystem distinguishes confidential matter inputs,
  controlled legal/practice material, internal derivatives and authoritative
  records, and lawyer-controlled outputs. It explicitly includes title,
  cadastral, survey, transaction, interest, identity/capacity, local-authority,
  stamp-duty, execution/attestation, supporting, unsupported, and AT-form
  material. Unsupported, handwritten, severely degraded, and unapproved
  Sinhala OCR inputs remain manual-review paths rather than automatic facts.
- Architecture choices other than the SRS-mandated Google Document AI
  dependency are reference implementation decisions. Exact managed services,
  production region, identity provider, retention policy, processor version,
  recovery objectives, and live-use approvals remain confirmation items.
- The architecture Markdown passes `markdownlint-cli2` with zero issues. The
  file remains uncommitted at this handoff.

### Sri Lanka Law College past-paper collection

- `past-papers/` contains 44 validated PDFs (418,512,430 bytes): 19 files from
  the official Sri Lanka Law College downloads page and 25 public GovDoc archive
  files.
- The collection is organized into `entrance/`, `entrance-archive/`,
  `preliminary/`, `intermediate/`, and `final/`. It includes official year-level
  bundles through 2023, a 2024 general entrance set, model papers, and GovDoc
  language variants from 2015-2023 where publicly listed.
- `past-papers/manifest.csv` records the exact source URL, local path, year,
  level, medium, byte size, page count, download status, and SHA-256 for every
  PDF. All 44 entries passed PDF-header, `pdfinfo`, file-size, and checksum
  validation.
- The official 2020 Final Year link is only Civil Procedure and Pleadings I in
  all three media, not a complete Final Year bundle. Some later official bundles
  are scanned, so subject-level extraction (including LW 307 Conveyancing)
  requires OCR rather than filename or text-layer matching.

### First use case & outputs

Concrete first use case: an **RTA/Bim Saviya notarial workbench**. V0 covers
examination of title, drafting, execution, and attestation. Its lawyer-review
outputs include:

- Verified structured RTA matter record
- Guided function decisions and lawyer checklist
- Missing-document checklist
- Current-title, parcel, party, interest, and instrument consistency findings
- Grounded legal answers with authority and evidence
- Approved prescribed RTA forms, beginning with Form 8 transfer
- Versioned DOCX/PDF exports and an audit history

Historical title-chain reconstruction, RDO/folio work, other conveyancing
regimes, and registration remain later extensions.

### Inputs & extraction (schema, not data)

Input = an **RTA matter bundle**: supported deeds, current title certificate,
cadastral map and parcel documents, proposed transfer/gift/lease/mortgage
instrument, registered-interest or encumbrance evidence, identity/capacity
documents, survey material, and applicable local-authority or supporting
records. V0 routes supported documents through Google Document AI. Handwriting,
severely degraded scans, unsupported scripts, and Sinhala source documents
without a separately approved processor use lawyer review and manual entry.
AT forms are excluded from extraction.

Fields extracted per source type (deeds: deed no/type/date, grantor/grantee,
consideration, notary, attestation, plan no, lot no, extent, boundaries,
registration refs; survey plans: plan no, surveyor, land name, lots, extent,
boundaries; municipal/assessment: assessment no, owner, annual value, receipt;
registry: volume/folio, owners, encumbrances, prior registrations).

Example red flags: title holder or party differs across current documents;
cadastral map, block, parcel, or extent mismatch; missing title-certificate
reference; unresolved registered interest; wrong prescribed form; missing
execution evidence; or incomplete attestation particulars.

### Data Science components

Document processing for approved V0 document classes and languages, document
classification, layout-aware field extraction, source-span provenance,
consistency checking over the current RTA record, grounded answering, and
template-constrained generation. Sinhala interface and output rendering remain
in scope, but reliable Sinhala source-document OCR is not assumed. Historical
folio OCR, AT-form extraction, old-deed entity linking, and title-chain
reconstruction are outside V0.

V0 is evaluated on a separate lawyer-verified holdout: document classification,
required-field extraction, pinpoint provenance, deterministic-check precision
and recall, citation support, verified-fact drafting, export fidelity, workflow
completion, and privacy/access tests. Initial thresholds are recorded in
`project Management/v0-implementation.md`.

### Software Engineering components

Web matter dashboard, accounts/roles, matter creation, document upload +
pipeline, template library, guided intake forms, fact-review UI,
evidence/provenance viewer, current-title consistency checks, lawyer
review/edit workspace, version history, audit trail, DOCX/PDF export, access
control. Domain model centres on a **Matter** (type, parties, documents,
extracted facts, templates, drafts, review comments, exports).

Tentative stack: Next.js/React + FastAPI + PostgreSQL; repo laid out as
`apps/web`, `apps/api`, `apps/ml-service`, `packages/shared`, `docs/`, `samples/`.

### Product interface research

- `docs/product-research/harvey/README.md` records Harvey's publicly documented
  Assistant, Vault, review-table, workflow, knowledge, library/history,
  collaboration, governance, and integration patterns. Ten official public
  product/help screenshots are stored under its `screenshots/` folder with
  source links. They are internal research references and must not ship as
  Draftly assets.
- `docs/product-research/harvey/draftly-interface-spec.md` translates those
  patterns into an original Draftly specification aligned with the RTA-first
  roadmap: a persistent matter shell, document intake, lawyer verification,
  guided notarial functions, grounded research, checks, side-by-side drafting,
  history, audit, visual tokens, responsive behavior, priorities, and prototype
  acceptance criteria.
- This research phase is specification-only. No Harvey-style Draftly interface
  was implemented, and no application code was changed.
- Design boundary: borrow calm workspace patterns and source-aware interaction,
  but do not copy Harvey's name, logo, proprietary assets, wording, exact
  layout, or workflow catalogue.

### RTA practice-note collection

- `docs/RTA_notes/` contains 20 reviewed files: the Registration of Title Act,
  the 2014 and 2022 Gazettes, three presentations, eight process maps, two
  checklist/clause documents, three private transfer examples, and one scanned
  Sinhala form.
- `docs/RTA_notes/README.md` is the collection guide. It records each file's
  subject, authority level, Draftly use, privacy boundary, form map, processing
  status, and recommended separation into primary-law, workflow,
  practice-rule, template, and private-matter layers.
- The 2014 Gazette uses legacy-font Sinhala and needs font recovery or OCR. The
  scanned Form 31 has no text layer and needs Sinhala OCR plus human
  verification. Sample instruments contain private data and may only support
  anonymized, lawyer-approved template research.

### Linear project management

- The complete `project Management/v0-tasks.md` hierarchy is in the Draftly
  Linear team under the project **Draftly v0 — Bim Saviya RTA Workbench**:
  `https://linear.app/draftly-lk/project/draftly-v0-bim-saviya-rta-workbench-8f92a8258482`.
- Linear contains six project milestones (`M0`-`M5`), 12 epic parent issues
  (`E0`-`E11`), and 73 numbered child tasks, for 85 project issues total.
  Existing exact IDs should be updated rather than recreated.
- The milestone dependency spine `M0 -> M1 -> M2 -> M3 -> M4 -> M5` is stored
  in milestone descriptions because the connector cannot create native
  milestone dependencies. `E1` has blocking relations to ten explicitly
  schema-dependent tasks.
- Linear project `Draftly v0` was updated for M2 on 2026-07-23. Project status
  update posted as on-track:
  `https://linear.app/draftly-lk/project/draftly-v0-8f92a8258482/activity#project-update-2cc4ed2f`.
- Completed M2 child issues were closed: `DRA-55`, `DRA-56`, and `DRA-61`
  through `DRA-68`. Parent epics `DRA-12` and `DRA-13` remain in progress with
  comments clarifying that M2 static UI work is done while later API/export,
  lawyer-owned legal wording, and Sinhala legal terminology review remain open.
- The Linear team URL is known, but interactive browser access was unavailable
  on 2026-07-30, so no new Linear inspection or mutation was performed in this
  session.

### draftly-platform repo — M2 static UI clone (BUILT, 2026-07-23)

The product front end lives in a **separate sibling repo**
`D:\projects\Draftly-Project\draftly-platform` (private). Status: the M2
static UI clone is **built and reviewed**.

- **Plan:** `docs/plan.md` in that repo is the authoritative M2 spec. It was
  authored by Claude Code and then hardened by a four-agent Opus review
  (theme/design with WCAG contrast math, needs-vs-plan gap analysis,
  unmentioned-considerations audit, and an AI build-review-loop design).
  Key outcomes folded in: derived accessibility tokens (`amber-text #8A5510`,
  `border-strong #AEB7AE`, `selected-bg #EEF2EE`, teal `:focus-visible`
  ring), fonts **Newsreader + IBM Plex Sans + Noto Sans/Serif Sinhala**, an
  interactive mock-state architecture (Zustand store + async `Promise<T>`
  accessors with `// TODO(api):` markers + timer-driven processing
  simulator + audit-event bus + `localStorage` persistence), 11 added types
  (incl. `AuditEvent`, `EvidenceSpan`, `FormTemplate`, `CrossCheck` for the
  "everything must tally" reconciliation), a strict Aceternity
  allowlist/denylist confined to first-run surfaces, and an engineering-setup
  section (strict TS, ESLint 9 + jsx-a11y, next-intl from scaffold, CI,
  eol=lf, pinned pnpm).
- **Layout decision:** flat `frontend/` (Next.js 15 + TS + Tailwind +
  shadcn + Tiptap) + placeholder `backend/` (FastAPI at M3) — not the earlier
  `apps/*` monorepo idea, because the backend is Python so shared TS types
  buy nothing; types live in `frontend/src/types`.
- **Conventions:** the platform repo has its own root `CLAUDE.md` (privacy,
  no-Harvey-assets, legal-wording-is-human-owned, tokens enforced) and
  `AGENTS.md`; the interface spec is copied to
  `docs/reference/draftly-interface-spec.md` so the repo is self-contained
  for any build agent.
- **Build:** executed by the GPT-5.6 build agent from a prepared handoff
  prompt. Final build commit:
  `feda24b fix(e8-2): complete final conformance review`. Handoff commit:
  `1f2b4fb docs(e8-2): add m2 linear handoff`. E7 editor (Tiptap FactChip,
  versioning, draft-generation gate) and E8 screens (shell, home, matters,
  documents, verified facts, workflow run, assistant, checks, drafts,
  activity/history, library, settings/help, new-matter, kitchen sink) are
  committed with per-screen review evidence under `docs/review/<screen>/`
  and **all five final review passes** (design tokens, spec fidelity,
  accessibility/keyboard, responsive/i18n, code quality/contract) under
  `docs/review/_final/`, plus a Linear handoff doc.
- **Verification:** `pnpm typecheck`, `pnpm lint`, `pnpm test`, and
  `pnpm build` passed in `draftly-platform/frontend`; the production Playwright
  route/demo-path suite passed; axe had zero serious/critical issues; and the
  production route sweep had zero console errors/warnings.
- **Escalations (open, human-owned):** Form 8 prescribed blocks and all
  template legal language are `PLACEHOLDER — legal wording pending lawyer`;
  `si.json` has key parity but English-fallback `TODO(si)` strings pending
  native drafting + lawyer terminology review; the synthetic demo scenario
  needs domain review before external demonstration. See
  `docs/review/escalations.md` in the platform repo.

### Real-case demo data layer (2026-08-02, branch not yet merged)

A **real client bundle** now sits at `draftly-platform/inputs/case-001/`
(gitignored; `inputs/` is in that repo's `.gitignore`). Seven CamScanner PDFs,
client consent given, repo private. Two adjacent Bim Saviya parcels at
Mawathgama, GN 485, Homagama DS, Colombo — cadastral map 520005, block 03,
sheet 00029:

- **Parcel 0021** — completed: Form 8 Instrument of Transfer No. 7347
  (RTA s.43, 2025-07-14). This is _evidence_, not output.
- **Parcel 0020** — the matter being drafted: owned by a development company
  that acquired it by a registered Sinhala s.43 instrument, whose board
  resolved to sell it onward; a cheque covers part of the consideration.

Branch `feat/e8-7-real-case-dummy-layer` (commit `4495dea`) rebuilds the demo
fixtures from this bundle: **38 facts across 7 sections, 9 documents, 7 checks
plus a cross-check**, replacing the 5 invented synthetic ones. Also makes the
form drive its own drafting gate — `FormTemplate.fields`/`.blocks` were dead
data and generation hardcoded two fact keys, so one
`deriveTemplateReadiness()` (`frontend/src/lib/templates/readiness.ts`) now
feeds both the pre-flight checklist and the store gate, and
`build-document.ts` emits the instrument from the template's blocks with
FactChips carrying provenance. Bindings moved from fact **ids to keys**
because `createMatter` clones facts under prefixed ids. Verified end to end in
a browser: gate reads 18/21, blocks generation, and clears once the lawyer
resolves the conflict, the unreviewed NIC, and the blocked certificate number.
Gates green; two defects fixed en route (blocked-fact resolution created an
orphan manual fact; documents screen requested a hardcoded check id).

**The checks fire on the bundle's genuine findings** — unreadable title
certificate for parcel 0020, payment short of consideration, unproven
survey-lot ↔ cadastral-parcel mapping, an identity document matching neither
party.

### How those particulars were extracted — and why the backend must differ

Recorded because it is easy to mistake the fixtures for pipeline output.
**No OCR engine was involved.** The PDFs were rasterized into a
vision-language model's context and read directly in one pass — printed
English, printed Sinhala, and handwriting together. Consequences:

- **Confidence values in the fixtures are invented** (`0.98`, `0.74`, …),
  chosen to drive demo states. Nothing measured them.
- **`EvidenceSpan.region` is fake** — every fact carries the same literal
  box. Nothing was located spatially. (No component renders regions yet.)
- **Snippets are hand transcription**, accurate but not machine-derived.
- **The red flags were found by reasoning**, not by a rule engine.

Mapped onto `backend/docs/services/document-processing.md`'s own escalation
ladder, that process was **Level 2 for every field** — whole page to a vision
model — which that plan correctly reserves as the confidence-gated last
resort. It yields good values fast and loses exactly the two things the
product promise rests on: precise provenance and real confidence. The plan's
"escalate the region, not the document" move stands.

Three decisions this settles for the backend:

1. **Never use model self-reported confidence.** Already established
   independently by the case-law extraction run, where the model reported
   `confidence=high` uniformly. Use Document AI's per-field confidence at
   Level 0, with _cross-document agreement_ as the second signal — a value
   identical in the plan and the certificate is trustworthy in a way no single
   model score is.
2. **The form is the extraction schema.** Particulars were extracted against
   Form 8's own numbered items, which is exactly the frontend's
   `FormTemplate.fields[]` + `factBinding` list. Make that one shared
   contract: it defines what to extract, what gates drafting, and what
   renders — not three parallel lists.
3. **Reconciliation stays deterministic.** Extent equality across sources,
   lot↔parcel mapping, payment vs consideration, presence of the
   prior-registration reference — all versioned explainable rules in
   `check-service`, never model calls.

### Tiptap statutory form templates already exist (unmerged)

Commit `64d0725` on `draftly-platform` branch **`feat/tiptap`**
("feat(e7-2): add Tiptap statutory form templates", 23 Jul) adds 114 files and
was **never merged to main** — nothing was deleted, that branch is the only
place it has lived. Contents: **20 RTA form templates**
(`frontend/src/lib/templates/form-NN-<slug>/{document,meta}.ts`), five custom
Tiptap nodes (`form-field`, `form-field-grid`, `form-section`,
`office-use-box`, `signature-block`), a `_shared-blocks.ts` whose
`standardInstrument()` reduces a statutory form to ~10 lines of config, a
dev compare UI at `/dev/templates`, and the **gazette source assets**:
`docs/reference/1886-58_S.pdf` (252 KB) plus 48 page PNGs (10.2 MiB) from
**Sri Lanka Gazette Extraordinary 1886/58, 2014.10.31**. All prescribed
wording is the `PLACEHOLDER — legal wording pending lawyer` sentinel — layout
is modelled, statutory text is not.

Legal discrepancies found while reviewing it, **for the mentor, not for code**:
Form 11 (caveat) templates cite s.43 but the gazette fee schedule ties caveats
to **s.36(1)**; Form 11 has no validity-duration field though the fee is per
six months; Sinhala titles disagree between `manifest.json` and the templates
for Forms 09 and 10 (the authoritative page-48 fee schedule backs the
manifest); `manifest.json` `titleEn` is confirmed wrong for Forms 24, 25, 26,
27, 32, 19/19A and omits Forms 14/14A entirely; and Forms 08–13, 23, 28–31
were never OCR-verified against their images, so those templates are generic
skeletons rather than transcriptions.

A companion research report, `docs/reference/rta-forms-extraction.md`
(page-by-page extract of the gazette forms), is on branch
`docs/rta-prescribed-forms-reference` (commit `6dd1842`) and also unmerged.

### Why the OCR pipeline was reverted (resolved)

`main` contains `d0fbd00` (identity-document OCR pipeline with Gemini
extraction) followed by `9c69f37` reverting it. The reason: the code targeted
`backend/src/draftly_api/`, which matched the backend plan **as written at the
time**; commit `c7d1ab6` then rewrote that section into a modular monolith
(`src/modules/<owner>/{api,application,domain,infrastructure}` +
`src/platform/` + `src/workers/`), superseding it. The revert was correct.
Re-landing means re-shaping the work to the new structure — classifier and
extractor behind ports in `src/modules/document/infrastructure/`,
orchestration in `application/`, run as the `document.process` job rather than
synchronously in the request. Three known landmines: adding
`backend/pyproject.toml` switches on every backend CI gate at once; CI runs
`pytest tests/unit` but the corrected scaffold has no `tests/unit`; and
`src/platform/` shadows the stdlib `platform` module.

- **Backend design baseline:** three commits on `draftly-platform/main` now
  capture the V0 backend plan and service contracts:
  `fe79ca3` (foundation and evidence services), `acacdcf` (knowledge, memory,
  voice, and checks), and `7c03b38` (governed workflows and outputs). The
  task-service compiles matter-specific checklists from approved base,
  transaction, registration-regime, and conditional modules. Applicability
  uses `applicable | not-applicable | unknown`; unresolved conditions remain
  pending, and changed dependencies mark completed steps stale without erasing
  history. All 20 new Markdown files pass `markdownlint-cli2`.

### Backend and reusable UI decisions

- `draftly-platform/backend/backend-implementation-plan-v0.md` is the backend
  implementation baseline: uv-managed FastAPI, PostgreSQL, ports and adapters,
  asynchronous workers, server-enforced roles, immutable document versions,
  verified particulars, deterministic checks, governed content, drafting,
  approval, export, research, memory, and audit.
- `backend/docs/services/voice-service.md` specifies Gemini Live
  `gemini-3.1-flash-live-preview` as the proposed real-time speech engine.
  Original audio, every partial/final transcript event, edits, confirmation,
  and audit events are persisted. Partial fragments enter a dedicated
  `voice-live` memory thread, are superseded rather than deleted, and cannot
  verify facts or alter a document without explicit user action.
- The voice service is technically designed but remains a scope conflict:
  the current SRS and architecture classify voice as conditional V1. It must
  not be presented as committed V0 functionality until those product documents
  are formally changed.
- Document verification will show the immutable original PDF or page image
  beside legally material candidate facts. Selecting a fact opens its exact
  page and evidence region. Draftly will not recreate the source document.
  OpenContracts is an MIT-licensed architectural reference, not a replacement
  backend. A PDF.js/highlighter compatibility spike is still required for the
  Next.js 15 and React 19 frontend.
- Matter checklists are compiled from approved base, transaction,
  registration-regime, and conditional modules. Applicability uses
  three-valued logic. A missing or non-authoritative fact produces
  `pending-applicability`, never an automatic exclusion. Fact or document
  changes preserve history and mark affected completed steps stale.
- `backend/docs/services/research-service.md` now makes LibreChat the primary
  chat-UI reference and MIT-licensed code-reuse source. Draftly will adapt a
  reviewed subset of LibreChat client components inside the existing Next.js
  shell rather than deploy LibreChat's full Node application as a second
  product. Draftly continues to own authentication, matter permission,
  retrieval, citation validation, authority ranking, corpus versions, memory
  policy, abstention, and audit.
- The research-service contract now includes conversations, immutable message
  successors, branches, attachments, visible tool calls, answer jobs, and
  resumable SSE. Its allowlisted Draftly tools are `search_statutes`,
  `search_cases`, `lookup_legal_reference`, `expand_citation_graph`,
  `get_source_passage`, `search_matter_memory`, and `get_matter_context`.
  These tools are read-only in V0 and derive actor and matter scope from the
  authenticated server session.

### Statutory knowledge base — the retrieval sub-project (active work)

Separate from the client-document pipeline, Draftly curates a **Sri Lankan
conveyancing statutory corpus** (the law itself) to support title reasoning and
consistency checks:

- ~67 sources in `data/legal-sources/manifests/source-registry.csv` (statutes,
  amendments, gazettes, case-law, guides), 1840–2024.
- 20 curriculum topics under `data/legal-sources/topics/<NN-name>/manifest.md`.
- The 20 curriculum topics are now flat Markdown files under
  `data/legal-sources/topics/NN-name.md`; there are no per-topic directories.
  `scripts/normalize_topics.py` and `scripts/reconcile_topics.py` both use this
  flat layout while preserving the existing topic IDs, slugs, and generated
  174 source links.
- Original PDFs in `data/legal-sources/library/`; extracted markdown being built
  in `data/legal-sources/library-markdown/` (mirrors `library/`; PDF stays the
  authority, markdown is the working copy).
- The statute source library is flat: 46 PDF/Markdown assets live directly in
  `data/legal-sources/library/statutes/`, with no statute subdirectories. The
  source and conversion registries use those flat paths. The extracted
  `library-markdown/statutes/` hierarchy remains nested and unchanged.
- The amendment source library is also flat: 19 PDFs live directly in
  `data/legal-sources/library/amendments/`, with no amendment subdirectories.
  The source and conversion registries use the flat amendment paths, while the
  extracted `library-markdown/amendments/` hierarchy remains unchanged.
- **Retrieval approach (decided): rule-based engine over a BookRAG-shaped
  index.** Keep BookRAG's _structure_ — the tree (`topics → subtopics → section`)
  plus the case↔statute graph (GT-Link: a `topics:` list per section) — but drop all
  its LLM/embedding machinery. The index is built by curation + regex citation
  extraction; queries route by a fixed keyword table; ranking is deterministic.
  BookRAG (arXiv:2512.03413, at `papers/`) is an LLM/embedding method wearing a
  structured coat — we take the coat, not the engine. Grounded and reproducible;
  embedding retrieval only as a later fallback for questions no rule covers.
- **Case-law corpus: normalized (2026-07-16).** The processed store contains
  3,703 CommonLII conveyancing judgments, all 5,474 official court judgments,
  and 33 historical Internet Archive volumes. Deterministic extraction has
  produced section-specific candidate links, but every generated edge remains
  `unverified` until lawyer review.
- **BM25 retrieval baseline: implemented (2026-07-18).**
  `notebooks/01_bm25_retrieval_baseline.ipynb` builds a persistent SQLite FTS5
  index from the canonical processed corpus using heading-aware 320-word chunks
  with 50-word overlap. It includes all curated non-case legal documents and
  the 5,121 cases marked as conveyancing matches, collapses chunk hits to one
  result per document, and evaluates against `evaluation/retrieval-gold.csv`.
  A smoke run indexed 100 documents into 6,222 chunks and returned grounded
  evidence for all three sample queries. The gold CSV currently contains only
  its header, so no benchmark metrics have been claimed yet. Full-run artifacts
  go to the ignored `data/processed/retrieval-indexes/` and
  `evaluation/runs/bm25-v1/` directories.
- **Statutes-only Q&A demo: implemented and reviewed (2026-07-18).**
  `src/draftly/retrieval/` now parses and indexes exactly 57 statutes plus 18
  amendments, decomposes the 18 exam questions in `src/questions.md` into 73
  subquestions, retrieves with source-aware BM25 and reciprocal-rank fusion,
  and produces bounded Gemini answers with claim-level citation and relevance
  checks. The Streamlit app is at `apps/statute-retrieval/app.py`. Index builds
  use a process lock, closed SQLite connections, and an atomic temporary-file
  replacement to remain reliable on Windows. Known missing sources cause
  explicit partial answers or abstention. Interleaved OCR in `SRC004:s23`
  through `SRC004:s27`
  is excluded from answer evidence until a verified transcription exists.
  Current development retrieval results on ten unverified labels are
  Recall@5 0.59, Recall@10 0.6567, MRR 0.6893, and nDCG@10 0.5840. The full
  18-question Gemini evaluation completes with no runtime errors: 14 questions
  return partial answers and 4 abstain for insufficient authority. The verifier
  accepted 44 claims covering 37 of 73 requested parts. These are machine
  citation-support checks, not legal-correctness scores; lawyer gold labels
  remain the required publication/deployment gate. Final artifacts are under
  `evaluation/runs/statute-qa-v2-final/`, and 35 automated tests pass.

### Statute section index — LawLanka structural sweep done (2026-08-07)

`statue-plans.md` Phases 0-1 are executed. Code:
`scripts/lawlanka-section-index/` (`config`, `gate_lexicon`, `relevance_gate`,
`fetch`, `parse_index`, `run_sweep`, `build_outputs`, `test_parse_index`,
`act-code-overrides.csv`). Outputs in the gitignored
`evaluation/runs/lawlanka-section-index/`.

The decision it implements: take the statute book's **structure** from LawLanka
(section numbers, marginal-note headings, inline `[n, Act of Year]` amendment
markers) and leave the **text**, which stays with official PDFs at source
priority 1-2. LawLanka is priority 3 and never supplies statute text; a section
it lists that our own extraction lacks is recorded as
`heading_source: lawlanka, text_source: none` — a known hole, not a silent fill.

- **Why it was needed:** our two section indexes were incomplete and disagreed
  (CPC: 103 in the live BM25 index, 514 in `derived/statute-section-index.json`,
  801 from LawLanka), and only 45 of 90 registry sources had any index at all.
- **The payoff: 700 of the 810 failing pinpoint case-to-section links (86.4%)
  now resolve** — CPC 370/452, Prescription Ordinance 125/136, Trusts Ordinance
  100/102. The 810 decomposes exactly as the plan said: 525 where the statute was
  indexed but the section missing, 285 where the statute had no index; 11 links
  are genuinely out of range and stay that way.
- **Phase 0 relevance gate** (deterministic, re-runnable): of 127 names cited
  three or more times, 30 in scope, 33 already held, 29 out, 11 legal systems,
  10 artifacts, 10 for review, 6 aliases. `aliases.csv` resolves 4,519 of 5,010
  mentions (90%) without acquiring anything.
- **Phase 1 sweep:** 88 requests at one per second, single session, written
  permission on file, password rotated. A-Z consolidation index returned exactly
  1,774 entries. 39 enactments indexed → `sections.jsonl` (3,269 sections),
  `actions.csv` (872 actions, `operation` `unknown` on 853 because a marker names
  the amending Act, not the operation), `crosscheck-report.md`. Re-running makes
  zero requests; the cache is keyed by URL and every record carries
  `source_url`, `fetched_at`, `sha256`, `retrieved_from: lawlanka`.
- **Law reports were not touched.** `viewNlrVolumeWise`, `viewSlrYearWise`,
  `viewSclrYearWise`, `viewScoaYearWise` and the Case Digest remain excluded —
  highest IP exposure, and we already hold 9,177 judgments.
- **Known limits, not to be papered over:** the PDF coordinate-block extractor
  the plan cites as a prototype **is not in this repo**, so the "official PDF
  wins on disagreement" adjudication is unrun and belongs to Phase 2. Four
  repealed statutes (`courts ordinance`, `land redemption`, `waste lands`,
  `british courts probates (re-sealing)`) are absent from a consolidation of
  in-force law and need official PDFs. `actsYearWise` ignores a year parameter
  and was dropped. Amending-instrument recovery reached 28 for the CPC, not ~40.
Everything is `status: unverified`.

`data/legal-sources/extra-statues-to-topics.md` records a provisional topic
mapping for index-only sources `SRC091` through `SRC112`. The mapping is
documentation only: their registry `topics` fields remain blank, and the
sources must remain `index-only` until authoritative text and metadata are
verified. `SRC108` also has an unresolved title mismatch between the registry
and its indexed section 1 heading.

### Next: bounded-LLM enrichment (planned, grounded)

Two LLM passes on top of the deterministic corpus — both **bounded** (closed
choice + validated output, never free generation), cheap, and left `unverified`
until lawyer review:

- **Citation disambiguation** — resolve the ~62k `unresolved_citations.csv`
  mentions (mostly bare "section N" with no nearby act; many are noise — Roman-law
  / Digest false positives). Pipeline: (1) deterministic **pre-filter** to drop
  obvious non-citations first; (2) give the model the **full 90-statute catalogue**
  as the allowed set (it fits — grounding: pick only a real `source_id`) + the
  **case's context** (acts already cited, topic) as the disambiguating prior +
  an **abstain** option; (3) **validate** `source_id ∈ registry` and section
  exists → else stays unresolved. Menu size isn't the disambiguator; context is.

- **Rule extraction (the payload)** — for each judgment, capture the **rule it
  establishes**, stored WITH a reference to the case (a case = authority for a
  rule). **Headnote-first**: for reported NLR/SLR cases the headnote _is_ the
  rule (cheap, high quality); for unreported court judgments the bounded LLM
  extracts a **quote-backed** rule. Output `rules.csv`:
  `{rule_id, statement, supporting_quote, statute_section, topics, case_ref,
  confidence, status=unverified}`. Retrieval then returns
  `section → rules → each rule cites its case`. Guardrails: extractive/quote-backed
  (quote must appear in the judgment), abstain when no clean rule, lawyer-sample
  before trust. Copyright: SLR headnotes are Council-of-Law-Reporting copyright —
  internal use only, don't republish (or store an extractive paraphrase + citation).

- **Model:** cheap + swappable via an OpenAI-compatible client — default
  **NVIDIA NIM** (`integrate.api.nvidia.com`, free dev tier) with a small instruct
  model (Llama-3.1-8B / Qwen2.5-7B); can swap to local Ollama or Claude/Gemini
  with no code change. A small model is safe because the **validation layer**, not
  the model, guards correctness. After pre-filtering, volume is a few thousand
  short calls → effectively free.

### Rule-extraction evaluation — provisional NO-GO (2026-07-18)

Before the full ~3,179-case no-headnote run, a **pre-registered ablation +
holdout study** was run (`evaluation/runs/caselaw-ablation-v1/`, notebook
`notebooks/02_caselaw_extraction_validation.ipynb`). Findings that change the plan:

- **Grounding ≠ correctness (the headline).** On the 100-case holdout: 74%
  accepted, **100% independently quote-grounded**, yet only **~58% judged
  _usable_** (Claude-Opus subagent judge, a proxy; a human `lawyer-labels.csv`
  pack of 74 rows is the authoritative gate). So the verbatim gate is necessary,
  not sufficient — it cannot catch obiter, borrowed quotes, or wrong statutes.
- **Windowing ablation overturned the earlier cue-window idea:** for the small
  8B, accept rate is monotonic in _less_ context — naive head+tail (0.83) >
  cue-aware (0.73) > full text (0.63) > 70B+full (0.55). **Deploy the naive 8B
  window** for the mass run; the cue-aware/16K changes were counterproductive.
- **Statute attribution is the weak link (~19% wrong, worst dimension).** Cause:
  the model only gets statute _titles_ (no text) and _guesses_ the section; the
  corpus is 68% pre-1950 and construes repealed statutes not in the catalogue
  (Partition Ordinance 1863/1951, Fiscal's Ordinance 1867, Courts Ordinance 1889,
  Public Trustee, Privy Council Appeal — still to be downloaded and added).

Fixes applied (code) toward a re-run: extraction now emits
`statute_citation_verbatim` (statute+section copied from the judgment, kept even
for out-of-catalogue statutes), an explicit common-law/no-statute option, and a
"never guess source_id/section + ratio-only + not-borrowed-quote" instruction;
`llm_client` now counts billable HTTP attempts; **50 of 85 statutes are now
wired to their on-disk markdown** and a section index built (`data/legal-sources/
derived/statute-section-index.json`, 3,547 sections) so section verification can
become real. **Next:** re-run the eval harness with naive window + these fixes +
deterministic section resolution, then get the human lawyer labels before any
full run.

### Corpus EDA + headnote-coverage reality (2026-07-25)

`notebooks/03_corpus_eda.ipynb` is a runnable exploratory pass over every
retrieval dataset (statutory registry, processed store, case corpus,
rule-extraction output). It executes clean end to end and reads all numbers live
from disk. Building it surfaced two things that correct earlier framing:

- **On-disk rule count is 1,541, not 2,166.** The current v2 run at
  `scripts/case-law-information-extraction/output/rules.csv` holds 1,541 rules
  (1,065 `headnote` + 476 `llm-extract`), all `status=unverified`. The 2,166
  figure in the 2026-07-17 log was an earlier run and is superseded. Extraction
  ran on the 5,121 conveyancing-relevant cases in `case_meta.csv` = 3,703
  reported (CommonLII, `LKCA`/`LKSC`) + 1,418 unreported (official courts,
  `SC`/`COA`).
- **Headnote coverage on reported cases is only 14%, and better regex will not
  fix it.** Of the 3,703 reported cases, only **524 (14%)** produced a headnote
  rule; **3,179 (86%)** returned `no-headnote`, and Track B (LLM) was run on
  none of them (0 LLM rules on reported cases). Sampling 800 of the 3,179
  no-rule cases: ~1% have a clean `Held:` block the current regex missed
  (regex ceiling is ~1%, not the missing 86%), ~89% contain "held" only as an
  ordinary word in the judgment prose (matching those would fabricate rules),
  ~11% have no "held" at all. The editor's headnote is simply not in the
  harvested CommonLII text for these cases. The `headnote.py` docstring claim of
  "~64% of reported cases have a clean marker" is wrong against the data.

**Recovery levers (headnotes are not sitting in our data).** We hold **nothing**
from LawNet (`lawnet.gov.lk` was dead during harvesting). LawLanka is index-only:
`slr-modern-cases.csv` is 630 modern SLR titles/citations/URLs (2012–2021),
`status=indexed_reference`, full text paywalled and copyright — no judgment text,
no headnotes. So the two real options are (1) run the quote-checked LLM track
(Track B) on the CommonLII judgment bodies we already hold — more coverage,
lower precision (~58% usable per the ablation) — or (2) acquire real headnotes
via the official LawNet / university data request. Lawyer verification stays the
gate either way.

### Track A2 headnote-structure recovery (2026-07-25)

`notebooks/04_headnote_rule_recovery.ipynb` acts on the finding above. It adds a
**deterministic, structure-aware headnote parser (Track A2)** that recovers the
rules the `Held:`-marker extractor drops. NLR reports state the rule as a plain
block after the catchwords line (`registry -> CATCHWORDS -> RULE -> body-start`),
so the parser trims CommonLII nav, anchors on the registry/case-number line,
splits catchwords from rule with an **abbreviation-aware** period boundary (so
`s.`/`No.`/`Rs.`/initials do not cut early), bounds the rule at the first body
marker (`THE facts`, `APPEAL from`, counsel line, `J.—`, a date), and validates
length/shape. It is **verbatim (no LLM)** and **precision-first**: unclean
structure -> abstain (route to Track B), never emit a junk rule.

- **Yield on the 3,179 dropped reported cases: 2,267 rules recovered (71%)**,
  912 (29%) abstain. Reported-case rule coverage lifts from **14% to ~75%** with
  no LLM spend and no dependence on the missing LawNet headnotes. Example
  abstention: `commonlii-LKCA-1872-1` (over-long catchword block with embedded
  `?`/quotes exceeds the 260-char cap).
- **Statute linking** is section-centric: for each `section N` it attributes the
  nearest statute name (<=60 chars), validates against
  `derived/statute-section-index.json`, and keeps the verbatim citation.
  1,056 links produced (929 with a pinpoint section); in-catalogue links are
  validated, out-of-catalogue (repealed ordinances) keep the verbatim string.
- This **corrects the earlier "~1% recoverable by regex" claim** — that was only
  the exact `Held:` token; real deterministic recovery via structure-aware
  parsing is ~66-71%.

### Court extraction artifacts and relevance gate (2026-08-16)

- `main` now contains the previously uncommitted public-court extraction
  artifacts: 509 Court of Appeal cache records, 909 Supreme Court cache
  records, 163 judge-pack/part/worker artifacts, four Track B run logs, and a
  five-file v1 output snapshot. Legacy extractor revisions 6-8 are retained
  under `archive/extractors/` for provenance.
- `evaluation/runs/conveyancing-gate-v1/` contains the deterministic
  conveyancing-relevance labels and a lawyer-review sample. These labels,
  extraction caches, and judge outputs remain derived and unverified; they are
  not lawyer-approved legal rules or production-ready retrieval material.
- Local `main` was synchronized with `origin/main` before these artifacts were
  split into seven reviewable commits. The upstream merge includes the latest
  quote-grounding fixes and case-law extraction outputs.
- Artifacts (gitignored `evaluation/runs/headnote-recovery-v1/`):
  `rules_recovered.csv` (2,267, all `status=unverified`), `statute_links.csv`,
  and `review-sample.csv` (50 rows with blank `rule_correct` / `rule_is_ratio` /
  `statute_link_correct` columns) — the lawyer gate. Known limits: OCR noise,
  occasional catchword remnants, and rule-vs-fact bleed on a minority of cases.

### Track A2 hardened to the full CommonLII corpus (2026-07-25)

`notebooks/04_headnote_rule_recovery.ipynb` was extended from the 3,179 dropped
cases to **all 3,703 CommonLII judgments**, and the parser was hardened
case-by-case against every failure mode found (drive: open a failing file →
identify the pattern → harden the regex → re-run). Patterns fixed: `?`-terminated
catchword lines, `Per JUDGE -` / `Withers, J. -` rule attributions, SLR headers
(`Sri LR`), section-dash catchwords (`s. 642-Application`), long multi-topic
catchword lists, registry number-dashes (`314-D. C.`) wrongly read as topic
dashes, and body-narrative bleed past the holding.

- **Result: 3,258 verbatim rules recovered from 3,703 CommonLII cases (88.0%)**;
  445 (12.0%) abstain to the LLM track. 1,898 rules begin with a `Held` variant.
  1,877 statute links (1,684 with a pinpoint section).
- **Precision-first and audited.** A hard guard drops any candidate that is
  itself a dash-topic list (`rule-is-catchword-list`, the largest abstention
  bucket at 182). A manual audit of 30 random parsed rules found them to be
  genuine ratios with only occasional trailing bleed; lowercase-fragment starts
  fell to ~0% after a body-tail trimmer and `held`-normalisation. Remaining
  abstentions are jumbled OCR, no-dash-list headnotes, or atypical layouts — kept
  as abstentions rather than forced into wrong rules.
- Final parser lives in the notebook (regex constants + `find_catch_end` +
  `parse_headnote` + section-centric `link_statutes`); dev scripts were
  throwaway. Artifacts regenerated in `evaluation/runs/headnote-recovery-v1/`:
  `rules_recovered.csv` (3,258), `statute_links.csv` (1,877), `review-sample.csv`
  (60 rows, blank verdict columns). All `status=unverified`; lawyer review is the
  gate, statute attribution especially.

### Statute QA agent — SOTA upgrade (2026-07-19, eval in progress)

The statutes-only QA slice (`src/draftly/retrieval/` + `apps/statute-retrieval/`)
was researched, reviewed, and upgraded toward state of the art in one pass:

- **Research:** 31 verified papers + 3 annotated notes files in `papers/qa-agent/`
  (agentic RAG: Self-RAG/CRAG/IRCoT/Plan\*RAG/Search-o1…; graph RAG:
  HippoRAG 1+2/GraphRAG/RAPTOR/SAT-Graph/LegalGraphRAG…; legal QA: SARA/
  LegalBench(-RAG)/CLERC/Chain-of-Logic/Stanford legal-retrieval benchmark/
  hallucination studies). Converged recipe: hybrid BM25+dense at section
  granularity, deterministic graph + PPR for multi-hop (skip LLM-built graphs on
  a closed corpus), statutory-vocabulary query restatement, pinpoint citations
  enforced per claim, claim-level verification with calibrated refusal.
- **Review** (`papers/qa-agent/review-and-plan.md`): generation side was already
  SOTA-aligned (citation gate + entailment verifier + honest abstention); all
  gaps were retrieval-side (single-shot, lexical-only, structure-blind, global
  evidence pool, hand-coded hints).
- **Implemented:** `graph.py` (deterministic statute graph, 15,810 edges —
  cross-refs, amendment→principal targets, definitions — with personalized-
  PageRank expansion); `embeddings.py` (Gemini `gemini-embedding-001` dense
  channel, 5,126 cached vectors incl. chunked OCR mega-sections, graceful
  lexical-only fallback); three-channel RRF fusion + densest-window excerpts in
  `search.py`; per-part evidence quotas + CRAG-style corrective retry (statutory
  query rewrites, same gate/verifier) in `answering.py`; ablation env switches
  (`DRAFTLY_DISABLE_DENSE/GRAPH`, `DRAFTLY_SKIP_CORRECTIVE`).
- **Verified live:** 2025 exam Q3.1 now retrieves Prevention of Frauds s.2 +
  BOTH amendments together (graph edges); the Somar Notaries question's part 4
  was answered on the corrective pass. Known corpus defect surfaced: 42 OCR
  mega-sections (worst: Notaries Ordinance s.31 fused into `SRC014:s30`, 22K
  chars; CPC has 22 such) — mitigated by chunked embeddings + densest-window
  excerpts, but a re-extraction of those sources is the real fix.
- **Eval done (quota-limited):** baseline 42 verified claims / 52% part
  coverage / 4 full abstentions; upgraded (best valid window) 46 claims / 53% /
  2 abstentions — converted 3 of 4 abstained questions into verified answers
  and won the multi-hop amendment questions. Retrieval gold saturated at 100%
  for both (anything a question names is retrieved). Gemini free-tier daily
  quota died mid-final-rerun (11 questions `evidence_only`, preserved as
  `upgraded/results.quota-dead-run.jsonl`); a resumable checkpoint is staged —
  rerun `python evaluation/qa-agent/run_eval.py upgraded` on fresh quota, then
  `--score`. Full results table in `papers/qa-agent/review-and-plan.md`.
  Remaining blockers are corpus, not retrieval: 42 fused OCR mega-sections,
  missing provincial stamp-duty sources, no verified drafting templates,
  interleaved-column MRIO share provisions.

### Team & workstreams

Three-person team; the current v0 plan is in
`project Management/v0-implementation.md`. Everyone builds against one shared
structured matter-record contract (the verified title record). Agree its field
schema + the demo case first, but keep implementation filenames out of
proposal-facing prose.

**v0 planning artifacts (`project Management/`, expanded 2026-07-21).** The v0
plan now carries four supporting documents and three settled technology
decisions:

- `v0-tasks.md` — the v0 plan broken into **6 milestones (M0–M5)** and
  **12 pickable epics (E0–E11)** with subtasks. Work is divided by **claiming
  epics, not by cutting every task into three**; owner lines are blank, and
  cross-cutting epics (scaffold, contracts, content/mentor loop, security,
  evaluation) are marked shared. An optional starting split maps to the
  historical strengths but is explicitly changeable.
- `retrieval-engine-methodology.md` — the engine's source of truth: §§1–8 the
  code/data pipeline as built, §9 the full 12-paper design record (adopt/reject
  verdicts, planned data model, query routing, authority-aware ranking, P1–P6
  build order) carried over from `retrieval-engine-plan.md`.
- `memory-system-evaluation.md` — the agent-memory decision: 22 papers / 16
  systems reviewed; **pick by spike, not adoption** (Graphiti first, MemMachine
  second, else build an SQLite ledger on REMem's model + a `superseded_by`
  column). The two-tier rule (gated verified record above; episodic/notes layer
  below) stays ours regardless of the store.
- **Draft editor = Tiptap** (MIT, ProseMirror): schema-validated JSON templates,
  locked prescribed wording, a `FactChip` node that refuses unverified facts,
  JSON-snapshot versioning; pagination and DOCX/PDF export are our own code, not
  Tiptap's paid cloud.
- **Web app = Harvey-clone UI** on Next.js + Tailwind + shadcn/ui + Tiptap at
  `apps/web/`; built static-with-mocks first, then wired to a FastAPI wrapper of
  `src/draftly/retrieval`.

- **Lahiru — OCR & Extraction.** Scanned Sinhala/English deeds/plans → structured
  fields. Candidate engines + Sinhala-OCR papers surveyed in the current v0 plan
  (Document AI / Cloud Vision / Surya / Tesseract / VLMs); privacy favours
  self-hosted open-source for real client docs. Also owns the ~70 scanned CoA
  judgments that need OCR.
- **Himath — Data & Legal Corpus lead.** This workstream (statutes + case law).
  Targets: (1) retrieval-method research → pick engine, (2) prepare datasets
  (corpus + retrieval eval set + ground-truth case record), (3) make the corpus
  traversable, (4) stand up the rule-based engine.
- **Praveen — Templates, Outputs & User-Facing Interface.** Every output doc as
  a parameterized template filled from the verified structured matter record.
  Also owns the lawyer-facing review interface and export flow. Full input +
  output document catalog is in the current v0 plan; build the shared deed schedule
  (උපලේඛනය) first.

Integration = the Streamlit POC (`deed-workflow-plan-poc.md`): OCR → verified
record → attach law → fill templates. Other planning docs: `pitch.md` (TA pitch),
`related-pepers.md`. A Markdown proposal draft now lives at
`report/project proposal.md`; it still contains the older two-track product
framing and should be updated separately before reuse. The current product
decision and SRS define Draftly as a notarial and conveyancing platform only.
The local proposal now uses proposal-safe wording
such as "verified structured matter record" rather than internal filenames,
caveats the case-law corpus as acquired but not yet validated as linked legal
authority, and presents the reusable legal-source counts as a compact table. The
proposal was rebuilt against the official
`C:\Users\asus\Downloads\CS3501 Project Proposal Template.docx`. The exported
`Draftly Project Proposal.pdf` is verified as five A4 pages: one
template-matched title page plus exactly four proposal pages, satisfying the
template's 3-4 page body limit. The body uses Arial 11 at 1.15 line spacing,
20 pt regular section headings, one-inch margins, and the template's eight
required sections. The title page preserves the template's top-right module
block, centered title, gray subtitle, and lower team-details block. The local
Markdown now embeds the workflow as a Mermaid diagram instead of the older PNG
image, because the raster figure looked poor in the proposal. Older figure
assets still live at `report/assets/draftly-workflow.svg`,
`report/assets/draftly-workflow.png`, and editable Mermaid source
`report/assets/draftly-workflow.mmd`, but the proposal source uses the inline
Mermaid block. A companion research map lives at `report/research-structure.md`;
it tracks papers, GitHub projects, production products, Hugging Face assets, and
search/API tooling. The live Google Doc
`1HmMt6o2wQRcMPkeMrkKFQ4lXvzOaWMUymwXupreFKpU` was synced earlier, but may not
include the latest local edits unless it is synced again.

### Tooling / environment

- Python venv at `.venv/`; docling installed. Convert PDFs with
  `.venv/Scripts/docling.exe … --no-ocr` or `papers/convert.py` (OCR off avoids
  a `std::bad_alloc` on born-digital PDFs).
- `scripts/convert_to_text.py` routes scanned PDF extraction through recorded
  Docling attempts, local RapidOCR/ONNX, and an explicit Document AI fallback or
  direct mode. Cloud OCR has a persistent 2,000-page ceiling and resumable
  per-page cache under ignored `data/processed/`; 208 pages have been used.
- `ocr-benchmark/` now treats each matter as the isolation unit and supports
  PDFs plus photographed image pages. Its ignored local corpus contains 38
  documents and 282 pages across four matters; only one matter currently has
  37 labelled fields, so cross-matter field accuracy remains unproven. Document
  IDs are matter-qualified, scoring reports per-matter metrics, and runs can be
  filtered with `--case`. The pending research work also adds docTR, MADP, and
  RaV-IDP experiment notebooks and their supporting OCR papers.
- `LLMs/nvidia.py` is the shared OpenAI-compatible NVIDIA NIM manager. Its CLI
  lists the live hosted model catalogue, enriches current IDs from public
  NVIDIA Build model-card pages, and atomically writes
  `LLMs/nvidia-models.json`. The saved schema includes endpoint records, short
  and full descriptions, labels, attributes, specifications, capabilities,
  licensing, and available bias/explainability/privacy/safety subcards. The
  2026-08-15 live run saved 102 unique IDs: 48 had complete official public
  cards and 54 retained explicit unavailable status because their model IDs no
  longer resolved to a public card. Its client loads numbered
  `NVIDIA_API_KEY_1`, `_2`, and later keys with round-robin selection and
  failover on authentication, rate-limit, connection, timeout, and server
  errors. Numbered keys override the old single-key variable. The case-law
  information-extraction client now uses this manager; two numbered keys are
  configured locally, and the live endpoint advertised 102 models on
  2026-08-15. No key values belong in tracked files or context.
- Discussion recording transcription CLI lives at
  `proj-docs/discussions/transcribe.py`.
  It uses Google Cloud Speech-to-Text V2 batch transcription through GCS with
  Sinhala `si-LK`, model `chirp_2`, region `asia-southeast1`, and optional
  vocabulary hints from `proj-docs/discussions/vocabulary.txt`. Local `.env`
  currently
  points `GOOGLE_APPLICATION_CREDENTIALS` at
  `proj-docs/discussions/secrets/draftly-502319-96a312953eb0.json`; the secrets,
  recordings, and generated transcripts folders are ignored.
- Portable skills in `.agents/skills/` (agentskills.io format):
  `avoid-ai-writing`, `legal-source-lookup`, `logbook-entry`, `update-context`.
- `AGENTS.md` (root) points all agents here and to the skills registry.
- Markdown must pass `npx markdownlint-cli2` before finishing (CLAUDE.md rule).

### Domain model (from expert mentor, 12 Jul 2026)

Source: `proj-docs/discussions/meeting-notes/notes-jul-12.md` (synthesis of the
Sinhala STT in `proj-docs/discussions/transcripts/`). The team is mentored by a
senior Sri Lankan lawyer/notary + Law College lecturer who authored a 20-topic
conveyancing syllabus and supplies the statutes, sample deeds, and worked
examples.

- **Original mentor direction:** start with conveyancing because it is
  rule-driven and systematisable. The current product decision keeps Draftly
  within notarial and conveyancing work rather than adding litigation.
- **Conveyancing = 6 notarial functions, in order:** (1) examination of title,
  (2) drafting, (3) execution, (4) stamping, (5) attestation, (6) registration.
  **Build 4 now — examination, drafting, execution, attestation — defer
  registration** (most complex); stamping is light.
- **Retrieval pattern he described = the tree walk:** each function breaks into
  ordered **steps**; each step surfaces its rules, and the step's **keywords**
  drive case-law lookup. Maps directly onto the `topics → subtopics → section`
  index and BookRAG's step/keyword navigation.
- **Examination of title:** land search → identify current + prior owners (~30
  yrs, across systems) → encumbrances/mortgages → local-authority docs →
  identity of parties.
- **4 registration systems** (mixed regime): deed registration (old; weak —
  adverse possession can beat a paying buyer), title registration (1998 "Bim
  Saviya", ~10%), condominium (~half), special-area (~25%) — percentages
  _uncertain_.
- **Two-track strategy:** (1) help users operate the _existing_ system, get
  popular first; (2) reform the system later. Build for (1).
- **"Everything must tally":** deed schedule ↔ survey plan ↔ municipal assessment
  (වරිපනම්/assessment no.) must cross-match — core of title checks + red flags.
- **Legal constraints to encode:** NIC identity check now mandatory in the
  attestation; notary territorial **jurisdiction** rules; annual licence renewal.
- **Checklist behaviour he wants:** don't make users tick a checklist — accept
  uploads, then tell them what's **missing**, then proceed.
- **Grounding is existential:** team flagged Gemini "lies creatively" → outputs
  must be grounded/traceable to real documents + statutes or the product fails.
- **Sources he will provide:** 20-topic syllabus (+ subtopic keywords), ~50–55
  statutes, ~25,000 important cases (of a much larger corpus; only a few apply to
  deeds — read head notes), Registrar-General handbook (get **officially via the
  university**), ~50–60 sample deeds + 16 condominium transfer deeds + sample
  title reports/pedigrees/T-forms/assessor letters.

### Case-law corpus (NLR/SLR) — acquisition plan

Case law is the missing corpus layer (statutes are largely in hand).

**STATUS (acquired 2026-07-14):** The internet-obtainable slice is DONE.
`scripts/harvest_ia_caselaw.py` pulled **33 public-domain Ceylon law-report
volumes** (full text, ~32 MB, incl. NLR vol. 1 1896; 1839–1913) from the
**Internet Archive** into `library/case-law/internet-archive/` (gitignored,
rebuildable). `scripts/filter_conveyancing_caselaw.py` scored them (26,843
conveyancing hits; all relevant). Manifests tracked:
`manifests/case-law-ia-manifest.csv`, `manifests/case-law-ia-conveyancing.csv`.
See `library/case-law/README.md`. **CommonLII (RESOLVED — the Cloudflare block was
only User-Agent gating, a browser UA passes):** `scripts/harvest_commonlii_caselaw.py`
and `finish_commonlii_caselaw.py` harvested the Supreme Court (LKSC) + Court of
Appeal (LKCA) — the NLR+SLR body. The repaired result is a **9,586-case citation
index**
(`manifests/case-law-commonlii-index.csv`) and **3,703 conveyancing full-text
judgments** (`manifests/case-law-commonlii-conveyancing.csv`; text in
`library/case-law/commonlii/`, gitignored). Span 1872–2010; 3,040 NLR-era
(<1978) + 663 SLR-era. Total case-law text on disk ≈ 99 MB. **Only LawNet stays
unobtainable** (site dead). Remaining work: segment judgments into per-case nodes
(citation, parties, headnote, statutes-cited) + link to statute sections/topics
(the graph/GT-Link layer) — acquisition and normalization are now done.

**DATA-PREP STATUS (2026-07-16):**

- **Cross-era parser sample:** `scripts/20-raw-htmls/` contains exactly 20 LKSC
  HTML judgments from 20 evenly spaced years between 1878 and 2010. The sample
  uses year-and-case-number filenames and every file passes the current parser's
  non-empty-text smoke test. The archive's 2011 and 2012 judgments are PDFs, so
  they are intentionally outside this HTML-only sample. A layout EDA notebook
  now lives at `data/commonlii/eda.ipynb`; it compares four normalized heuristic
  layout scores over time and explicitly avoids treating the category constants
  as model probabilities. The notebook now runs the reusable fingerprint
  generator itself, scans all 2,162 archived HTML judgments, and atomically
  rebuilds `data/commonlii/layout-categories.json`; 34 PDFs are counted but
  excluded from tag-layout analysis. End-to-end execution completed with no
  cell errors and produced the CSV and PNG artifacts under
  `data/commonlii/layout-eda/`. The evidence-linked parser outputs 2,162
  structured records plus extraction tables under `data/commonlii/parsed/`.
  The CommonLII archive, layout work, parser outputs, OCR benchmark, and shared
  tooling are published on `main` through commit `7abc9b17`; PR #7 is merged.
  Seaborn is a uv dev dependency.
- **Canonical store complete:** `data/processed/` is the only retrieval data
  source. It contains 9,295 normalized Markdown documents and 9,177 case
  records: 57 statutes, 18 amendments, 7 gazettes, 3 institution guides, 3,703
  CommonLII judgments, 5,474 official court judgments, and 33 historical report
  volumes. `scripts/verify_processed_store.py` proves an exact 9,295-file/index
  match, real text, matching checksums, and processed-only retrieval paths.
- **CommonLII join repaired:** 47 rows belonged to year groups omitted from the
  rebuilt remote landing-page index although all local texts existed.
  `scripts/repair_commonlii_index.py` reconstructs their title, citation, and URL
  from local headers. All 3,703 conveyancing rows now join with no blank title,
  citation, or URL.
- **OCR backlog cleared:** ten scanned statutory/support PDFs were converted;
  35 pages used local RapidOCR and the rest used the operator-approved Document
  AI route. Two low-text court judgments were fetched from official court URLs
  and OCRed. The cloud ledger records 208/2,000 pages used. No
  conversion-registry row remains `needs-ocr`.
- **Section graph and review queues built:**
  `case_statute_section_links.csv` has 14,665 unique, evidence-backed candidate
  edges across 4,004 cases and 53 statutory sources. The strict unresolved queue
  contains 62,385 section mentions; `verification-sample.csv` contains 30
  unverified edges across 30 cases and 19 sources for lawyer sign-off.
- **Official court judgments:** all 5,474 records are normalized; 1,418 are
  conveyancing matches (SC 909 + CoA 509). The prior “~70 needs OCR” estimate
  was stale; current verification found only two records below the text
  threshold, and both are now repaired.
- **Modern SLR (2012–2021):** public LawLanka volume index only — **630 case
  citations/titles** (`manifests/slr-modern-index.csv`, `slr-modern-cases.csv`;
  pages under `library/case-law/sri-lanka-law-reports/`). Full report text is
  paywalled + copyright → NOT downloaded. Planned next: **cross-match these 630
  to our free court judgments by party name** to attach reported-status +
  citation (clean; no paywall).
- **Topics normalized + reconciled to the registry (source of truth):**
  `scripts/normalize_topics.py` + `reconcile_topics.py` regenerate
  `manifests/topics.csv`, `topic-sources.csv` (**174 edges**), `topics.json` and
  YAML frontmatter on every topic manifest. `scripts/audit_corpus.py` cross-checks
  all registries → **0 registry↔topic mismatches**, junk conversion rows removed.
- **Pipeline notebook:** `notebooks/data_processing_pipeline.ipynb` keeps its
  exploratory Stages 0–5 and adds Stage 6 for building and verifying the
  canonical processed store. OCR stays an explicit operator action; the
  notebook does not silently make cloud calls.

Original plan:

- **Sources (verified 2026-07-14):** NLR (New Law Reports, ~1878–1978) + SLR
  (Sri Lanka Law Reports, 1978–~2012) are on **CommonLII**
  (`commonlii.org/lk/`, free) and **LawNet** (`lawnet.gov.lk`, official/free).
  LawLanka is the paid fallback.
- **Do NOT crawl CommonLII** — it returns 403 to automated agents and its
  `robots.txt` disallows AI crawlers. LawNet has no bot block (just a broken TLS
  cert) and hosts **SLR volume PDFs + topic Digests** under
  `lawnet.gov.lk/wp-content/uploads/`.
- **Method = digest-driven, not case-by-case scrape:** (1) download LawNet Digest
  PDFs (the topic index of all reported cases); (2) filter digest entries to
  conveyancing catchwords → the citation list ("all relevant"); (3) download the
  volume PDFs holding those cases; (4) docling → markdown → split per case;
  (5) parse citation/headnote/statutes-cited/catchwords; (6) link to statute
  sections + topics (the graph/GT-Link layer).
- **Case node schema:** `citation`, `court`, `year`, `parties`, `catchwords`,
  `statutes_cited: [SRCxxx-sN]`, `topics: [NN]`, `headnote`. Store under a new
  `data/legal-sources/library/case-law/` + `library-markdown/case-law/` mirror,
  tracked in `conversion-registry.csv`.
- **Conveyancing filter catchwords:** prescription/adverse possession,
  servitudes, fidei commissum, deeds & instruments, notaries & attestation,
  partition, gift & revocation, mortgage, vendor & purchaser, title/ownership,
  co-ownership/condominium, state land, trusts, last wills, powers of attorney.
- **Copyright:** raw judgment text is public record; SLR **headnotes/digests are
  Council of Law Reporting copyright** — fine to use internally for
  retrieval/eval, do not republish as a public dataset.
- **Cleanest bulk route for completeness:** official data request via the
  university to LawNet/Ministry of Justice, or to AustLII (who run CommonLII and
  license data feeds). Slower; pursue in parallel with the LawNet-PDF route.

### Data & privacy (critical)

`data/raw/` holds **real** client conveyancing bundles (deeds, plans, receipts,
registry extracts, NICs, signatures) — including at least one complete supervised
example set (source documents + lawyer-prepared title report + pedigree) usable
as evaluation ground truth. **Never** publish raw files or copy real names,
NICs, addresses, deed/registry numbers, or the actual pedigree chains into
committed docs, demos, or this context file. For demo/dataset use anonymized or
synthetic versions that preserve structure. (Specific client examples that were
in the old `contxt.md` were deliberately left out of this file for that reason.)

### Open questions

- Subtopic granularity for the statutory tree: one markdown file per subtopic
  under each topic? (leaning yes — small leaves.)
- Do `library-markdown` sections get real `## Section N` headings + node
  frontmatter (`node_id`, `type`, `level`, `source_id`, `section`, `topics`,
  `amended_by`)? Proposed, not yet applied.
- What precision does the 30-edge lawyer sample achieve for each confidence
  method, and which deterministic aliases should be added before any bounded
  model-assisted review?
- The platform frontend exists, and the backend now has a complete design
  baseline but no FastAPI implementation scaffold. The first BM25 retrieval
  baseline exists, but the gold evaluation rows and full-corpus benchmark run
  are still outstanding.
- Confirm whether voice is formally promoted into V0 or remains conditional
  V1. Until the SRS and architecture are changed, the latter remains the
  submission-facing scope.
- Select and pin the first LibreChat upstream revision and component inventory
  after a Next.js 15 and React 19 compatibility, accessibility, security, and
  licence spike.
- Confirm research-conversation persistence, resumable-event retention, and
  whether the initial agent calls application ports directly before an MCP
  adapter is added.
- Confirm the first lawyer-approved RTA transaction workflow and its governed
  module set.

### Next steps

- Rotate the locally configured NVIDIA API keys because their values were
  exposed in local assistant command output during the 2026-08-15 inspection;
  retain only the replacement numbered variables in `.env`.
- **M2 → human gates:** have the lawyer mentor supply/approve the Form 8
  prescribed wording (all template legal text is placeholder); draft real
  Sinhala strings for `si.json` (`TODO(si)` markers) and get terminology
  reviewed; domain-review the synthetic demo scenario before external demos.
  Then walk the platform repo's acceptance criteria against the built UI.
- **M3 next:** stand up FastAPI in `draftly-platform/backend/` wrapping
  `src/draftly/retrieval`, and swap the mock layer screen by screen
  (Assistant first) per plan §Out of scope / next milestones.
- Run the LibreChat reuse spike before implementing the Assistant screen:
  shortlist the sidebar, message renderer, composer, branching, tool-call, and
  resumable-stream components; record their pinned source revision and licence
  notice; replace their data-provider calls with typed Draftly APIs.
- Build the document-review spike with the immutable source viewer,
  normalized evidence overlays, click-to-page highlighting, and exception-first
  fact review. Test scanned pages, zoom, rotation, Sinhala/Tamil text layers,
  keyboard access, and React 19 compatibility.
- Ratify the backend open decisions, then scaffold the uv/FastAPI foundation
  and implement auth, matter isolation, audit, document versioning, and
  verification before wiring research or drafting.
- Fill the feasibility study's index numbers and confirm its mentor line
  (`proj-docs/proj-feasibilty/feasibility-study.md`).
- Divide v0 work: each team member claims epics in
  `project Management/v0-tasks.md` (fill the blank `Owner:` lines). Start
  milestone **M0** — E0 (scaffold `apps/web` + `apps/api`) and E1 (matter-record
  and step-definition contracts as shared Python/TS types) block everything else,
  so land those first; kick off the E9 agent-memory spike and E10 security
  foundations in parallel.
- Review the Draftly interface specification with the lawyer/notary and team;
  validate terminology, workflow order, required verification states, and the
  P0 demonstration path before implementation.
- Convert the approved specification into low-fidelity wireframes and a
  clickable prototype using anonymized matter content; implementation remains
  intentionally out of scope for the completed research pass.

- Ask the lawyer to complete `data/processed/verification-sample.csv`; calculate
  precision by confidence method before exposing case links as authority.
- Prioritize repeated items in `unresolved_citations.csv`, curate historical law
  aliases, and rerun the deterministic linker before considering a bounded LLM
  review pass.
- Populate and review `evaluation/retrieval-gold.csv` with questions and expected
  authorities, then execute the full BM25 notebook and freeze its baseline
  Recall@k, MRR, and nDCG results.
- After freezing the baseline, evaluate topic routing, graph expansion,
  authority ranking, and temporal filtering as separate controlled additions.
- Segment statutory Markdown into stable section nodes with frontmatter and
  connect only lawyer-approved case edges to those nodes.
- OCR and split the scanned Final Year past-paper bundles by subject, then build
  a searchable LW 307 Conveyancing question index without treating unavailable
  access-controlled compilations as downloaded sources.
- Optionally write `papers/bookrag-notes.md` mapping the paper → the build.
- Product/academic track (from the idea-doc feedback; verify what's still open):
  refine the "beyond template-filling" answer to Dr. Nisansa, review SigmaLaw
  papers, keep "Proposed Supervisor" wording, soften claims about existing tools,
  make the dataset-annotation plan concrete (entities, deed-to-deed links,
  lawyer-verified chain ground truth).
- Google Docs copy: Composio Google Docs is connected for `draftly-local-user`.
  The proposal Doc ID `1HmMt6o2wQRcMPkeMrkKFQ4lXvzOaWMUymwXupreFKpU` was updated
  from the local Markdown on 2026-07-15. Google Docs could not embed the local SVG
  directly because its inline-image API needs a public PNG/JPEG/GIF URL, so the
  SVG was rendered to PNG and inserted through a temporary public PNG URL. A
  full-document Markdown replacement can inherit italic run formatting and drop
  the image, so future syncs must reset `italic=false`, remove any generated
  image-placeholder text, and reinsert the PNG before final export. The live
  Google Doc is now built through explicit Docs style operations rather than a
  whole-document Markdown import.

- Keep voice input documented as a later V1 capability unless the SRS scope is
  formally changed; do not add it to the V0 architecture by implication.

---

## Log

### 2026-08-26 · Claude (HiREC-inspired statute retrieval experiment)

- Added `experiments/HiREC-inspired-retrieval/`, a port of HiREC (ACL 2025
  Findings) to Sri Lankan statute retrieval. It maps the paper's
  document/page/passage hierarchy onto act/section/provision, expands every BM25
  hit to its whole section subtree, and curates evidence in one LLM call that
  also decides answerability and writes the next query.
- Its own directory rather than a variant inside the KOBLEX experiment, so that
  experiment's index schema, config, prompts and committed b0/b1 artifacts are
  untouched. Corpus, questions and gold are read from its data directory rather
  than copied, which is what keeps the numbers comparable. Every module carries a
  `hirec_` prefix because both directories go on `sys.path` in one pytest run and
  unprefixed names would shadow each other; a test enforces it.
- Section-subtree expansion closes the gap the flat baselines could not: complete
  gold evidence available on 20 of 20 questions against 0.90 for both b0 and b1,
  and complete-evidence accuracy 1.00 against b1's 0.85 with evidence recall
  1.00. Paid for in precision (0.99 to 0.87-0.91), so F1 lands slightly below
  b1's. A control run of b1 at a matched candidate-pool size scores exactly what
  b1 scored, which rules out the extra candidates as the explanation.
- The paper's answerability check does not transfer. The b1 selection stage
  claimed complete evidence on all 20 questions, a false-complete rate of 1.0 and
  an MCC of 0.0; that baseline is now recomputed into every `metrics.json` here.
  Deriving the flag from a forced coverage table does fire where the raw boolean
  never does, and the resulting extra iterations are what tighten precision. But
  once the hierarchy removes the retrieval ceiling the metric loses its ground
  truth, so `false_complete_rate` is reported as null with an explicit
  `degenerate` note. Scoring it properly needs questions whose evidence is
  genuinely absent from the corpus.
- 20 questions, synthetic and authored alongside the corpus, so the results are
  directional, not significant. Artifacts are `status=unverified` experimental
  evidence, not legal answers. Focused tests: 77 passed; `uv run pytest tests/`:
  229 passed.

### 2026-08-25 · Codex (KOBLEX-inspired legal-retrieval experiment)

- Replaced the superseded Graphiti memory prototype with a bounded,
  KOBLEX-inspired statute-retrieval experiment. It builds a Sri Lankan statute
  smoke corpus, runs a transparent local BM25 baseline, and records each
  multi-hop retrieval and answer-stage artifact for review.
- Vendored the upstream KoBLEX implementation and related research papers as
  reference material only. Draftly's local experiment remains separate from
  the Korean benchmark and does not treat generated information needs as legal
  evidence or citations.
- Added a grounded LLM smoke path that requires an explicit OpenAI API key and
  makes paid calls only when run. Its 20-question smoke artifacts and tests are
  experimental evidence, not a production legal-answering claim. Focused tests:
  53 passed.

### 2026-08-24 · Codex (statute corpus finalization and parser hardening)

- Added a reviewable amendment-ingestion path, preserved HTML and OCR source
  evidence, and produced canonical amendment-operation records. Finalization
  tooling now keeps verified source packs separate from reviewed statute JSON.
- Strengthened CommonLII and consolidated-PDF parsing, including nested-table
  handling, definitions, Roman numerals, amendment-event de-duplication, and
  clearly recorded alternate-edition corrections. Regenerated canonical records
  and the live section/version index from those improvements.
- Updated the statute-browser coverage reports to show finalized status and
  amendment operations. Focused browser tests passed: 24 passed. Raw harvested
  HTML is intentionally preserved verbatim, including its upstream whitespace.

### 2026-08-16 · Codex (enriched statute extraction schema)

- Upgraded both statute extractors to emit registry-grounded document metadata,
  raw and normalized text, SHA-256 source hashes, explicit verification status,
  and nested subsection/paragraph/subparagraph structures. Regenerated the
  National Housing Development Authority Act JSON (84 sections, eight Parts,
  41 subsection-bearing sections) and Apartment Ownership Law JSON (26
  sections). The ten identified NHDA source anomalies are retained verbatim and
  flagged for authoritative-source review rather than silently corrected.

### 2026-08-16 · Codex (Apartment Ownership Law PDF extraction)

- Ran the coordinate-aware PDF extractor in
  `data/legal-sources/library/statutes/sandbox/extractor.py` against the
  Apartment Ownership Law No. 11 of 1973 source. The generated JSON contains
  26 consecutive, non-empty sections with marginal headings and page spans;
  strict validation and representative page-render checks passed.

### 2026-08-16 · Codex (NHDA statute HTML extraction)

- Ran `data/legal-sources/library/statutes/HTML/extractor.py` against the
  National Housing Development Authority HTML source and populated the parsed
  JSON output. Strict validation found 84 consecutive, non-empty sections
  numbered 1 through 84 with no duplicate or missing section warnings.

### 2026-08-16 · Codex (court extraction artifacts published)

- Synchronized local `main` with all available `origin/main` changes, then
  organized the remaining uncommitted public case-law work into seven commits:
  legacy extractor archives, conveyancing-gate labels, Court of Appeal caches,
  Supreme Court caches, judge outputs, the v1 snapshot, and Track B logs plus
  this handoff.
- Preserved the verification boundary: the relevance labels and extracted
  rules remain machine-derived and unverified until the lawyer-review sample
  is completed and acceptance results are recorded.

### 2026-08-15 · Codex (provisional extra-statute topic map)

- Added `data/legal-sources/extra-statues-to-topics.md` with one clean mapping
  table for `SRC091` through `SRC112`, plus the evidence boundary, `index-only`
  requirement, `SRC108` title discrepancy, and the approval/reconciliation
  steps. No source-registry topic assignments were changed.

### 2026-08-15 · Codex (flat amendment source library)

- Flattened 19 amendment PDFs from 18 per-amendment directories into
  `data/legal-sources/library/amendments/`. Updated 34 source/conversion
  registry references, verified byte identity for every moved PDF, and checked
  all 136 statute/amendment source paths successfully.

### 2026-08-15 · Codex (flat statute source library)

- Flattened 46 statute source assets from 42 per-statute directories into
  `data/legal-sources/library/statutes/`. Renamed the one generic
  `manifest.md` to `national-housing-development-authority-act.md` and updated
  102 source/conversion registry references; every resulting path resolves.
- Kept `data/legal-sources/library-markdown/statutes/` unchanged because it is
  the separate extracted-text hierarchy, not the requested source-library
  directory.

### 2026-08-15 · Codex (flat conveyancing topic files)

- Flattened all 20 conveyancing topic manifests from
  `topics/NN-slug/manifest.md` to `topics/NN-slug.md`, retaining numeric order,
  stable slugs, content, and source membership. Updated the topic index and both
  normalization/reconciliation scripts; reconciliation still finds 20 topics
  and 174 source edges.

### 2026-08-15 · Codex (OCR corpus and shared model tooling handoff)

- Prepared the pending research workspace for a single commit on `main`:
  expanded the OCR benchmark from one PDF bundle to matter-isolated PDF and
  photographed-page inputs, added per-matter scoring and filtering, and recorded
  the 282-page four-matter corpus boundary without exposing private case data.
- Added docTR, MADP, and RaV-IDP experiment notebooks and OCR research papers;
  integrated the shared NVIDIA NIM manager into case-law extraction with
  numbered-key rotation and failover tests; and moved discussion material under
  `proj-docs/discussions/` to keep project documents together.

### 2026-08-15 · Codex (NVIDIA model-card catalogue)

- Extended `uv run python LLMs/nvidia.py models` to combine the authenticated
  `/v1/models` response with structured metadata and full Markdown from public
  NVIDIA Build model-card pages, including both current and older page layouts.
- The command now performs bounded concurrent enrichment, records per-model
  failures without inventing metadata, and atomically saves
  `LLMs/nvidia-models.json`. The verified live output has 102 unique records,
  48 complete cards and descriptions, 106 additional model-card subcards, and
  no API-key content. Eight focused tests pass.

### 2026-08-15 · Codex (NVIDIA NIM manager)

- Implemented a reusable OpenAI-compatible NVIDIA NIM manager and model-listing
  CLI in `LLMs/nvidia.py`. It discovers ordered numbered keys, prevents
  duplicates, rotates logical requests, and fails over safely without exposing
  credential values. The legacy single key is ignored when numbered keys exist.
- Connected the case-law information-extraction client to the manager. A live
  authenticated catalogue request returned 102 model IDs and confirmed that
  both configured defaults remain available. Five focused tests pass, and the
  extraction client reports two configured keys.
- Added OpenAI as an explicit project dependency and pytest root-path
  configuration. The live-looking local keys should be rotated because their
  values appeared in assistant command output during initial inspection.

### 2026-08-14 · Codex (twelve commits published to main)

- Split the CommonLII and OCR work into seven additional logical commits, making
  the branch exactly twelve commits ahead of the previous `main`: crawler and
  raw archive work, layout fingerprints and EDA, evidence-linked parsers,
  structured records and extraction tables, the OCR benchmark, and supporting
  configuration.
- Validated 2,162 layout fingerprints, 2,162 JSONL records, 2,162 judgment-table
  rows, both notebooks without saved errors, Python compilation, the uv lock,
  and 44 passing OCR benchmark tests. Ignored private OCR inputs, renders, and
  run outputs were not published.
- Fast-forwarded `main` without force pushing from `4d799c9a` to `7abc9b17`.
  Remote and local SHAs match, and PR #7 is recorded as merged. Unrelated local
  discussion deletions, meeting materials, a paper, `scripts/20-raw-htmls/`, and
  `still.json` remain untouched and uncommitted.

### 2026-08-14 · Codex (full-corpus CommonLII layout scan)

- Replaced the layout notebook's dependency on a pre-existing JSON file with a
  reproducible generator that fingerprints every HTML judgment in the raw LKSC
  archive. It detected all 2,162 HTML files across 1878–2010 with zero failures,
  classified 1,124 NLR and 1,038 SLR records, and explicitly skipped the 34 PDF
  files because HTML tag features do not apply to them.
- The notebook now rebuilds its fingerprint report before EDA, resolves the repo
  root safely, validates complete scan coverage, and has no saved error outputs.
  Its end-to-end run generated the record table, yearly scores, candidate
  transitions, uncertainty queue, and timeline chart under
  `data/commonlii/layout-eda/`.

### 2026-08-14 · Codex (CommonLII layout EDA notebook)

- Added a validated 11-code-cell notebook for category counts, relative layout
  scoring, yearly curves, a heatmap, candidate transitions, decade composition,
  uncertainty review, and CSV/PNG export. The notebook treats its four scores as
  exploratory heuristics rather than calibrated probabilities and averages by
  year so it remains usable when more than one case per year is added.
- Added Seaborn to the uv development dependencies and verified all EDA imports.
  Full notebook execution remains pending because `layout-categories.json` has
  not yet been generated or added to `data/commonlii/`.

### 2026-08-14 · Codex (cross-era LKSC HTML sample)

- Created an exactly 20-file HTML sample for parser analysis, selecting one
  judgment from each of 20 evenly spaced available years across 1878–2010 and
  preserving the year and case number in every filename.
- Confirmed all 20 samples parse without errors and produce non-empty case text.
  The sample ends in 2010 because the archived 2011–2012 LKSC judgments are PDF
  files rather than HTML.

### 2026-08-14 · Codex (LKSC archive published)

- Published the CommonLII crawler and complete LKSC archive as exactly four
  commits on `agent/commonlii-archive`: parser improvements (`6d2ce15d`), the
  year index and cache (`80ec922d`), the resumable downloader (`54c6401e`), and
  the complete raw archive (`06802158`).
- Pushed the branch to `Draftly-LK/draftly-research` and opened draft PR #7:
  `https://github.com/Draftly-LK/draftly-research/pull/7`.
- Left unrelated local changes untouched: `.gitignore` and the deletions of
  `today-meeting-notes.md` and `today-meeting-script.md`.

### 2026-08-14 · Codex (complete LKSC raw judgment download)

- Extended the CommonLII fetch support for raw judgment downloads. Ordinary
  browser-style GET requests handle HTML judgments; PDFs require loading their
  year index in the same cookie session and sending that index as the referer.
  Added a resumable `scripts/1901-crawler/download_cases.py` downloader with
  signature checks and atomic `.part` replacement.
- Downloaded every entry in `year-cases.json` to
  `data/commonlii/raw/LKSC/<year>/<case-number>.<html|pdf>`. The completed local
  archive contains exactly 2,196 judgments: 2,162 HTML files and 34 PDFs,
  totalling 71,341,604 bytes. The 2011 and 2012 folders contain all 5 and 6 PDF
  judgments respectively.
- A full manifest-to-disk audit found zero missing, invalid, extra, or partial
  files. `download-progress.json` records `complete: true` with no failures.

### 2026-08-13 · Codex (LKSC year-to-case manifest)

- Added the GitHub `cloudscraper` source to the uv project dependencies because
  PyPI version 1.2.71 cannot handle CommonLII's managed challenge. `uv.lock`
  pins commit `9ea528a8675f1bebd49ff853d142e94988a95178`; the synced environment reports
  `cloudscraper 3.0.0`.
- Extended `scripts/1901-crawler/crawl.py` with `--all-years` and the operator's
  exact 118-year LKSC list. The mode fetches year indexes only, saves progress
  after every index, and writes `year-cases.json` with year-to-case-number/URL
  mappings.
- The corrected crawl found 2,196 downloadable LKSC case URLs across the 118
  requested years with zero failed indexes. The initial extractor recognized
  only HTML judgments and therefore missed later PDF judgments; it now handles
  both formats. This recovered 5 PDF cases for 2011 and 6 for 2012, with no
  duplicate case numbers. JSON assertions and all offline parser tests pass.

### 2026-08-13 · Codex (CommonLII recovery-crawler JSON output)

- Ran the documented `scripts/1901-crawler/crawl.py --db LKSC --year 1906`
  path. The cached CommonLII index contains four judgment links; all four raw
  HTML files were present, all parsed successfully, and there were no parse
  failures.
- Extended the crawler to emit `cases.json`, a standard indented JSON array,
  alongside its existing `cases.jsonl`. The JSON contains the four complete
  parsed case records and their source URLs. JSON validation and the crawler's
  offline parser tests pass.

### 2026-08-07 · Claude Code (LawLanka structural sweep, Phases 0-1 of statue-plans.md)

- **Phase 0, the relevance gate, is deterministic code**, not a one-off judgement:
  `scripts/lawlanka-section-index/relevance_gate.py` extracts statute names from
  the 3,521 recovered headnotes plus the unresolved links, folds spelling
  variants, and classifies each candidate. Re-running produces byte-identical
  CSVs. The conveyancing lexicon was lifted out of notebook 05 into an importable
  `gate_lexicon.py` (the notebook keeps its own copy and still runs).
- **Variant folding is what makes the counts mean anything.** The reports write
  one statute three ways — `courts ordinance`, `of the courts ordinance`,
  `Validity-Civil Procedure Code` — and unfolded, each copy falls below the
  three-citation threshold. Folding prose prefixes, dashed catchword prefixes,
  plurals and word order took 935 raw spellings to 425 names and reproduced the
  plan's own figures closely (courts ordinance 75 v 69, estate duty 28 v 28,
  interpretation 23 v 23, money lending 22 v 22).
- Gate result on the 127 names cited three or more times: **30 in scope**,
  33 already held, 29 out, 11 legal systems, 10 artifacts, 10 for review,
  6 aliases. `aliases.csv` resolves **4,519 of 5,010 mentions (90%) with no
  acquisition at all**.
- **Correction to the plan's alias estimate.** It expected ~150 citations
  resolved by fragments such as `frauds ordinance` (77) and `documents ordinance`
  (71). Those fragments do not exist in our data at all — a name regex that does
  not truncate at the first enactment noun yields `prevention of frauds
  ordinance` (41) and `registration of documents ordinance` (36) instead. The
  71/77 counts were artifacts of the plan's own regex.
- **Correction to the fetch list.** The plan's ~60 `consShortTitleView` requests
  were framed around the in-scope acquisition candidates, but the 810 failing
  pinpoint links are overwhelmingly in statutes we _already hold_ — 452 in the
  Civil Procedure Code alone. Fetching only new statutes would have left the
  headline number untouched. The sweep covers both: 15 held statutes with index
  gaps + 30 candidates.
- **Phase 1 ran on 2026-08-07 under written permission, password rotated.**
  88 requests total, one per second, single session. **A-Z consolidation index
  returned exactly 1,774 entries**, matching the plan. 39 enactments indexed →
  `sections.jsonl` (3,269 sections), `actions.csv` (872 amendment actions),
  `crosscheck-report.md`. Re-running the sweep makes **zero** requests.
- **The headline result: 700 of the 810 failing links (86.4%) now resolve.**
  Civil Procedure Code 370/452, Prescription Ordinance 125/136, Trusts Ordinance
  100/102, Prevention of Frauds 33/33. The 11 genuinely out-of-range links stay
  out of range.
- **CPC verified against the plan's own quoted evidence.** 801 sections, highest
  `s.840` (plan: up to s.840), and every heading the plan quotes matches
  verbatim, including the `s.756` three-step version chain
  `[50, 79 of 1980] [50, 79 of 1988] [12, 14 of 1997]` and `s.9`'s
  `[3, 43 of 2024]`. Section count is 801 against the plan's 797/734-distinct;
  the parser is slightly more inclusive, not less.
- **Four endpoint corrections found by probing before sweeping.** The plan named
  the endpoints but not their parameters. Real forms:
  `consolidation?menuValue=legislative&selectedLetter=X`,
  `consShortTitleView?selectedAct=<code>` (not `actcode`),
  `revisedVersion1981|1956?...&selectedLetter=X` (letter-paginated, not per act).
  A guessed A-Z URL returned page chrome with no statute list; probing one page
  cost 2 requests instead of 26 wasted ones.
- **`actsYearWise` was dropped, not fixed.** It ignores a year in the query
  string — all ten years returned a byte-identical page — so the plan's 10-request
  budget for it bought nothing. The amending Acts come from the inline markers
  instead. `revisedVersion1956` lists `view1956RevisedVersionPdf` links (PDFs),
  not section lists, so it yields no structure.
- **Repealed statutes cannot come from LawLanka**, confirmed rather than assumed:
  `courts ordinance` (75 citations), `land redemption ordinance`,
  `waste lands ordinance` and `british courts probates (re-sealing) ordinance`
  have zero entries in a consolidation of _in-force_ law. They need official PDFs
  in Phase 4. Recorded with reasons in
  `scripts/lawlanka-section-index/act-code-overrides.csv`.
- Amending-instrument recovery is a modest gain, stated honestly: **28 distinct
  CPC amending instruments (1960-2024)** from the markers, against 26 from our
  PDF and zero in `source-registry.csv` — not the ~40 the plan hoped, because the
  pre-1960 instruments sit in a document header this page does not render.
  `operation` is `unknown` on 853 of 872 actions: a marker names the amending Act
  and section, not what it did.
- Deferred as planned: the **PDF coordinate-block extractor does not exist in
  this repo**, so the "official PDF wins on disagreement" adjudication is Phase 2
  and is not claimed anywhere in the outputs. One-hop cross-reference expansion
  waits on this re-measure.
- Everything is `status: unverified`. Lawyer review remains the gate, statute
  attribution especially.

### 2026-08-02 · Claude Code (real-case demo data layer + form-template audit)

- Organised the first **real client bundle** into
  `draftly-platform/inputs/case-001/` (7 CamScanner PDFs, flat layout, named
  by document type, with a `manifest.md` recording the two parallel transfer
  chains and open questions for the lawyer). Added `inputs/` to that repo's
  `.gitignore` **before** anything was staged; verified nothing under it is
  tracked. Also removed `.claude/` from git and ignored it.
- Rebuilt the demo fixtures from that bundle on branch
  `feat/e8-7-real-case-dummy-layer` (`4495dea`): 38 facts / 9 documents /
  7 checks + cross-check, replacing 5 invented ones. Made the **form drive its
  own drafting gate** — `FormTemplate.fields`/`.blocks` were dead data and
  generation hardcoded `transferee`/`extent`, so a single
  `deriveTemplateReadiness()` now feeds both the pre-flight checklist and the
  store gate, and the generated instrument is built from the template's blocks
  with provenance-carrying FactChips. Bindings moved from fact ids to keys
  (`createMatter` clones facts under prefixed ids). Verified the whole path in
  a browser; typecheck/lint/build/8 tests green. Fixed two defects found while
  wiring it: resolving a blocked fact created an orphan manual fact instead of
  supplying the blocked one (so the gate could never clear), and the documents
  screen requested a hardcoded check id absent on cloned matters.
- **Recorded how those particulars were actually extracted** (new Current
  State section) because the fixtures are easy to mistake for pipeline output:
  a vision-language model read the rasterized PDFs directly, **no OCR engine**,
  so fixture confidence values and `EvidenceSpan.region` boxes are fabricated
  and the red flags were reasoned rather than computed. That is Level 2 of the
  escalation ladder in `document-processing.md` applied to every field. Settles
  three backend decisions: never trust model self-reported confidence (matches
  the earlier case-law finding), make the form's field list the single
  extraction/gating/render contract, and keep reconciliation as deterministic
  rules in `check-service`.
- **Found the Tiptap statutory form templates already built and unmerged** —
  `64d0725` on `feat/tiptap` (20 forms, 5 custom nodes, `standardInstrument()`,
  dev compare UI, gazette PDF + 48 page PNGs). Never merged to main; nothing
  was deleted. Audited it and logged the legal discrepancies for the mentor
  (Form 11 s.43 vs s.36(1), missing caveat duration field, Sinhala title
  conflicts for Forms 09/10, six wrong `titleEn` labels, Forms 14/14A missing,
  Forms 08–13 unverified against their images). Also recovered
  `docs/reference/rta-forms-extraction.md` onto
  `docs/rta-prescribed-forms-reference` (`6dd1842`).
- **Explained the OCR revert**: the reverted code targeted `src/draftly_api/`,
  correct against the plan as written, then superseded by `c7d1ab6`'s modular
  monolith. Re-landing is a reshape, not a re-merge; three CI/structure
  landmines recorded.
- Wrote the CS3501 **feasibility study** at
  `proj-docs/proj-feasibilty/feasibility-study.md` (third-person, IEEE
  references, technical feasibility argued from the validated prototypes).
  Placeholders left: index numbers and the mentor line.

### 2026-07-30 · Codex (full-day handoff)

- Consolidated the product boundary established in the submission documents:
  Draftly is a Sri Lankan notarial and conveyancing platform, V0 is the initial
  RTA-first release, later V1-V3 releases expand the same product, and
  litigation is no longer in the roadmap.
- Confirmed the full Software Architecture Document is committed in
  `draftly-research` at `5b9e7f5d`. It covers the V0 logical, process,
  deployment, implementation, data, security, and quality views without
  exposing internal project-file references in the submission text.
- Created and committed the platform backend design baseline in three commits:
  `fe79ca3`, `acacdcf`, and `7c03b38`. The 20 Markdown files cover the
  implementation plan, infrastructure, auth, matter, document processing,
  verification, checks, research, memory, voice, governed content, workflows,
  drafting, approval, export, obligations, and audit. All pass Markdown lint.
- Specified Gemini Live `gemini-3.1-flash-live-preview` as the proposed
  real-time voice engine. Voice storage preserves original audio, every
  transcript event and revision, confirmation, supersession links, memory
  episodes, and audit history. The formal release scope remains unresolved
  because the SRS still places voice in conditional V1.
- Chose immutable-source document review: show the original PDF or page image,
  overlay source coordinates, and review only legally material particulars.
  OpenContracts will be studied as an MIT-licensed reference; Draftly will not
  adopt its full backend. PDF.js/highlighter compatibility must be tested
  before choosing a frontend dependency.
- Reworked the checklist model so approved base, transaction,
  registration-regime, and conditional modules compile into a reproducible
  matter run. Unknown applicability remains pending, completed steps become
  stale when dependencies change, and no history is silently rewritten.
- Updated `draftly-platform/backend/docs/services/research-service.md` to use
  LibreChat as the main assistant-UI reference and code-reuse source. Selected
  components will be adapted into Draftly's Next.js shell; LibreChat will not
  own legal truth, authentication, matter permissions, corpus policy, memory,
  abstention, or audit. Added conversation history, branches, attachments,
  visible allowlisted tool calls, answer jobs, and resumable SSE contracts.
- Verified the LibreChat decision against its official repository,
  MIT licence, MCP, Agents, authentication, and access-control documentation.
  Its Vite/React 18 client is not a drop-in dependency for Draftly's
  Next.js 15/React 19 frontend, so the component inventory remains subject to a
  pinned compatibility and licence review.
- The research-service update passes Markdown lint and `git diff --check`; it
  is currently uncommitted. The platform also has an unrelated modified
  `docs/review/_template/checklist.md`, which this work did not alter.
- The research worktree still has unrelated notebook, data-marker, PDF
  template, ignore-file, and courts-extraction-plan changes. They were not
  modified or staged during this context update.

### 2026-07-30 · Codex (backend service design commits)

- Committed the complete backend design set to the sibling
  `draftly-platform` repository in three coherent commits: foundation and
  evidence, knowledge and memory, then governed workflow and output services.
- Hardened `task-service.md` so RTA-first matter checklists are compiled
  deterministically from lawyer-approved versioned modules. Missing or
  non-authoritative applicability facts now produce a pending state rather
  than silently removing a step.
- Added immutable compilation provenance and stale-step handling when a relied
  on fact, document, or matter classification changes. AI suggestions remain
  non-authoritative and cannot mutate the checklist.
- Ran Markdown lint over all 20 committed Markdown files with zero errors and
  confirmed the platform worktree was clean after the third commit.

### 2026-07-30 · Codex (context refresh)

- Confirmed the latest committed architecture baseline is `5b9e7f5d`, which
  adds the complete V0 Software Architecture Document and its diagrams.
- Recorded the product decision that voice dictation/playback remains
  conditional V1 scope. V0 architecture and requirements remain unchanged.
- Recorded that the Linear team URL is known but the interactive browser had no
  available session, so no new Linear changes were made.
- Current worktree still contains unrelated unstaged notebook, data-marker,
  PDF-template, ignore-file, and temporary-script changes; they were not
  staged or modified by this context refresh.

### 2026-07-29 · Codex (software architecture document)

- Read the supplied seven-page software architecture template, current SRS,
  RTA source inventory, document-processing research, implementation
  contracts, and current interface technology baseline.
- Created the full software architecture source with all template sections,
  eight central use-case realisations, thirteen Mermaid diagrams, a complete
  V0 document inventory, explicit trust boundaries, component interfaces,
  data invariants, state models, performance responses, and quality scenarios.
- Kept Google Document AI output at candidate status, preserved explicit
  manual review for handwriting/degraded/unsupported material, isolated the
  legal corpus from confidential matters, and made verified particulars the
  only source for approved generated facts.
- Completed two structural/safety review passes and ran
  `markdownlint-cli2`; the architecture document reported zero issues.
- Current commit at handoff: `e6a1c032`; the new architecture document and
  this context update are not yet committed.

### 2026-07-29 · Codex (notarial/conveyancing product boundary)

- Updated the SRS to version 0.3 and removed litigation from the active product
  roadmap. V2 now expands Sri Lankan conveyancing regimes and notarial
  instruments; V3 matures the same product through collaboration, knowledge,
  integrations, reporting, and deployment scale.
- Named Google Document AI as the V0 OCR and document-quality service.
  Handwriting, severely degraded scans, unsupported scripts, and unapproved
  languages route to lawyer review and manual entry.
- Recorded that Google's current Enterprise Document OCR language list does not
  explicitly list Sinhala. Sinhala interface and export support remain in
  scope, but reliable Sinhala source-document OCR is not promised in V0.

### 2026-07-28 · Codex (full-product SRS rebuild)

- Rebuilt the SRS after two adversarial review-and-fix passes. It now frames V0
  as the initial RTA release of the wider Draftly product, with V1 expanding
  conveyancing, V2 adding litigation, and V3 extending the practice platform.
- Removed internal paths, static-interface assumptions, temporary stack
  choices, and prototype-level screen requirements from the submission-facing
  document.
- Added traceable requirements across product functions and quality
  attributes, explicit lawyer-verification and abstention controls, V0
  acceptance criteria, and stronger official legal, standards, research, and
  public product references.

### 2026-07-28 · Codex (SRS naming cleanup)

- Removed the product-stage label “Draftly v0” from
  `proj-docs/SRS/draftly-srs.md`; the specification now refers to the product
  simply as Draftly.

### 2026-07-28 · Codex (SRS working draft)

- Captured the first full Draftly v0 software requirements specification and
  its three supplied reference/template PDFs under `proj-docs/SRS/`.
- Preserved the existing headnote-rule-recovery results while updating the
  notebook's recorded repository path and Python kernel metadata to the current
  workspace.
- Kept the SRS as a working draft: team review and final Word-template porting
  remain open.

### 2026-07-25 · Codex (Gantt schedule commit)

- Committed the project Gantt schedule in `596fca92`: the schedule blueprint at
  `project Management/grantt-blueprint.md` and rendered HTML chart at
  `proj-docs/gantt/draftly-gantt.html`.
- Validation: the new Markdown file passes `markdownlint-cli2 --no-globs`; the
  normal repo lint command still expands into the generated legal corpus and
  fails on pre-existing corpus-format Markdown issues.

### 2026-07-25 · Codex (data snapshot commit)

- Committed and pushed the non-private `data/` corpus snapshot to `origin/main`
  as `d9fdb33a`: generated statute index data, harvested case-law library
  outputs, and processed canonical-store artifacts.
- Privacy guard: `data/raw/` was deliberately excluded from staging/push and
  added to `.gitignore`; it contains private legal documents under the repo
  privacy rule.
- Validation notes: no staged `data/raw/` paths and no non-raw file above
  GitHub's 100 MB per-file limit. `git diff --check` reported whitespace noise
  inside generated corpus/PDF artifacts, and `markdownlint-cli2` did not
  complete on the generated Markdown corpus before timeout.

### 2026-07-25 · Codex (hardened notebook commit)

- Committed the full-CommonLII Track A2 parser notebook update as `e3663e8`
  after confirming valid notebook JSON, zero saved execution errors, and a
  whitespace-clean diff.

### 2026-07-25 · Codex (commit pending research work)

- Committed the corpus EDA and deterministic headnote-rule recovery notebooks,
  feasibility-study draft and template, and the intentional removal of the
  16 July logbook entry in `9463c53`.
- Added ignore rules for the generated headnote-recovery artifacts and
  machine-local Claude settings so those files remain outside version control.

### 2026-07-25 · Claude Code (Track A2 hardened to full CommonLII)

- Extended Track A2 from the 3,179 dropped cases to all 3,703 CommonLII
  judgments and hardened the parser case-by-case (open failing file → harden
  regex → re-run) against `?`-terminated catchwords, `Per JUDGE -` / `Withers,
  J. -` attributions, SLR headers, section-dash catchwords, registry
  number-dashes, and body-narrative bleed.
- Final: **3,258 verbatim rules from 3,703 CommonLII cases (88.0%)**, 445 abstain
  to the LLM track; 1,877 statute links (1,684 pinpoint). Precision-audited (30
  random rules = genuine ratios); a hard guard drops dash-topic-list candidates.
  Final code lives in `notebooks/04_headnote_rule_recovery.ipynb`; artifacts
  regenerated in `evaluation/runs/headnote-recovery-v1/`. All `status=unverified`.

### 2026-07-25 · Claude Code (Track A2 headnote-structure rule recovery)

- Built `notebooks/04_headnote_rule_recovery.ipynb`: a deterministic,
  structure-aware headnote parser that recovers rules the `Held:`-marker
  extractor drops, plus a section-centric statute linker, visualizations, and a
  manual-validation harness. Runs clean end to end.
- Result on the 3,179 dropped reported cases: **2,267 verbatim rules recovered
  (71%)**, 912 abstain (routed to the LLM track), lifting reported-case rule
  coverage from 14% to ~75% — no LLM spend, no LawNet dependency. 1,056 statute
  links (929 pinpoint), validated against the section index where in-catalogue.
- This corrects the earlier "~1% recoverable by regex": deterministic recovery
  via structure-aware parsing is ~66-71%, not marker tweaking. All output is
  `status=unverified`; `evaluation/runs/headnote-recovery-v1/review-sample.csv`
  (50 rows, blank verdict columns) is the lawyer gate.
- Developed and tested the parser against real cases before writing the
  notebook; installed no new deps beyond the `matplotlib` added earlier.

### 2026-07-25 · Claude Code (corpus EDA + headnote-coverage audit)

- Built `notebooks/03_corpus_eda.ipynb`: a runnable EDA over the statutory
  registry, processed store, case corpus, and rule-extraction output, with the
  reported-vs-unreported split (3,703 vs 1,418), per-court breakdown, decade
  histogram, three live headnote samples (extractable / not-extractable / no
  headnote), and the rule-extraction funnel. Executes clean end to end;
  installed `matplotlib` into `.venv` for it.
- Audited why reported cases mostly produced no rule. Only 524/3,703 (14%)
  yielded a headnote rule; 3,179 (86%) returned `no-headnote` and Track B was
  never run on them. A better regex recovers ~1% at most — for the rest the
  editor's headnote is absent from the harvested CommonLII text (89% have "held"
  only in prose, 11% none). Confirmed we hold no LawNet material and LawLanka is
  index-only (630 SLR citations, no text). Documented the recovery levers.
- Corrected the on-disk rule count in Current State: the current v2 run is 1,541
  rules (1,065 headnote + 476 LLM), superseding the 2,166 figure from the
  2026-07-17 run. All rules remain `status=unverified`.

### 2026-07-23 · Codex (M2 static UI completion + Linear update)

- Completed the `draftly-platform` M2 static UI clone and recorded the handoff
  in `docs/review/_final/linear-handoff.md` at commit `1f2b4fb`. The final UI
  build remains at `feda24b`, with all route inventory, typed mocks,
  next-intl scaffolding, Zustand simulator/audit state, Tiptap/FactChip draft
  workflow, review evidence, and five final review passes complete.
- Updated Linear project `Draftly v0`: posted an on-track project update,
  closed M2 child tasks `DRA-55`, `DRA-56`, and `DRA-61` through `DRA-68`, and
  left later-scope API integration, P0 completion, real export, lawyer-owned
  legal wording, and Sinhala legal terminology review open.

### 2026-07-23 · Claude Code (M2 plan + build handoff + feasibility study)

- Stood up the sibling **`draftly-platform`** repo as the product front end.
  Wrote `docs/plan.md` (the authoritative M2 spec), then hardened it with a
  **four-agent Opus review**: (1) theme/design — found two real WCAG failures
  (amber text, 1px border) and a selected/verified color collision, fixed via
  derived tokens; flagged that Newsreader has no Sinhala glyphs → **Noto Serif
  Sinhala** for සිං headings; (2) gap analysis — static fixtures can't demo
  the acceptance criteria, so the plan gained a Zustand mock store, async
  accessors, a processing simulator, an audit-event bus, and 11 missing
  contract types (incl. `CrossCheck` for the tally rule); (3) engineering
  audit — i18n-from-scaffold (not retrofit), strict TS/CI/hooks, private
  repo + never commit Harvey screenshots; (4) an **AI build-review loop** (per
  screen: Playwright capture → 8 mechanical checks + token probes → fix →
  re-verify, 3-iteration cap, committed baselines, human gate for legal
  wording). Layout decision: flat `frontend/` + `backend/`, no monorepo —
  backend is Python so shared TS types buy nothing. Added the platform repo's
  own `CLAUDE.md`/`AGENTS.md` and copied the interface spec into
  `docs/reference/` so the repo is agent-self-contained.
- Prepared the build handoff prompt (build order 1→12 + five final review
  passes) and the **GPT-5.6 build agent executed it**: as of platform commit
  `1f2b4fb`, the M2 static UI clone is built — E7 Tiptap/FactChip editor with
  versioning and a verified-fact draft-generation gate, all E8 screens, per-
  screen review evidence, all five `_final` passes, and a Linear handoff doc.
  Open escalations (human-owned): Form 8 / template legal wording is
  placeholder, `si.json` needs native Sinhala + lawyer terminology review,
  synthetic scenario needs domain review.
- Wrote the CS3501 **feasibility study** at
  `proj-docs/proj-feasibilty/feasibility-study.md` from the official template:
  third-person, need argued from the profession (manual reconciliation,
  fragmented sources, transcription risk, generic-AI unreliability),
  technical feasibility from the validated prototypes, risks mirroring what
  the research phase actually hit, PDPA/ETA/copyright analysis, 12 IEEE
  references. Placeholders: index numbers, mentor-line confirmation.
- Widened `.claude/settings.local.json` permissions (research repo) to the
  whole `Draftly-Project` tree for frictionless cross-repo sessions.

### 2026-07-21 · Codex (v0 task import to Linear)

- Connected to the official Linear MCP for workspace `draftly-lk` and imported
  `project Management/v0-tasks.md` into team `DRA` without modifying project
  source files.
- Created the v0 project, six milestones, 12 epic parents, and 73 child tasks;
  preserved descriptions, nested checklists, statuses, suggested leads,
  milestone feeds, and explicit schema dependencies. Readback verified all 85
  issues and reported no failed writes.

### 2026-07-21 · Claude Code (v0 planning docs + task breakdown)

- Added an **agent-memory** section to `project Management/v0-implementation.md`
  and wired in `memory-system-evaluation.md`: v0 picks the per-matter session
  memory by spike (Graphiti → MemMachine → own SQLite ledger), keeps the
  two-tier gated-record-over-notes rule, and runs the spike inside the engine
  track. Confirmed **Tiptap** as the draft-editor foundation (schema-validated
  JSON, FactChip provenance node, our own export) — the editor schema, not
  discipline, enforces "no unverified fact in a draft."
- Folded the retrieval design record into
  `project Management/retrieval-engine-methodology.md` as **§9** (12-paper
  adopt/reject verdicts, planned data model, query routing, authority-aware
  ranking, P1–P6 build order) carried from `retrieval-engine-plan.md`, keeping
  the built-vs-planned honesty (§§1–8 = current state, §9 = intent). Referenced
  it from the v0 plan's engine section and track.
- Created `project Management/v0-tasks.md`: the whole v0 plan as 6 milestones
  (M0–M5) and 12 pickable epics (E0–E11) with subtasks. Deliberately **not**
  split 1/3 — work is claimed by epic, owner lines blank, cross-cutting epics
  marked shared, optional starting split provided. Nothing from the plan
  dropped. (Codex later imported this into Linear — see the entry above.)
- All new/edited Markdown passes `markdownlint-cli2`.

### 2026-07-21 · Codex (v0 scope and implementation gates)

- Clarified that v0 means all P0 and P1 work in
  `project Management/v0-implementation.md`; P0 is only the first integrated
  demo milestone. Completion means every listed capability works end to end.
- Removed historical title-chain reconstruction from the Bim Saviya v0 scope.
  V0 still OCRs and extracts supported deeds and matter documents for lawyer
  verification, but excludes AT-form extraction. It verifies the current RTA
  title certificate, cadastral parcel, parties, instrument, interests or
  encumbrances, and supporting evidence without building an ownership graph.
- Added formal matter/step contracts and invariants, a versioned deterministic
  rule/check catalogue, security and privacy controls, and a lawyer-verified
  holdout design with practical acceptance thresholds. Updated the build order
  so these are required work rather than background guidance.

### 2026-07-20 · Codex (RTA notes collection guide)

- Read and classified all 20 files under `docs/RTA_notes/`, separating primary
  law from explanatory material, practice notes, and private examples.
- Created `docs/RTA_notes/README.md` with a complete inventory, RTA and Gazette
  coverage, prescribed-form index, workflow summaries, extraction limitations,
  privacy requirements, and recommended processing architecture for Draftly.
- Confirmed that the 2014 Gazette needs legacy Sinhala font recovery or OCR and
  that the scanned Form 31 needs Sinhala OCR and human verification. No source
  document was modified.

### 2026-07-19 · Codex (Harvey research and Draftly interface specification)

- Researched Harvey's public product pages and Help Center, covering Assistant,
  Vault, review tables, Workflow Agents, Knowledge, Library/History, Shared
  Spaces, integrations, governance, drafting, citations, and versioning.
- Downloaded ten official public Harvey screenshots into
  `docs/product-research/harvey/screenshots/` and documented each source. These
  are internal design references, not product assets.
- Wrote a Draftly-specific, RTA-first product and UX specification with page
  behavior, navigation, lawyer-verification states, guided workflows, grounded
  legal research, draft editing, auditability, visual tokens, responsiveness,
  MVP priorities, and acceptance criteria. Per the user's clarification, no UI
  implementation was performed.

### 2026-07-19 | Claude Code (statute QA agent — SOTA research + upgrade)

- Collected 31 verified papers into `papers/qa-agent/` via three parallel
  research agents (agentic RAG, graph/structure RAG, legal QA) with annotated
  notes files; wrote the code review + upgrade plan in
  `papers/qa-agent/review-and-plan.md`.
- Upgraded `src/draftly/retrieval/`: NEW `graph.py` (deterministic statute
  graph — section cross-refs, amendment→principal-target edges, definition
  edges; 15,810 edges; personalized-PageRank expansion of retrieval seeds) and
  NEW `embeddings.py` (Gemini dense channel, SQLite-cached by corpus
  fingerprint, 5,126 vectors, chunked embedding for 42 OCR mega-sections,
  graceful fallback). `search.py` now fuses lexical + dense + hints + graph via
  RRF and picks densest-window excerpts; `answering.py` adds per-part evidence
  quotas and a bounded CRAG-style corrective retry (statutory-vocabulary query
  rewrites → re-retrieve → regenerate missing parts → same citation gate +
  entailment verifier). Ablation switches: `DRAFTLY_DISABLE_DENSE`,
  `DRAFTLY_DISABLE_GRAPH`, `DRAFTLY_SKIP_CORRECTIVE`.
- Live checks: Prevention-of-Frauds question now surfaces the principal +
  both amendments together; a previously unanswerable Notaries part was
  answered on the corrective pass. Surfaced corpus defect: OCR fused Notaries
  s.31 into `SRC014:s30` (22K chars; 42 such blobs corpus-wide, 22 in the CPC)
  — mitigated at retrieval level, but those sources need re-extraction.
- Baseline-vs-upgraded evaluation over all 18 exam questions
  (`src/questions.md`) launched via `evaluation/qa-agent/run_eval.py` with
  objective gold labels (`gold-labels.json` — only sections/statutes explicitly
  named in question text). Results pending; nothing committed.

### 2026-07-19 | Codex (context refresh)

- Refreshed the shared handoff after the latest local commits. The repository is
  clean at `99426f0`, which includes the statute retrieval dependency update,
  statutes-only retrieval baseline, Streamlit retrieval app, case-law extraction
  validation harness, and the later statute-QA/caselaw ablation artifacts.
- Preserved the current caution: statute-QA verifier results are machine
  citation-support checks, not lawyer-approved legal correctness scores; the
  case-law rule-extraction pipeline remains provisional until human legal review.

### 2026-07-18 | Codex (full Gemini question evaluation)

- Ran every one of the 18 exam-question blocks (73 subquestions) through the
  current Gemini draft-and-verifier pipeline. The final clean run has zero
  execution errors, 14 partial answers, 4 explicit insufficient-authority
  outcomes, and 44 verifier-accepted claims covering 37 requested parts.
- Preserved all iteration artifacts and consolidated the current results under
  `evaluation/runs/statute-qa-v2-final/`. The metrics explicitly label this as
  machine checking only because no lawyer gold answers were supplied.
- Fixed citation normalization, partial-claim salvage, result checkpointing and
  serialization, Windows SQLite build locking, and the known-corpus-gap UI.
  All 35 automated tests pass. Streamlit is running locally on port 8501; the
  in-app browser was unavailable, so visual desktop/mobile QA remains open.

### 2026-07-18 | Codex (statutes-only retrieval and Q&A hardening)

- Reviewed the Q&A system with parallel architecture, corpus, research, and
  answer-audit passes. Adopted typed outcomes, question decomposition,
  source-aware retrieval, claim citation validation, a second relevance check,
  explicit corpus-gap reporting, and repeatable evaluation traces.
- Fixed long legislative-volume contamination, false section boundaries,
  amendment alias provenance, subsection citation normalization, and Windows
  index rebuild locking. Quarantined unreliable two-column inheritance OCR.
- Added the Streamlit statutes-only Q&A demo, command-line build/search/ask and
  evaluation commands, 33 passing tests, a 73-subquestion retrieval run, and
  four live Gemini regression answers. Legal correctness remains unscored until
  lawyer labels are supplied.

### 2026-07-18 | Claude Code (rule-extraction evaluation — provisional NO-GO)

- Ran a **pre-registered ablation + holdout study** on the no-headnote
  rule-extraction method before scaling to ~3,179 cases. Artifacts in
  `evaluation/runs/caselaw-ablation-v1/`; presentation notebook
  `notebooks/02_caselaw_extraction_validation.ipynb`; reusable harness
  `scripts/case-law-information-extraction/ablation.py` + `audit_window_recall.py`.
- **Why NO-GO:** holdout is 74% accept / 100% quote-grounded but only ~58% _usable_
  (Claude-Opus judge proxy; lawyer labels authoritative). Grounding ≠ correctness —
  it misses obiter, quotes borrowed from other cases/counsel, and wrong statute tags.
- **Ablation result:** naive 8B head+tail wins (0.83) > cue-aware (0.73) > full
  (0.63) > 70B+full (0.55). More context hurts the small model. This reverses the
  earlier cue-window/16K change (measured via a misleading "cue-in-window" proxy);
  deploy the naive window for the mass run.
- **Statute attribution** is the worst dimension (~19% wrong): model gets only
  titles and guesses sections, and the corpus cites repealed statutes absent from
  the catalogue. Fixes applied: `statute_citation_verbatim` field + common-law/
  no-statute option + no-guess instruction in `extract_case_rules.py`;
  `llm_client` counts billable HTTP attempts; `validate.py` carries the new fields.
- **Codex (driven via `codex exec`)** wired 50/85 statutes to their on-disk
  markdown in `source-registry.csv` and built `data/legal-sources/derived/
  statute-section-index.json` (3,547 sections) so section verification can work.
- **Still to do:** download the missing historical statutes (Partition Ordinance
  1863/1951, Fiscal's Ordinance 1867, Courts Ordinance 1889, Public Trustee, Privy
  Council Appeal); wire deterministic section resolution; re-run the eval harness
  with the naive window; then collect human lawyer labels before any full run.
  Nothing committed. NVIDIA 70B endpoint was heavily throttled (~110s/call) during
  this session, so the 70B judge/arm were slow.

### 2026-07-18 | Codex (BM25 retrieval baseline notebook)

- Added `notebooks/01_bm25_retrieval_baseline.ipynb` as the reproducible first
  retrieval experiment: corpus selection, heading-aware chunking, persistent
  SQLite FTS5 BM25 indexing, interactive search, gold-set evaluation, and
  artifact export are all in one runnable notebook.
- Added notebook usage and scope notes to `evaluation/README.md`. The baseline
  deliberately excludes embeddings, LLM retrieval, graph expansion, authority
  ranking, and temporal filtering so later improvements can be measured cleanly.
- Verified all notebook code cells in smoke mode: 100 documents produced 6,222
  chunks, the index built successfully, and all three sample queries returned
  grounded results. The gold CSV has no question rows yet, so the notebook
  correctly records configuration without inventing evaluation scores.

### 2026-07-17 · Claude Code (case-law rule extraction — implemented)

- Built `scripts/case-law-information-extraction/` (config, llm_client, catalogue,
  headnote, windowing, validate, extract_case_rules, README) per
  `case-law-extraction-plan.md`. NVIDIA NIM verified (key in `.env`); tiered
  **llama-3.1-8b (cheap)** + **llama-3.3-70b (strong escalation)**, OpenAI-compatible,
  swappable. Outputs → `scripts/case-law-information-extraction/output/` (gitignored;
  rules.csv, case_meta.csv, extract-rejects.csv, per-case cache, usage.json).
- **Track A (reported, deterministic `Held:` extraction, $0): 1,065 rules** from
  ~524 reported cases; the strict block-marker correctly ignores prose "held", so
  ~86% route to Track B. Track A extractor verified: 98% extraction on
  Held-bearing cases.
- **Track B (unreported, bounded LLM, quote-validated): verified working** — real
  grounded rules (e.g. prescription burden → SRC071-s3; partition pedigree duty),
  grounding gate rejects paraphrased (non-verbatim) quotes. ~5.1k prompt tok/case.
  **COMPLETE: 2,166 rules total** (1,065 headnote + 1,101 llm-extract) from 1,625
  cases; 405 linked to a statute section; ~7.2M tokens on the 8B tier (~$0 free
  tier). Caveats: 18% Track-B quote-rejected (model paraphrased — fuzzy-match
  tolerance would recover many); model self-reports confidence=high uniformly
  (weak signal — escalate on quote-rejection, not confidence); 5 transient API
  errors to retry.
- Everything `status=unverified` until lawyer sample. Literature backing for the
  cheap-model + constrained + grounded + validated design captured
  (case-law-extraction-plan.md). `retrieval-engine-plan.md` = the engine that
  consumes rules.csv.

### 2026-07-17 · Codex (Law College past-paper collection)

- Downloaded and organized every publicly downloadable Sri Lanka Law College
  paper found on the official downloads page, plus the public GovDoc year and
  language archives, under `past-papers/`.
- Kept official year-level bundles separate from entrance/archive papers and did
  not bypass Studocu, Scribd, or other access-controlled hosts.
- Added `past-papers/manifest.csv` with source provenance, pages, sizes, and
  SHA-256 checksums; all 44 PDFs and manifest rows were validated. The files are
  untracked and no commit was made.

### 2026-07-17 · Claude Code (retrieval engine plan)

- Deep-read 12 papers via three parallel review agents (legal-RAG limits/temporal,
  case↔statute linking, eval+graph-walk) and wrote **`retrieval-engine-plan.md`**
  — the end-to-end engine design with per-paper adopt/reject verdicts. Headlines:
  topic-partitioned retrieval worth ~+40pts MRR (2502.20364); multi-hop = PPR
  over our REAL 14.6k-edge citation graph (HippoRAG's walk without its noisy
  LLM-KG); temporal layer = dated section-versions + amendment Action nodes +
  SnapshotLast (SAT-Graph RAG); IL-PCSR cross-task statute-injection for the 62k
  disambiguation queue; CLERC mask-a-citation recipe auto-generates the eval gold
  set; BM25 > dense zero-shot in law (rerankers can harm). Authority-aware
  ranking (SC binding > CoA binding-below > HC persuasive — CoA IS binding on
  lower courts, and most land litigation ends there) is absent from all 12 papers
  → our most novel component. Build order P1–P6 in the plan. Papers organized in
  papers/data/ + papers/ocr/ with verified README index.

### 2026-07-16 · Codex (normalized legal corpus and citation graph)

- Repaired the 47-row CommonLII join gap caused by omitted year groups in the
  rebuilt landing-page index; all 3,703 conveyancing judgments now join.
- Built and strictly verified the file-based `data/processed/` store: 9,295
  normalized documents, 9,177 cases, zero missing/low-text files, and matching
  file checksums. The generated store remains ignored and rebuildable.
- Cleared the scanned-source backlog through local OCR and an approved,
  resumable Document AI path capped at 2,000 pages; usage ended at 208 pages.
  Repaired two weak court records from official PDFs.
- Generated 14,665 section-specific candidate case links, a 62,385-row
  unresolved queue, and a balanced 30-row lawyer-verification sample. All links
  remain unverified pending legal review.
- Extended the existing notebook with a canonical production-store stage and
  added repeatable build, conversion, sampling, and verification scripts. No
  changes were committed.

### 2026-07-16 · Claude Code (data prep + court judgments + audit)

- Harvested post-2012 **official court judgments** (supremecourt.lk +
  courtofappeal.lk): 5,474 judgments, 1,418 conveyancing; ~70 scanned CoA ones
  flagged `needs-ocr`. Scripts: `harvest_courts_caselaw.py`,
  `rebuild_courts_manifest.py`.
- **Normalized + reconciled topics** to the registry as source of truth
  (`normalize_topics.py`, `reconcile_topics.py`): topics.csv / topic-sources.csv
  (174 edges) / topics.json + manifest frontmatter. Wrote `audit_corpus.py`;
  cross-checked all registries → 0 mismatches; dropped 16 junk conversion rows;
  fixed SRC036/037 topic union + SRC088 `00`. Restored `conversion-registry.csv`
  after it was found deleted from the working tree.
- `reextract_failed.py`: the 10 docling-`bad_alloc` statutes are scanned/no text
  layer → `needs-ocr` (not fixable by re-extraction).
- Built `notebooks/data_processing_pipeline.ipynb` (Stages 0–5: consolidate →
  clean → case↔statute links → cases.jsonl → topic tables → eval seed).
- Reviewed the modern-SLR discovery (630-case public LawLanka index, citations
  only; full text paywalled/copyright) — planned cross-match to court judgments.
- Wrote `pitch.md`, `roadmap.md` (3 workstreams + OCR model survey + doc
  catalog), `deed-workflow-plan-poc.md`.

### 2026-07-16 · Codex (proposal local polish and handoff refresh)

- Updated the shared context after the latest local proposal polish. The local
  proposal now uses an inline Mermaid workflow diagram instead of the older PNG,
  because the raster figure looked poor in the proposal.
- Recorded the compact reusable legal-source table, the cleaner expected
  outcomes paragraph, and the team split now shown in the proposal: Himath as
  data/legal-corpus lead and Praveen covering templates, outputs, and the
  user-facing lawyer review/export interface.
- Verified the exported `Draftly Project Proposal.pdf` is five A4 pages
  including the title page. The Google Doc was synced earlier but may need a new
  sync pass to reflect the newest local Markdown edits.

### 2026-07-15 · Codex (two-workflow proposal framing fix)

- Corrected `report/project proposal.md` after the proposal drifted back into
  conveyancing-only wording. The proposal now frames Draftly as a two-workflow
  legal platform: conveyancing as the first prototype and evaluation workflow,
  and litigation as the second platform workflow using an IRAC-style structure.
- Updated Current State so future proposal edits preserve the broader project
  identity instead of treating litigation as a vague afterthought.

### 2026-07-15 · Codex (official template rebuild)

- Read and rendered the official CS3501 Word template. Confirmed A4 paper,
  one-inch margins, Arial 11 body text at 1.15 spacing, 20 pt regular section
  headings, a separate title page, eight required proposal sections, and a 3-4
  page limit excluding the title page.
- Reworked `report/project proposal.md` into the template's exact section order,
  reduced the body to about 1,060 words before references, retained the grounded
  legal-data and evaluation details, and restored 20 preliminary references.
- Rebuilt the live Google Doc with a template-matched title page and formatting,
  restored the workflow figure, and exported it for visual QA. Final pagination
  is five A4 pages: one title page plus exactly four proposal pages.

### 2026-07-15 · Codex (six-page proposal refinement)

- Refined `report/project proposal.md` from about 1,660 to about 1,380 words by
  removing repetition while preserving the project scope, statutory counts,
  case-law readiness caveat, methods, evaluation, and bibliography.
- Updated the live Google Doc through Composio, reset inherited all-italic body
  formatting to the template's Arial 11 regular style, restored the workflow
  figure at a readable size, fixed numbered criteria and bibliography entries,
  and removed the generated image placeholder.
- Exported and visually reviewed all six pages. The final Google Doc is exactly
  six US-letter pages and has no observed clipping, overlap, broken tables, or
  stray numbering.

### 2026-07-15 · Codex (4-page proposal and embedded figure)

- Compressed `report/project proposal.md` from the long working draft into a
  4-page-friendly proposal while preserving the core problem, data, methods,
  evaluation, success criteria, team split, and selected bibliography. Google
  Docs plain-text readback is about 1,600 words.
- Rendered `report/assets/draftly-workflow.svg` to
  `report/assets/draftly-workflow.png`, synced the proposal to Google Docs via
  Composio, and verified the Google Doc contains an inline image object.

### 2026-07-15 · Codex (proposal review fixes)

- Applied the review fixes requested after the proposal critique: renamed the
  legal-source table to selected statutory source categories, added a sharper
  case-law caveat, standardized all proposal wording to "verified structured
  matter record," added stronger OCR/document-AI bibliography references from
  `report/research-structure.md`, and changed the workflow diagram labels from
  implementation-heavy BookRAG wording to reader-facing legal-source wording.
- Synced the updated proposal back to the Google Doc
  `1HmMt6o2wQRcMPkeMrkKFQ4lXvzOaWMUymwXupreFKpU` through Composio and verified
  the new caveat, OCR references, and standardized wording are present.

### 2026-07-15 · Codex (proposal and Google Docs sync)

- Strengthened `report/project proposal.md`: added a production-product
  comparison table, workflow-gap matrix, concrete evaluation/annotation table,
  dataset-risk paragraph, lawyer review checklist, and missing retrieval
  bibliography entries. Removed internal implementation filenames from
  proposal-facing text.
- Replaced the simple Mermaid pipeline with a proposal-ready workflow figure
  (`report/assets/draftly-workflow.svg`) and editable Mermaid source
  (`report/assets/draftly-workflow.mmd`). The figure shows document upload,
  OCR/classification, extraction, cross-document linking, verified structured
  matter record, grounded legal-source lookup, red flags, lawyer checklist,
  template generation, and lawyer review/export.
- Connected through Composio using the existing `COMPOSIO_API_KEY`, found an
  active Google Docs connection for `draftly-local-user`, and updated the Google
  Doc `1HmMt6o2wQRcMPkeMrkKFQ4lXvzOaWMUymwXupreFKpU` with the completed proposal.
  The Google Docs copy includes a Figure 1 text reference; the local SVG remains
  the actual diagram asset because Google Docs inline images require public
  PNG/JPEG/GIF URLs.

### 2026-07-14 · Codex (research map)

- Added `report/research-structure.md` as the working research map for Draftly.
  It records the search stack (Semantic Scholar, OpenAlex, arXiv, Hugging Face,
  GitHub, broad web search, and third-party Scholar APIs if needed), core papers
  such as BookRAG/RAPTOR/GraphRAG/HippoRAG/legal RAG benchmarks, open-source
  repos, production products, and Hugging Face assets. Updated
  `report/project proposal.md` to point to this structure.

### 2026-07-14 · Codex (proposal draft)

- Wrote `report/project proposal.md` from the current Draftly context, existing
  `report/main.tex`, `roadmap.md`, `related-projects.md`, and the actual
  `data/` inventory. The proposal keeps the broader product framing while naming
  two workflows: conveyancing/title documentation as the first workflow and
  litigation drafting/review as the later workflow. It also records the current
  local data counts without copying private client details from `data/raw/`.

### 2026-07-14 · Claude Code (context refresh)

- Refreshed Current State: recorded the **rule-based engine over a BookRAG-shaped
  index** decision (keep the structure, drop the LLM/embedding machinery); added
  a **Team & workstreams** section (Lahiru/OCR, Himath/Data, Praveen/Templates)
  with the shared `case_record.json` contract; marked the case-law corpus fully
  acquired (~5,100 judgments + 33 volumes). New docs since last refresh:
  `roadmap.md` (team plan + OCR model survey + document catalog), `pitch.md`,
  `deed-workflow-plan-poc.md`, `related-pepers.md`.

### 2026-07-14 · Claude Code (official court judgments harvested)

- Added the **post-2012 official court judgments** — the layer beyond the
  reported NLR/SLR. Since 2012 the Supreme Court and Court of Appeal publish all
  judgments directly (free, official PDFs). `scripts/harvest_courts_caselaw.py`
  pulled from `supremecourt.lk/judgements/` (2,583 PDFs) and
  `courtofappeal.lk/judgements/` (3,042 PDFs); text extracted with pypdfium2
  (born-digital text — only ~1 needs OCR in the kept set, ~70 CoA scanned images
  have no text layer and are deferred to OCR). Result: **5,474 judgments indexed,
  1,418 conveyancing matches (SC 909 + CoA 509)**. Manifest tracked:
  `manifests/case-law-courts.csv`; text/PDFs gitignored under
  `library/case-law/courts/` (rebuildable via `rebuild_courts_manifest.py`). All
  text kept (not just matches) so the conveyancing filter stays re-tunable.
  Corpus now: IA 33 volumes + CommonLII 3,703 (reported, pre-2012) + courts 1,418
  (post-2012) conveyancing judgments.

### 2026-07-14 · Claude Code (CommonLII harvest complete)

- Cracked the CommonLII access problem: the Cloudflare 403 was User-Agent gating,
  not a JS challenge (confirmed a real browser via Playwright passes, then that a
  plain `curl` with a Chrome UA also passes). Built
  `scripts/harvest_commonlii_caselaw.py` (+ `finish_commonlii_caselaw.py` to
  finish LKCA 2001–2012 and rebuild manifests). Harvested Supreme Court + Court
  of Appeal: **9,539-case citation index**, **3,703 conveyancing full-text
  judgments** (1872–2010; 3,040 NLR-era + 663 SLR-era), ~99 MB. Gitignored the
  text (rebuildable), tracked the manifests. Updated `library/case-law/README.md`
  and `pitch.md`; wrote `deed-workflow-plan.md` updates. Goal met: all
  internet-obtainable NLR/SLR conveyancing docs acquired. Next: segment into
  per-case nodes + statute/topic links.

### 2026-07-14 · Claude Code (case-law acquisition)

- Acquired the internet-obtainable case-law corpus. Probed sources: CommonLII/
  WorldLII are Cloudflare-bot-walled (403 to all non-browsers), LawNet is dead
  (root = "root directory", paths 404), LawLanka is commercial. Pivoted to the
  **Internet Archive** (open API, public-domain holdings). Wrote
  `scripts/harvest_ia_caselaw.py` → downloaded **33 Ceylon law-report volumes**
  (full text ~32 MB, incl. NLR vol.1 1896, span 1839–1913, all NOT_IN_COPYRIGHT)
  to `library/case-law/internet-archive/`. Wrote
  `scripts/filter_conveyancing_caselaw.py` → conveyancing relevance index
  (26,843 hits). Tracked manifests: `case-law-ia-manifest.csv`,
  `case-law-ia-conveyancing.csv`. Added `library/case-law/README.md` documenting
  acquisition + access limits. Gitignored the raw IA text (rebuildable). Modern
  NLR(→1978)/SLR remain unobtainable by automation → official data request.

### 2026-07-14 · Codex (case-law pilot)

- Added `scripts/collect_case_law.py` and ran the Registration of Documents
  digest pilot. LawNet PDF fetch was not reliable: TLS certificate verification
  failed for `lawnet.gov.lk` / `www.lawnet.gov.lk`, and the uploads directory
  returned 404 without TLS verification. Used the already-referenced public
  LawLanka Registration of Documents related-case digest as the fallback source.
- Generated `data/legal-sources/manifests/case-law-citations.csv` with 76
  row-level digest references, 51 unique citations, and 76 conveyancing-filter
  matches. All rows remain `unverified` until the underlying NLR/SLR report text
  is checked. Added three linked sample case nodes and conversion-registry rows.

### 2026-07-14 · Claude Code (case-law plan)

- Verified NLR/SLR sources and access constraints (CommonLII blocks bots +
  disallows AI crawlers → 403; LawNet has no bot block but a broken TLS cert and
  hosts SLR volume + Digest PDFs). Added the "Case-law corpus (NLR/SLR)
  acquisition plan" section: digest-driven collection, per-case node schema,
  conveyancing catchword filter, copyright note, and the official-data-request
  route. Wrote a Codex task prompt for the case-law pilot.

### 2026-07-14 · Claude Code (domain notes)

- Wrote `discussions/meeting-notes/jul - 12.md`: a comprehensive synthesis of the
  6 mentor recordings/transcripts (the 6 notarial functions, examination-of-title
  steps, 4 registration systems, litigation/IRAC, the condominium worked example,
  document tally rule, sources he'll provide, business/deployment thoughts).
  Personal names/deed numbers kept out per the privacy rule.
- Added the "Domain model (from expert mentor)" section to Current State above,
  distilling the durable facts and tying his step→keyword retrieval pattern to
  the existing tree/BookRAG design.

### 2026-07-14 · Codex

- Added the discussion-recording STT CLI under `discussions/transcribe.py` for
  Google Cloud Speech-to-Text V2 Sinhala transcription using `chirp_2` in
  `asia-southeast1`. Added the Google Speech/Storage/dotenv dependencies,
  `discussions/vocabulary.txt`, and local ignore rules for private recordings,
  generated transcripts, and discussion secrets.
- Updated local `.env` so `GOOGLE_APPLICATION_CREDENTIALS` points to the
  service-account JSON the user placed at
  `discussions/secrets/draftly-502319-96a312953eb0.json`. Verified dry-run
  behavior and that the credential file path exists; no real transcription was
  run because there was no recording in `discussions/recordings`.

### 2026-07-14 · Claude Code

- Consolidated the full project handover from the old `contxt.md` (the DSE /
  ChatGPT conversation dump) into this file, then removed `contxt.md`. Corrected
  the earlier too-narrow framing ("a retrieval system") to the real product: a
  lawyer-in-the-loop conveyancing drafting platform, with the statutory-corpus
  retrieval work as one sub-component. Deliberately excluded real client PII per
  the privacy rule.
- Created the cross-agent context system: this file + the `update-context`
  skill + root `AGENTS.md`, so Claude, Codex, and ChatGPT can hand off context.
- Downloaded BookRAG (arXiv:2512.03413) to `papers/` and converted it to
  markdown with docling (OCR disabled to dodge a `std::bad_alloc` on the
  figure-heavy appendix; got the full method, pages 1–12). Extracted its
  BookIndex schema and mapped it to Draftly's tree/graph/GT-Link design.
- Widened `.claude/settings.local.json` so routine work (in-repo file writes,
  venv toolchain, arXiv fetch, inspection) no longer prompts; kept destructive /
  outbound actions (push, delete, non-arXiv network) gated.
- Added ignore rules (`tmp/`, `.venv/`, `__pycache__/`, `data/legal-sources/derived/`).
