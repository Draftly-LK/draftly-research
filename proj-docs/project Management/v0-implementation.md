# Draftly Roadmap — v0: The Notary's RTA Workbench

Rewritten 19 July 2026 after the mentor sessions (see
`discussions/meeting-notes/notes-jul-12.md` and `notes-jul-19.md`). The earlier
OCR, corpus, and template work carries into this plan. Historical title tracking
and AT-form extraction do not. The product is now a single, sharply scoped app,
and the interface follows the workspace patterns of mature legal-AI products
(Harvey research in `docs/product-research/harvey/`).

## The product in one line

A web app where a Sri Lankan notary (new or experienced) does their **four core
conveyancing functions under the Registration of Title Act (Bim Saviya)** —
examination of title, drafting, execution, attestation — with every step,
rule, and form supplied and every answer grounded in statute, gazette, or case
law. Registration is deferred; stamping is folded into drafting as the
"stamp-duty valuation first" sequencing rule.

Why RTA first (mentor's reasoning, Jul-19): RTA documents are machine-readable
(no handwritten-folio OCR), ~90% of lawyers don't know the Act, the system is
~90% statute law (registries follow statute, not case law), and the whole
country migrates to it over the next 10–15 years. One app that satisfies
90–95% of a title-registration notary's needs is achievable in the project
window; the other three regimes (RDO folios, Apartment Ownership, Special
Area) come later as modules on the same skeleton.

### V0 boundary and meaning of done

**V0 means everything described in this document, including both the P0 demo
milestone and the P1 completion work.** P0 is only the first integrated
milestone; it is not the finished v0.

V0 is done when every in-scope capability works end to end through the user
interface on the agreed evaluation matters, without manual database edits or
hidden operator intervention. The lawyer must be able to create and resume a
matter, process its documents, verify facts against evidence, complete all four
guided functions, receive grounded answers and deterministic checks, generate
and review the approved forms, export them, and inspect the audit history.

V0 is **not a title-tracking system**. It does not reconstruct a historical
chain of title or extract the AT form, because the relevant historical material
is not reliably extractable within this scope.

Draftly still reads supported deeds and other matter documents through OCR or
digital-text extraction, classifies them, extracts useful particulars, and
places every result before the lawyer for verification. The verified record is
then checked against the structured particulars and official forms supplied
through the Bim Saviya/RTA process. The lawyer can correct or manually enter
anything that extraction cannot read. Draftly applies the guided workflow,
legal-source retrieval, deterministic checks, and approved Bim Saviya form
templates without building an ownership-history graph.

## What the site does

**The interface source of truth is
`docs/product-research/harvey/draftly-interface-spec.md`** (a full
screen-by-screen specification modeled on mature legal-AI workspaces — see the
Harvey screenshots beside it). Direction: a **lawyer's operating workspace,
not a chatbot** — matter-centric, workflow-first, evidence beside every
output, verification as an explicit action, abstention as a designed state,
bilingual by construction.

Where the interface specification mentions historical title-chain
reconstruction, the narrower Bim Saviya boundary in this document takes
priority.

The shell (persistent left sidebar: search, Home, Matters, Workflows, Legal
sources, History) wraps these surfaces:

1. **Home** — resume work in one click: recent matters with status and open
   issues, upcoming obligations (monthly-list deadline, licence renewal). No
   marketing hero, no generic prompt suggestions.
2. **Create matter** — a short stepper: regime (RTA active; others labelled
   future), transaction type (transfer/gift/lease/mortgage), privacy-safe
   reference, applicable Bim Saviya form, and optional documents. Under a
   minute.
3. **Matter overview** — what is known, what is missing, what to do next:
   function completion, document-processing status, extracted or entered
   particulars, missing/conflicting information, drafts and their review state,
   and recent activity.
4. **Document intake and Bim Saviya particulars** — upload supported deeds and
   matter documents for OCR or digital-text extraction. Show pages, extracted
   text, fields, confidence, and pinpoint evidence for lawyer review. Alongside
   that evidence, show the structured particulars required by the selected
   official Bim Saviya form. Unsupported or unreadable documents remain visible
   for manual entry; AT-form extraction and historical title tracking are not
   offered.
5. **Verified particulars** — the lawyer-approved structured matter record, as
   a review table with explicit states: *unreviewed → verified / corrected /
   conflict / blocked*. Extracted and manually entered values share the same
   verification gate, and unverified particulars can never silently enter a
   draft.
6. **Guided RTA workflow** — the core screen, three panes: ordered steps with
   blockers (left), the active step's plain-language objective + required
   inputs + statutory anchors + automated checks + lawyer decision (center),
   contextual grounded assistant scoped to the step (right, collapsible).
   Listen controls on instructions, dictation on inputs. Blocked mandatory
   steps require evidence or a recorded override that enters the audit trail.
7. **Legal research** — matter-aware or standalone; scope chips (current step,
   documents, statutes, gazettes, verified case rules, question bank);
   per-part answers with pinpoint citation chips and an evidence pane;
   explicit **insufficient-authority state**; binding vs persuasive vs
   historical vs unverified-candidate authority always distinguished.
8. **Checks and missing evidence** — findings grouped by class (missing
   documents, identity conflicts, parcel/extent conflicts, inconsistencies
   between current RTA records, encumbrances, stamp-duty
   sequencing, execution/attestation, jurisdiction), each with severity,
   evidence, authority, and resolve/waive-with-reason actions.
9. **Draft editor** — two panes: assistant + source facts left, paginated
   editable draft right. Prescribed gazette forms as templates; every inserted
   fact traceable to its source; version compare and restore; lawyer approval
   required before DOCX/PDF export with an audit-safe version id. Editor
   foundation: Tiptap (see the technology decision below).
10. **Workflow library** — approved procedures (functions, draft templates,
    question sets, worked examples) with version governance; no generic
    AI-agent marketplace.
11. **History vs audit trail** — history resumes work; the immutable matter
    audit trail (uploads, extraction versions, particular changes,
    verifications, overrides, authorities retrieved, approvals, exports) is the
    notary's due-diligence shield.

Practice-management hooks (monthly-list auto-generation + before-the-15th
reminder, licence renewal, jurisdiction warnings) surface on Home and in
checks. Visual language, components, accessibility (WCAG 2.2 AA, Sinhala at
200% zoom), and responsive rules are all specified in the interface spec.

## What the retrieval/answering engine must do

The engine exists (`src/draftly/retrieval/`, Streamlit slice in
`apps/statute-retrieval/`) and was upgraded and evaluated this week. **The
engine's source of truth is `retrieval-engine-methodology.md`** (same folder):
§§1–8 walk the code and data pipeline as built, and §9 carries the full design
record — the 12-paper adopt/reject verdicts, the planned data model, query
routing, authority-aware ranking, and the P1–P6 build order the engine grows
along. v0 wires the engine into the site and extends it along these axes —
everything below is either built (✓) or scoped:

- ✓ **Grounded, citation-gated answering**: every claim cites a retrieved
  section ID; claims are entailment-verified; no-evidence questions abstain
  ("insufficient authority") instead of hallucinating.
- ✓ **Hybrid retrieval**: BM25 + Gemini dense vectors + curated hints, fused
  with RRF; deterministic statute graph (cross-references, amendment→principal
  targets, definitions; ~15.8K edges) expands evidence via PageRank.
- ✓ **Multi-part question handling**: per-part evidence quotas + one corrective
  retrieval retry for unanswered parts.
- ✓ **Case-law rule layer**: extracted, cleaned rules (headnote + LLM tracks,
  quality-judged; `rules_vetted.csv` pipeline) with verbatim quotes and case
  citations — feeds the cautionary notes and validity Q&A. Authority tiers
  (binding / persuasive / historical / unverified candidate) must surface in
  the research UI.
- **RTA deepening (the main v0 corpus work):** ingest the RTA gazettes as
  first-class sections — the **2022 Gazette (2308/27) first**: it is in hand,
  readable, and carries the prescribed forms (index already extracted, Forms
  4–39); the **2014 Gazette (1886/58)** is in hand but its legacy Sinhala
  font garbles text extraction, so it needs font mapping or OCR before
  line-level ingestion; the **1998 Gazette (1050/10)** still has to be
  obtained. Encode the prescribed forms as structured templates the deed
  generator fills, starting with Forms 8–11 (transfer, gift, lease,
  mortgage — the create-matter transaction types). Add the Rules of Notaries
  ("the 55", mentor's 20-topic split) as a distinct source with its own
  module.
- **Step-aware retrieval:** each workflow step carries its statutory anchors
  and keywords, so the step context scopes retrieval (the Jul-12 "steps are
  the retrieval pattern" insight) — a step's Q&A defaults to its sections
  before searching wide. This powers the workflow screen's right-rail
  assistant and its scope chips.
- **Question-bank serving:** the mentor-curated question set (his answers,
  AI-augmented, mentor-verified) served verbatim when a user question matches,
  with the generative path as fallback — curated beats generated when
  available.
- **Checks engine:** the finding classes on the checks screen (missing
  documents, identity and parcel conflicts, current-title inconsistencies,
  sequencing, and jurisdiction) are rule-based evaluations over the
  verified-facts record — deterministic first, grounded citations attached.
- **Sinhala:** questions in Sinhala answered against the English corpus
  (translate-then-retrieve for v0), answers rendered in the UI language;
  voice in/out via the same STT (Chirp) and a TTS pass.
- **Evaluation:** the gold Q&A set (mentor-verified answers + the exam-paper
  harness in `evaluation/qa-agent/`) scores every engine change; printed
  output packs go to the mentor for markup — his preferred loop.

## The RTA source collection — what v0 takes from it

The mentor's RTA materials arrived: 20 files inventoried and assessed in
`docs/RTA_notes/README.md` (the Act, two of the three gazettes, three
presentations, eight process maps, an examination-of-title checklist, a sample
attestation clause, three completed sample instruments, one scanned Sinhala
form). These are the sources v0 builds from; each track's inputs are now
concrete rather than awaited.

**How each track uses it:**

- **Schemas (build-plan step 1).** Official Bim Saviya forms for transfer,
  gift, lease, and mortgage define the required structured output fields.
  Supported deeds and other matter documents define the OCR/extraction inputs
  that can populate those fields for lawyer verification. Private samples may
  support field discovery and extraction tests, but they do not become drafting
  templates. The step definitions' *statutory anchors* seed from the
  practical-aspects presentation's section groups — examination ss. 34, 35,
  37, 38, 42, 49; drafting ss. 28, 39, 43, 46–49, 57, 63; execution ss. 43–44;
  registration ss. 40, 41, 45 — each verified against the Act before it enters
  a step definition.
- **Content track.** The six-function split (examination, drafting,
  execution, stamping, attestation, registration) is confirmed by the
  practical presentation; v0's four-function scope stands, with stamping as
  checks inside drafting. The examination question set can be drafted now,
  anchored on the Act's Part structure (75 sections mapped in the notes).
- **Engine track.** Ingestion is layered, not merged (per the notes'
  processing structure, which matches our authority tiers): primary law
  (Act + gazettes, section/form-segmented) → derived guidance (presentations,
  process maps, linked back to the provisions they explain) → practice rules
  (checklist items, local-authority certificate requirements, each with a
  verification status) → templates (anonymized, lawyer-approved only) →
  private matter layer (originals, access-controlled, excluded from demos
  and general indexes). Every processed item carries the notes' metadata
  fields (authority level, effective date, linked section, form number,
  workflow stage, verification status, personal-data flag).
- **Checks engine.** The finding classes get their first concrete rule
  sources: the examination checklist (encumbrances, probate/estate,
  corporate authority, plans and conformity) and the local-authority
  presentation (street line, building line, non-vesting, ownership,
  conformity, rates) — split into generic rules vs matter-specific instances
  before use, validated against primary authority.
- **Web track.** The one prescribed draft flow targets **Form 8 (transfer)**,
  using the official Bim Saviya form as its schema and approved template. The
  private transfer and attestation samples are comparison material only.

**New work items this creates:** obtain Gazette 1050/10 (1998), collect the
official Bim Saviya forms in editable or accurately transcribed form, and get
lawyer approval for each structured field set and template. Supported deeds and
other matter documents need an extraction schema and lawyer-labelled examples.
AT-form extraction remains excluded. Recovering the 2014 Gazette's legacy
Sinhala text is legal-source preparation, separate from client-document OCR.

**Boundaries (binding):** presentations, process maps, and checklists are
explanatory material — nothing derived from them becomes a retrieval rule or
step anchor until checked against the Act, regulations, or Gazette. The
sample instruments contain private personal and property data: no
publication, no demo use, no model training, and the incomplete sample's
stale carried-over fields are the standing argument for why drafts generate
from the verified matter record, never by copying an earlier deed.

## Formal contracts

The matter record and step definition are versioned contracts shared by the
web app, extraction service, retrieval engine, checks engine, and draft
generator. Define them as machine-validated schemas before feature work begins,
then generate or share the corresponding Python and TypeScript types.

### Matter record

| Entity | Required content |
| --- | --- |
| Matter | Stable ID, privacy-safe reference, RTA regime, transaction type, language, status, assigned users, and timestamps |
| Document | Stable ID, matter ID, version, detected and verified type, language, page count, checksum, processing state, protected storage reference, and replacement link |
| Source span | Document ID, page, bounding box or character offsets, extracted excerpt, extraction method, and confidence |
| Particular | Official-form field ID, extracted or entered value, normalized value, source spans or manual evidence notes, verification state, reviewer, and correction history |
| Party | Role, verified identity attributes, capacity, representative or power-of-attorney relationship, and supporting particulars |
| Parcel | Cadastral map, block, parcel, extent, administrative divisions, title-certificate reference, and supporting particulars |
| Instrument | Prescribed form, transaction type, parties, parcel, consideration, relevant interests, execution state, and source particulars |
| Interest | Current registered interest or encumbrance, holder, affected parcel, status, dates, and evidence; this is not a historical title-chain edge |
| Finding | Rule ID, severity, affected particulars, evidence, authority, status, owner, resolution, and waiver reason |
| Step run | Step-definition version, state, inputs, checks, lawyer decision, overrides, and completion time |
| Draft | Template version, verified particular IDs used, unresolved placeholders, content snapshot, status, and version hash |
| Approval | Artifact, approving lawyer, decision, timestamp, and comments |
| Audit event | Actor, action, object, before/after references, timestamp, reason, and correlation ID |

Matter, document, particular, finding, step, draft, and approval states must use
enumerations with explicit allowed transitions. Corrections create a new value
and preserve the earlier value; they never overwrite history.

### Step definition

Every guided step contains:

- stable ID, schema version, function, order, title, and instruction;
- applicability conditions for transaction and matter type;
- required particulars, documents, and lawyer inputs;
- statutory, Gazette, form, and verified-case anchors;
- automated rule IDs and blocking behavior;
- allowed lawyer decisions and required reasons;
- produced particulars, findings, drafts, or checklist items; and
- owner, approval status, effective date, and superseded version.

### Contract invariants

- Every required output particular is defined by an approved Bim Saviya form or
  workflow schema.
- Every extracted particular has at least one valid source span.
- Only a lawyer may move a particular to `verified` or `corrected`.
- A final draft may reference only verified or corrected particulars.
- Prescribed locked wording may change only through a new approved template
  version.
- A blocked mandatory step needs new evidence or a recorded lawyer override.
- Every correction, override, approval, export, and template change produces an
  audit event.
- Deleted or replaced documents remain referenced by historical audit events
  but are not used for new outputs.

## Rule and check catalogue

Checks are deterministic rules over the verified matter record. They do not
come from unconstrained model output. Maintain one versioned catalogue with the
following contract:

| Field | Meaning |
| --- | --- |
| Rule ID and version | Stable identity and change history |
| Function and applicability | Examination, drafting, execution, or attestation plus relevant transaction types |
| Required inputs | Facts and documents needed to evaluate the rule |
| Condition | Deterministic pass, warning, fail, or needs-review logic |
| Finding | Message, severity, affected facts, and suggested lawyer action |
| Authority | Verified Act section, Gazette provision or form, or approved practice source |
| Effective period | Date range and superseded rule where applicable |
| Review state | Draft, legally verified, active, suspended, or retired |
| Tests | Positive, negative, missing-input, boundary, and superseded-version examples |

The first catalogue must cover:

1. Required-document completeness for each transaction type.
2. Party identity, legal capacity, representation, and power-of-attorney
   evidence.
3. Consistency between the RTA title certificate, cadastral identifiers,
   parcel extent, current instrument, and supporting documents.
4. Current registered interests and encumbrances relevant to the transaction.
5. Prescribed-form selection, mandatory particulars, and unresolved
   placeholders.
6. Stamp-duty valuation and sequencing checks included within drafting.
7. Execution checks, including parties, witnesses, identity evidence, and
   section 44 requirements where verified.
8. Attestation completeness and alteration or erasure certification.
9. Jurisdiction, administrative division, and registration-office warnings.

A lawyer must verify the authority, wording, severity, and expected result of
each active rule. Guidance from presentations or checklists remains in `draft`
until matched to primary authority or explicitly approved as a practice rule.

## Security and privacy controls

V0 processes confidential legal and identity documents, so these controls are
part of completion rather than post-demo hardening:

- Role-based access for lawyer, reviewer, and administrator roles, with every
  matter limited to explicitly assigned users.
- Encryption in transit and at rest for the database, stored documents,
  backups, and exported artifacts.
- Protected object storage; the database stores opaque references rather than
  public file paths or permanent public URLs.
- Secrets loaded from environment or secret management, never committed or
  written to logs.
- PII-safe application logs, analytics, notifications, screenshots, and error
  reports. Raw names, identity numbers, addresses, signatures, and document
  images must not appear there.
- Separate development, evaluation, and demonstration data. Demo matters must
  use approved anonymized copies, not the originals in `data/raw/`.
- Document retention, export expiry, user-requested deletion, and backup
  restoration procedures recorded before lawyer testing.
- Append-only audit events for viewing, extraction, verification, correction,
  override, generation, approval, export, and permission changes.
- External OCR, translation, speech, embedding, and language-model calls send
  only the minimum required content and record the processor, purpose, and
  time. Provider training or retention must be disabled where the service
  supports that control.
- Automated tests confirm that one user cannot access another user's matter
  and that unverified facts cannot reach an approved export.

## Evaluation dataset and acceptance thresholds

V0 evaluation measures the Bim Saviya workflow promised here. It includes OCR
and extraction for the supported deeds and matter documents, but does not
include AT-form extraction, historical title-chain reconstruction,
entity-linking across old deed pedigrees, or a handwritten-folio OCR benchmark.

Build two privacy-safe sets before final evaluation:

1. A development set used while building extraction, rules, and templates.
2. A lawyer-verified holdout set that is not used to tune prompts, rules, or
   templates. It contains the supported transaction types and representative
   English and Sinhala RTA documents, low-quality scans, missing-document
   cases, conflicts, and clean cases.

Each holdout matter must include verified document labels, field values with
source locations, expected findings, applicable authorities, completed
workflow decisions, and an approved target form. Record dataset size and class
coverage before evaluation; do not report percentages without the underlying
counts.

Initial v0 acceptance gates are:

| Capability | Acceptance threshold |
| --- | --- |
| Document processing | Every supported document reaches `ready for review` or an explicit recoverable failure state; no silent loss |
| Document classification | At least 90% macro F1 on the lawyer-verified holdout set |
| Required field extraction | At least 90% normalized F1 overall and 95% accuracy for mandatory fields used in the first approved form |
| Evidence provenance | 100% of accepted extracted particulars open the correct source document and page or region |
| Verification gate | Zero unverified facts in an approved draft across all holdout runs |
| Deterministic checks | At least 90% precision and 85% recall against lawyer-labelled expected findings |
| Grounded answering | 100% structurally valid citations and at least 90% lawyer-confirmed claim support; unsupported questions abstain |
| Draft correctness | 100% of mandatory fields come from verified facts, locked wording is preserved, and no unresolved placeholder survives approval |
| Export fidelity | Every approved test form passes lawyer review for content, Sinhala/English rendering, page layout, and version identification |
| Workflow completion | Every in-scope P0 and P1 acceptance scenario completes through the UI without manual data repair |
| Privacy and access | Zero cross-matter authorization failures and zero raw PII disclosures in demo assets or logs |

Thresholds are provisional until the mentor approves the holdout design. Any
failed gate remains an open v0 defect or must be narrowed explicitly in scope;
it cannot be hidden by a successful scripted demo.

## Agent memory — the per-matter session layer

v0 ships with a working agent memory: the layer that lets the assistant
resume a matter across sessions (document summaries ingested, session notes,
lawyer corrections remembered with history). The full evaluation — 22 papers,
16 systems, 4 benchmarks — and the selection method live in
`memory-system-evaluation.md`; this plan only fixes what v0 must do:

- **Pick the system by spike, not by adoption.** No off-the-shelf system
  satisfies all six requirements (self-hostable Python, provenance,
  correction-with-history, two tiers, light infra, per-matter keying). Run
  the fixed spike scenario (`experiments/agent-memory/`) against **Graphiti**
  first, **MemMachine** second; if both fail or fight the integration, build
  the fact ledger ourselves on SQLite using REMem's append-only model plus a
  `superseded_by` column.
- **The two-tier rule is ours regardless of the winner.** The verified matter
  record stays our own gated schema; the memory system only holds the
  episodic/notes layer underneath it. A lawyer correction never overwrites —
  the old value is invalidated and preserved (the audit-trail requirement in
  memory form).
- **Scoring is fixed in advance:** correction wins, history survives,
  provenance traces to the correcting event, and integration/infra cost stays
  tolerable.

## Draft editor — Tiptap as the template foundation

Decision: build the draft editor on **Tiptap** (MIT, React bindings, built on
ProseMirror). It was chosen because its document model is exactly the shape
our templates need:

- **Documents are schema-validated JSON**, not HTML blobs. A prescribed
  gazette form becomes a Tiptap JSON template: the mandatory statutory
  wording as locked nodes (ProseMirror plugins make ranges non-editable),
  the schedules and particulars as editable regions.
- **Fact provenance becomes a node type, not a discipline.** A custom
  `FactChip` inline node carries `{fact_id, verification_state}` and renders
  like a mention chip; the deed generator emits template JSON with these
  nodes resolved from the verified matter record. An unverified fact
  *cannot* be inserted because the node requires a fact ID from the record —
  the "unverified facts never silently enter a draft" rule enforced by the
  editor schema itself. Hover shows the source document and pinpoint.
- **Versioning is cheap:** every version is a JSON snapshot; audit-safe
  version IDs are snapshot hashes; `prosemirror-changeset` powers the
  compare view. No dependency on Tiptap's paid collaboration cloud.
- **Sinhala** input is native contenteditable behaviour; we own only font
  choice and rendering QA.

Two accepted trade-offs, planned rather than discovered later:

1. **Pagination happens at export, not in the editor.** ProseMirror is a
   continuous-flow editor; the legally meaningful pagination is the
   printed/attested artifact anyway. The editor shows continuous flow; the
   export path produces page-accurate output.
2. **DOCX/PDF export is our code.** Tiptap's own DOCX extension is paid; the
   open path is a purpose-built converter per prescribed form (JSON → `docx`
   npm library, PDF via print CSS). With a handful of finite, structured
   forms this is small work and gives audit-exact output a generic converter
   would not.

Alternatives considered: raw ProseMirror (more control, months more work),
Lexical (younger extension ecosystem), Slate/Plate (historically less
stable), CKEditor (licensing friction). Tiptap keeps ProseMirror's document
model with the ecosystem that saves the time.

## Web app — build plan (Harvey-clone UI)

Decision (21 July): replicate Harvey's workspace UI directly — their layout,
components, and density — and plug our features and backend into it. Sources:
the 10 screenshots in `docs/product-research/harvey/screenshots/` and the
interface spec. RTA drafting lives under **Workflows**. Full editing is
supported (Tiptap, per the decision above).

**Fixed choices:**

- **Stack:** Next.js (App Router, TypeScript) + Tailwind CSS + shadcn/ui +
  Tiptap + lucide-react, at `apps/web/`. Backend later: FastAPI wrapping
  `src/draftly/retrieval`.
- **Sidebar = Harvey's layout, Draftly's nouns:** "Draftly" workspace mark +
  search (⌘K) + collapse; **Create** button; matter selector; nav **Home,
  Assistant, Matters** (Harvey's Vault, with recent-matters sublist),
  **Workflows, History, Library**; Settings + Help pinned bottom.
- **Visual system:** Harvey structure with the spec's Draftly tokens (canvas
  `#F4F3EF`, ink `#1B211D`, forest `#24533D`, teal/amber/red status colors,
  6 px radius, 1 px borders, dense 40–44 px table rows). Fonts: Source
  Serif 4 display, Inter UI, Noto Sans Sinhala.

**Phase 1 — static UI clone (no backend, mock data only).** Build every
screen as React with fixtures, matched side-by-side against the screenshots:

1. Shell (sidebar + matter header + secondary nav: Overview · Documents ·
   Verified facts · Workflow · Checks · Drafts · Activity).
2. Home — serif wordmark, composer card (Matter ▾ / Prompts ▾, Files/Sources,
   mic, ink send), suggested notarial prompts, recent matters, obligations.
3. Workflows — library grid (tabs: Functions · Draft templates · Question
   sets · Examples) and the three-pane guided run screen (steps rail
   240–280 px, step detail center, assistant rail 340–400 px).
4. Draft editor — Tiptap with Harvey's toolbar; right-rail **Revisions** and
   **Sources** cards; **FactChip** inline node with verification-state dot
   and source popover; version pill + read-only previous-version banner
   with restore.
5. Assistant — scope chips, per-part claims with citation chips, evidence
   pane, authority badges, the insufficient-authority empty state.
6. Matters — files table with upload and processing states, OCR/extraction
   confidence, source evidence, manual correction, and replacement history;
   verified-particulars review table with the five verification states. AT
   forms remain visible reference files but are marked unsupported for
   extraction.
7. Checks, History/Activity (audit timeline), create-matter stepper, entry
   screen (four regimes, RTA active).

Mock types mirror the engine's real JSON (`StatuteAnswer.to_dict()` /
`StatuteHit.to_dict()` in `src/draftly/retrieval/models.py`) plus the matter
record schema, so wiring is a data-source swap, not a rewrite. All fixture
names invented — nothing from `data/raw/`.

**Phase 2 — wire the backend.** FastAPI app exposing the engine
(`/answer`, `/search`, `/topics`, `/sources` — the serializers already
exist) plus matter CRUD, documents, extracted particulars, drafts, and audit
events on SQLite; `build_index()` once at startup. Swap the mock layer for API
calls screen by screen: Assistant first (engine is ready today), then matters
and particulars, then drafts.

**Phase 3 — the rest of P0:** minimal auth, protected document upload and
storage, OCR/extraction for supported deeds and matter documents with evidence
spans and manual fallback, DOCX/PDF export, and the EN/සිං switch on the demo
path. Historical title tracking and AT-form extraction remain outside the
integration.

The full screen-by-screen build plan with routes and component inventory is
in the working plan file; this section is its fixed summary.

## Case-law extraction — plan and open blockers

The full extraction design (two-track headnote/LLM strategy, prompts,
validation gates, cost model) lives in `case-law-extraction-plan.md` and is
part of this v0 plan. Where it stands: 2,193 quote-grounded rules extracted,
re-extracted with the improved prompt and cleaned to ~1,400, quality judging
in progress (`rules_vetted.csv` pipeline). Grounding is solved — every rule
carries a verbatim quote or is rejected. What is **not** solved are these four
blockers:

1. **Section matching is unreliable.** The model sees statute *titles* from
   the catalogue, not section text, so it guesses section numbers — the
   holdout study measured statute attribution as the worst dimension (~19%
   wrong). Fix direction: resolve sections deterministically against the
   parsed section index (`statute-section-index.json`, 3,547 sections) instead
   of trusting the model, and null anything that doesn't resolve.
2. **No temporal boundary.** A 1959 judgment can currently be linked to a
   statute enacted in 1970 — the catalogue has no enactment/repeal dates, so
   nothing blocks an anachronistic match. Fix direction: add
   `enacted_year` / `repealed_year` to the source registry and reject any
   case→section link where the case predates the statute (and flag links to
   statutes repealed before the case).
3. **The law changed under the corpus.** ~68% of judgments are pre-1950 and
   construe *earlier versions or repealed predecessors* of today's statutes
   (Partition Ordinance 1863/1951, Fiscal's Ordinance 1867, Courts Ordinance
   1889, Public Trustee Ordinance, Privy Council appeals) that aren't in the
   catalogue at all. Fix direction: download and register those historical
   statutes, then tag each extracted rule with the statutory *regime* it was
   decided under, so a rule construing repealed law is served as historical
   context, never as current authority.
4. **Extraction correctness itself.** Verbatim grounding proves the quote is
   real, not that the rule is right — the judged holdout measured only ~58%
   of grounded rules as legally usable (borrowed lower-court reasoning,
   obiter tagged as ratio, over-generalized statements). Fix direction:
   finish the judge-then-filter vetting (fleet paused at 26/57 packs), then
   the stratified lawyer sample as the authoritative gate before any rule
   reaches the research UI.

Until 1–3 land, case-law rules stay in the **unverified-candidate** authority
tier in the interface — visible, cited, but explicitly below statute.

## What we already have (assets to reuse)

- 57 statutes + 18 amendments parsed to 3,468 sections, indexed, embedded.
- The RTA itself (SRC011) already in the corpus with a section index.
- ~1,400 cleaned case-law rules with verbatim quotes (vetting in progress).
- The QA engine + evaluation harness + 18-question exam gold set.
- The RTA source collection, in hand (see the section above and
  `docs/RTA_notes/README.md`): the Act (75 sections, readable), the 2022
  Gazette with the prescribed-form index, the 2014 Gazette (pending Sinhala
  font recovery), three presentations, eight process maps, the examination
  checklist, and the sample instruments/clauses.
- Still incoming from the mentor: Gazette 1050/10 (1998), the 20-topic Rules
  of Notaries, recorded Bim Saviya classes, SLR soft copies, and the weekly
  question-set review loop.
- The processed corpus pipeline, citation graph (14,665 case→section links),
  the meeting-notes/context documentation, and the Harvey interface spec +
  screenshot research.
- The agent-memory evaluation (`memory-system-evaluation.md`): 22 papers
  reviewed, shortlist fixed (Graphiti → MemMachine → own SQLite ledger), spike
  scenario and scoring already designed.
- The retrieval-engine methodology and design record
  (`retrieval-engine-methodology.md`): the engine as built, module by module
  (§§1–8), plus the 12-paper design record — planned data model, query
  routing, authority-aware ranking, P1–P6 build order (§9).

## Build plan (order of attack)

Sequenced by the interface spec's MVP tiers. P0 is the first integrated demo;
P0 and P1 together are v0:

1. **Contract first (this week).** Define the two schemas everything hangs on:
   the *step definition* (id, function, order, title, instruction, statutory
   anchors, required inputs, automated checks, outputs) and the *matter
   record* (documents, extracted fields + verification states, step states,
   parties, parcels, instruments, current interests, findings, drafts,
   approvals, and audit events). Implement the formal contracts and invariants
   defined above as machine-validated schemas with shared Python and
   TypeScript types. Field discovery for both now has real sources: the sample
   instruments and the examination checklist. Content and engineering both
   build against these contracts.
2. **Content track (mentor loop, weekly).** Draft the examination-of-title
   question set → mentor answers → AI-augment → file as step definitions +
   Q&A bank. Then drafting, execution, attestation. The gazettes are in
   hand: encode Form 8 (transfer) as the first Tiptap template, then Forms
   9–11; seed step anchors from the presentation's section groups, verified
   against the Act. Build and lawyer-verify the rule/check catalogue alongside
   each workflow rather than adding checks after the interface is complete.
3. **Engine track.** Gazette ingestion (2022 Gazette first; 2014 after
   Sinhala font recovery); layered corpus with authority levels and the
   notes' metadata fields; step-aware retrieval scoping; curated
   question-bank serving; checks engine over verified facts; Sinhala
   translate-then-retrieve; finish the rule vetting (judge fleet at 26/57
   packs); run the agent-memory spike and wire the winning store as the
   per-matter session layer (see the agent-memory section above); grow the
   engine along the methodology's §9 design record where v0 needs it — the
   unified edge list and `authority.csv` feed the research UI's authority
   tiers, and the dated section-version model feeds the case-law temporal
   fixes; wire the engine behind a FastAPI endpoint the web app calls.
4. **Security and privacy track, from the first vertical slice.** Implement
   role-based matter access, protected document storage, secrets handling,
   PII-safe logs, anonymized demo data, retention/deletion behavior, append-only
   audit events, and the cross-matter access tests defined above. Security is a
   release dependency for every later milestone.
5. **Web track — P0 scope** (per the interface spec): auth + matter list;
   create-RTA-matter stepper; document upload/processing with the three-pane
   review; verified-facts table with verification states; guided
   examination-of-title workflow (three-pane); step-aware grounded Q&A;
   missing-document/conflict findings; one prescribed draft flow with
   approval + DOCX/PDF export + audit trail; English/Sinhala switch on the
   demo path.
6. **P1 completes v0 after the P0 demo:** drafting, execution, and attestation
   workflows, voice
   in/out, question bank + frequently-wrong-questions, template governance,
   monthly-list and licence reminders, collaboration.
7. **Evaluate and demo.** Freeze the lawyer-verified holdout before the final
   run and apply every acceptance gate above. Use approved anonymized
   input/output pairs as the demo script: upload the bundle → missing-document
   prompt → verify facts → guided steps → generated deed. A successful demo
   does not replace the recorded holdout results.

Same three-way split as before, remapped: OCR/extraction work becomes document
intake + fact verification; corpus/retrieval work becomes the engine track;
templates work becomes gazette-form templates + the draft editor. The junior
law student (mentor's contact) owns case-law reading support.

## Out of scope for v0 (deliberately)

- Historical title tracking or ownership-chain graphs, AT-form extraction,
  registration function (most complicated — mentor deferred it), RDO/folio
  OCR, Apartment Ownership and Special Area modules, litigation modules (the
  25-action programme), plaint drafting, government-integration plays, mobile
  apps, payments/subscription plumbing, external shared spaces, and Word/DMS
  integrations. Name is a working title until the end.

## Principle to hold

Grounded or silent. Every answer, step, and generated clause traces to a
statute section, gazette form, or judged case-law rule — or the app says it
cannot answer. That discipline is the entire difference between this and a
chatbot, and it is what makes the audit trail a genuine due-diligence shield
for the notary.
