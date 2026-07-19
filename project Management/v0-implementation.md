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
   required before DOCX/PDF export with an audit-safe version id.
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
- **RTA deepening (the main v0 corpus work):** ingest the **three RTA
  gazettes** (prescribed forms and rules — one is 69 pages) as first-class
  sections; encode the prescribed forms as structured templates the deed
  generator fills; add the Rules of Notaries ("the 55", mentor's 20-topic
  split) as a distinct source with its own module.
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

## What we already have (assets to reuse)

- 57 statutes + 18 amendments parsed to 3,468 sections, indexed, embedded.
- The RTA itself (SRC011) already in the corpus with a section index.
- ~1,400 cleaned case-law rules with verbatim quotes (vetting in progress).
- The QA engine + evaluation harness + 18-question exam gold set.
- Mentor's materials incoming: his papers (handed over, being scanned), the
  three gazettes, 20-topic Rules of Notaries, recorded Bim Saviya classes,
  SLR soft copies, question-set review weekly.
- The processed corpus pipeline, citation graph (14,665 case→section links),
  the meeting-notes/context documentation, and the Harvey interface spec +
  screenshot research.

## Build plan (order of attack)

Sequenced by the interface spec's MVP tiers:

1. **Contract first (this week).** Define the two schemas everything hangs on:
   the *step definition* (id, function, order, title, instruction, statutory
   anchors, required inputs, automated checks, outputs) and the *matter
   record* (documents, extracted fields + verification states, step states,
   findings, drafts, audit events). Content and engineering both build
   against these.
2. **Content track (mentor loop, weekly).** Draft the examination-of-title
   question set → mentor answers → AI-augment → file as step definitions +
   Q&A bank. Then drafting, execution, attestation. Scan and ingest the
   gazettes the moment they arrive; encode the prescribed forms as templates.
3. **Engine track.** Gazette ingestion; step-aware retrieval scoping; curated
   question-bank serving; checks engine over verified facts; Sinhala
   translate-then-retrieve; finish the rule vetting (judge fleet at 26/57
   packs); wire the engine behind a FastAPI endpoint the web app calls.
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
