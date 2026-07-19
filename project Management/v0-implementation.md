# Draftly Roadmap — v0: The Notary's RTA Workbench

Rewritten 19 July 2026 after the mentor sessions (see
`discussions/meeting-notes/notes-jul-12.md` and `notes-jul-19.md`). The earlier
three-workstream roadmap (OCR / corpus / templates) fed this plan; the corpus
and retrieval work carries straight over. What changed: the product is now a
single, sharply scoped app.

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

## What the site does (page by page)

1. **Landing.** The four registration systems as the top-level choice — RDO,
   RTA, Apartment Ownership, Special Area — with only RTA active in v0 (the
   rest visibly "coming soon"; this matches how the mentor framed the market).
   Language selector (Sinhala / English) top-right. One short AI-generated
   looping hero video.
2. **RTA workspace — function picker.** The notary's functions as cards:
   *Examination of Title*, *Drafting*, *Execution*, *Attestation* (+ greyed
   *Registration*). Clicking one opens its guided flow.
3. **Guided function flow (the core screen).** Left: the ordered steps for the
   function (e.g. examination of title: land search → current owner → local-authority documents → party
   identification → recommend title). Center: the active step's instructions,
   applicable rules (statute section + gazette form, cited), and the inputs the
   step needs. Right: a grounded Q&A panel — ask anything mid-step; answers
   cite section IDs and case-law rules. Every step can be read or **listened
   to** (voice out), and deed particulars can be **dictated** (voice in) —
   the mentor's "client sits opposite, lawyer turns the screen" scenario.
4. **Document intake, not checklists.** The user uploads what they have
   (deeds, title certificate, plans, extracts). The system tells them **what
   is missing** ("these are missing, send them") and proceeds when supplied —
   the mentor explicitly rejected a manual tick-box checklist.
5. **Deed generation.** For drafting: collect the particulars (typed or
   dictated), apply the prescribed gazette form for the transaction type
   (transfer, gift, lease, mortgage), enforce the stamp-duty-valuation-first
   ordering, and emit the draft deed + the attestation clause (including the
   NIC-verification statement the law now requires). Export DOCX/PDF. A
   draft-checker flags errors in a user-supplied draft.
6. **FAQ + "frequently wrong questions".** Per function, a browsable bank of
   practice questions (target ~100 per topic) with grounded answers — the
   mentor's exam-paper-derived question bank plus case-law-derived cautionary
   notes ("beware of these", including obiter warnings).
7. **Practice-management extras (the retention hook).** Monthly-list
   auto-generation from the deeds the app has seen, with a reminder before the
   15th; annual licence-renewal reminder (March, High Court); jurisdiction
   (bala pradeshaya) warnings when the execution location looks wrong.
8. **Account/matter basics.** A matter = one property transaction: its
   uploaded documents, extracted facts, step progress, generated drafts, and
   an audit trail. The audit trail is the notary's due-diligence shield — the
   record that every required step was followed.

### UI brief (paste into v0.dev or use as the design spec)

> Professional legal-tech web app, desktop-first, for Sri Lankan notaries.
> Clean serif/sans pairing, deep green + parchment palette, generous white
> space. Screens: (1) landing with four registration-system cards (one active),
> Sinhala/English toggle; (2) function picker with five cards; (3) a
> three-panel guided workflow screen — step list with progress on the left,
> step detail with cited rules and required inputs in the center, a chat-style
> grounded Q&A panel with citation chips (e.g. "RTA s.38", "Gazette form TR-1")
> on the right; microphone buttons on inputs, listen buttons on step text;
> (4) a document-intake screen with upload dropzone and a "missing documents"
> list; (5) a deed-preview screen with form-field sidebar and DOCX/PDF export.
> Every AI answer shows its citations; unverifiable answers render as an
> explicit "insufficient authority" state, never as prose without sources.

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
  citations — feeds the cautionary notes and validity Q&A.
- **RTA deepening (the main v0 corpus work):** ingest the **three RTA
  gazettes** (prescribed forms and rules — one is 69 pages) as first-class
  sections; encode the prescribed forms as structured templates the deed
  generator fills; add the Rules of Notaries ("the 55", mentor's 20-topic
  split) as a distinct source with its own module.
- **Step-aware retrieval:** each workflow step carries its statutory anchors
  and keywords, so the step context scopes retrieval (the Jul-12 "steps are
  the retrieval pattern" insight) — a step's Q&A defaults to its sections
  before searching wide.
- **Question-bank serving:** the mentor-curated question set (his answers,
  AI-augmented, mentor-verified) served verbatim when a user question matches,
  with the generative path as fallback — curated beats generated when
  available.
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
  and the meeting-notes/context documentation.

## Build plan (order of attack)

1. **Contract first (this week).** Define the two schemas everything hangs on:
   the *step definition* (id, function, order, title, instruction, statutory
   anchors, required inputs, outputs) and the *matter record* (documents,
   extracted fields, step states, drafts). Content and engineering both build
   against these.
2. **Content track (mentor loop, weekly).** Draft the examination-of-title
   question set → mentor answers → AI-augment → file as step definitions +
   Q&A bank. Then drafting, execution, attestation. Scan and ingest the
   gazettes the moment they arrive; encode the prescribed forms as templates.
3. **Engine track.** Gazette ingestion; step-aware retrieval scoping; curated
   question-bank serving; Sinhala translate-then-retrieve; finish the rule
   vetting (judge fleet at 26/57 packs); wire the engine behind a FastAPI
   endpoint the web app calls.
4. **Web track.** Next.js app with the five screens above, calling the engine
   API; document upload with missing-document inference (start rule-based:
   required-set per transaction type); deed generation from gazette-form
   templates + DOCX export; voice in/out; matter records + audit trail.
5. **Evaluate and demo.** Input/output pairs from the mentor's real
   (anonymized) matters as the demo script: upload the bundle → missing-doc
   prompt → guided steps → generated deed — "the system working correctly on
   real matters," which is exactly the symposium demo.

Same three-way split as before, remapped: OCR/extraction work becomes document
intake + deed generation; corpus/retrieval work becomes the engine track;
templates work becomes gazette-form templates + exports. The junior law
student (mentor's contact) owns case-law reading support.

## Out of scope for v0 (deliberately)

- Registration function (most complicated — mentor deferred it), RDO/folio
  OCR, Apartment Ownership and Special Area modules, litigation modules (the
  25-action programme), plaint drafting, government-integration plays, mobile
  apps, payments/subscription plumbing. Name is a working title until the end.

## Principle to hold

Grounded or silent. Every answer, step, and generated clause traces to a
statute section, gazette form, or judged case-law rule — or the app says it
cannot answer. That discipline is the entire difference between this and a
chatbot, and it is what makes the audit trail a genuine due-diligence shield
for the notary.
