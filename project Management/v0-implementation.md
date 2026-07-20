# Draftly Roadmap — v0: The Notary's RTA Workbench

Rewritten 19 July 2026 after the mentor sessions (see
`discussions/meeting-notes/notes-jul-12.md` and `notes-jul-19.md`). The earlier
three-workstream roadmap (OCR / corpus / templates) fed this plan; the corpus
and retrieval work carries straight over. What changed: the product is now a
single, sharply scoped app, and the interface follows the workspace patterns
of mature legal-AI products (Harvey research in
`docs/product-research/harvey/`).

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

## What the site does

**The interface source of truth is
`docs/product-research/harvey/draftly-interface-spec.md`** (a full
screen-by-screen specification modeled on mature legal-AI workspaces — see the
Harvey screenshots beside it). Direction: a **lawyer's operating workspace,
not a chatbot** — matter-centric, workflow-first, evidence beside every
output, verification as an explicit action, abstention as a designed state,
bilingual by construction.

The shell (persistent left sidebar: search, Home, Matters, Workflows, Legal
sources, History) wraps these surfaces:

1. **Home** — resume work in one click: recent matters with status and open
   issues, upcoming obligations (monthly-list deadline, licence renewal). No
   marketing hero, no generic prompt suggestions.
2. **Create matter** — a short stepper: regime (RTA active; others labelled
   future), transaction type (transfer/gift/lease/mortgage), privacy-safe
   reference, optional documents. Under a minute.
3. **Matter overview** — what is known, what is missing, what to do next:
   function completion, document processing status, missing/conflicting
   evidence, drafts and their review state, recent activity.
4. **Document intake** — upload what exists; the system infers and lists
   **missing documents** from the matter type (the mentor explicitly rejected
   tick-box checklists). Three-pane review per document: pages / text layer /
   extracted fields with confidence and pinpoint source.
5. **Verified facts** — the lawyer-approved structured matter record, as a
   review table with explicit states: *unreviewed → verified / corrected /
   conflict / blocked*. Unverified facts can never silently enter a draft.
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
   documents, identity conflicts, parcel/extent conflicts, chain-of-title
   breaks, encumbrances, stamp-duty sequencing, execution/attestation,
   jurisdiction), each with severity, evidence, authority, and
   resolve/waive-with-reason actions.
9. **Draft editor** — two panes: assistant + source facts left, paginated
   editable draft right. Prescribed gazette forms as templates; every inserted
   fact traceable to its source; version compare and restore; lawyer approval
   required before DOCX/PDF export with an audit-safe version id. Editor
   foundation: Tiptap (see the technology decision below).
10. **Workflow library** — approved procedures (functions, draft templates,
    question sets, worked examples) with version governance; no generic
    AI-agent marketplace.
11. **History vs audit trail** — history resumes work; the immutable matter
    audit trail (uploads, fact changes, verifications, overrides, authorities
    retrieved, approvals, exports) is the notary's due-diligence shield.

Practice-management hooks (monthly-list auto-generation + before-the-15th
reminder, licence renewal, jurisdiction warnings) surface on Home and in
checks. Visual language, components, accessibility (WCAG 2.2 AA, Sinhala at
200% zoom), and responsive rules are all specified in the interface spec.

## What the retrieval/answering engine must do

The engine exists (`src/draftly/retrieval/`, Streamlit slice in
`apps/statute-retrieval/`) and was upgraded and evaluated this week. v0 wires
it into the site and extends it along these axes — everything below is either
built (✓) or scoped:

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
  documents, conflicts, chain breaks, sequencing, jurisdiction) are rule-based
  evaluations over the verified-facts record — deterministic first, grounded
  citations attached.
- **Sinhala:** questions in Sinhala answered against the English corpus
  (translate-then-retrieve for v0), answers rendered in the UI language;
  voice in/out via the same STT (Chirp) and a TTS pass.
- **Evaluation:** the gold Q&A set (mentor-verified answers + the exam-paper
  harness in `evaluation/qa-agent/`) scores every engine change; printed
  output packs go to the mentor for markup — his preferred loop.

## The RTA source collection — what v0 takes from it

The mentor's RTA materials arrived: 20 files inventoried and assessed in
`Registration of Title Act Notes.md` (the Act, two of the three gazettes,
three presentations, eight process maps, an examination-of-title checklist,
a sample attestation clause, three completed sample instruments, one scanned
Sinhala form). These are the sources v0 builds from; each track's inputs are
now concrete rather than awaited.

**How each track uses it:**

- **Schemas (build-plan step 1).** The matter-record fields come from the
  three sample transfer instruments (office-use registration fields,
  cadastral/parcel identifiers, title-certificate details, parties,
  consideration, encumbrances, life-interest conditions, witness and
  attestation blocks) plus the examination checklist. The step definitions'
  *statutory anchors* seed from the practical-aspects presentation's section
  groups — examination ss. 34, 35, 37, 38, 42, 49; drafting ss. 28, 39, 43,
  46–49, 57, 63; execution ss. 43–44; registration ss. 40, 41, 45 — each
  verified against the Act before it enters a step definition.
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
- **Web track.** The one prescribed draft flow targets **Form 8 (transfer)**:
  we hold the 2022 Gazette form, two sample transfer instruments for field
  discovery, and the attestation-clause sample for the section 44 execution
  checks.

**New work items this creates:** recover the 2014 Gazette's Sinhala text
(legacy font mapping or OCR); OCR the Form 31 scan; obtain Gazette 1050/10
(1998); anonymize and get lawyer approval before any sample becomes a
template.

**Boundaries (binding):** presentations, process maps, and checklists are
explanatory material — nothing derived from them becomes a retrieval rule or
step anchor until checked against the Act, regulations, or Gazette. The
sample instruments contain private personal and property data: no
publication, no demo use, no model training, and the incomplete sample's
stale carried-over fields are the standing argument for why drafts generate
from the verified matter record, never by copying an earlier deed.

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
  `Registration of Title Act Notes.md`): the Act (75 sections, readable),
  the 2022 Gazette with the prescribed-form index, the 2014 Gazette
  (pending Sinhala font recovery), three presentations, eight process maps,
  the examination checklist, and the sample instruments/clauses.
- Still incoming from the mentor: Gazette 1050/10 (1998), the 20-topic Rules
  of Notaries, recorded Bim Saviya classes, SLR soft copies, and the weekly
  question-set review loop.
- The processed corpus pipeline, citation graph (14,665 case→section links),
  the meeting-notes/context documentation, and the Harvey interface spec +
  screenshot research.
- The agent-memory evaluation (`memory-system-evaluation.md`): 22 papers
  reviewed, shortlist fixed (Graphiti → MemMachine → own SQLite ledger), spike
  scenario and scoring already designed.

## Build plan (order of attack)

Sequenced by the interface spec's MVP tiers:

1. **Contract first (this week).** Define the two schemas everything hangs on:
   the *step definition* (id, function, order, title, instruction, statutory
   anchors, required inputs, automated checks, outputs) and the *matter
   record* (documents, extracted fields + verification states, step states,
   findings, drafts, audit events). Field discovery for both now has real
   sources: the sample instruments and the examination checklist (see the
   RTA source-collection section). Content and engineering both build
   against these.
2. **Content track (mentor loop, weekly).** Draft the examination-of-title
   question set → mentor answers → AI-augment → file as step definitions +
   Q&A bank. Then drafting, execution, attestation. The gazettes are in
   hand: encode Form 8 (transfer) as the first Tiptap template, then Forms
   9–11; seed step anchors from the presentation's section groups, verified
   against the Act.
3. **Engine track.** Gazette ingestion (2022 Gazette first; 2014 after
   Sinhala font recovery); layered corpus with authority levels and the
   notes' metadata fields; step-aware retrieval scoping; curated
   question-bank serving; checks engine over verified facts; Sinhala
   translate-then-retrieve; finish the rule vetting (judge fleet at 26/57
   packs); run the agent-memory spike and wire the winning store as the
   per-matter session layer (see the agent-memory section above); wire the
   engine behind a FastAPI endpoint the web app calls.
4. **Web track — P0 scope** (per the interface spec): auth + matter list;
   create-RTA-matter stepper; document upload/processing with the three-pane
   review; verified-facts table with verification states; guided
   examination-of-title workflow (three-pane); step-aware grounded Q&A;
   missing-document/conflict findings; one prescribed draft flow with
   approval + DOCX/PDF export + audit trail; English/Sinhala switch on the
   demo path.
5. **P1 after the P0 demo:** drafting/execution/attestation workflows, voice
   in/out, question bank + frequently-wrong-questions, template governance,
   monthly-list and licence reminders, collaboration.
6. **Evaluate and demo.** Input/output pairs from the mentor's real
   (anonymized) matters as the demo script: upload the bundle → missing-doc
   prompt → verify facts → guided steps → generated deed — "the system
   working correctly on real matters," which is exactly the symposium demo.

Same three-way split as before, remapped: OCR/extraction work becomes document
intake + fact verification; corpus/retrieval work becomes the engine track;
templates work becomes gazette-form templates + the draft editor. The junior
law student (mentor's contact) owns case-law reading support.

## Out of scope for v0 (deliberately)

- Registration function (most complicated — mentor deferred it), RDO/folio
  OCR, Apartment Ownership and Special Area modules, litigation modules (the
  25-action programme), plaint drafting, government-integration plays, mobile
  apps, payments/subscription plumbing, external shared spaces, Word/DMS
  integrations. Name is a working title until the end.

## Principle to hold

Grounded or silent. Every answer, step, and generated clause traces to a
statute section, gazette form, or judged case-law rule — or the app says it
cannot answer. That discipline is the entire difference between this and a
chatbot, and it is what makes the audit trail a genuine due-diligence shield
for the notary.
