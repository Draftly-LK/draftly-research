# Draftly v0 — Task Breakdown, Milestones, and Work Split

Derived from `v0-implementation.md` (the authoritative plan). This file turns
that plan into concrete work: **milestones** (phase gates with a definition of
done) and **epics** (pickable chunks of work, each broken into tasks and
subtasks). Nothing from the plan is dropped.

## How the three of us use this

- The team is three people. **Work is divided by picking epics, not by cutting
  every task into three.** Put your name on an epic in its `Owner:` line and
  you own it end to end.
- Pick what you want to do. The *Suggested lead* line on each epic is only a
  hint from the historical workstream split (Lahiru = extraction/OCR, Himath =
  data/corpus/engine, Praveen = templates/outputs/interface) — ignore it if you
  want a different piece.
- Some epics are **shared** by nature (contracts, security, evaluation). Those
  say so; agree a primary owner but expect all three to touch them.
- An epic can have more than one owner, and a big epic (the web app) can be
  split by screen between two people. Just write who owns what.
- Statuses: `todo` · `in-progress` · `blocked` · `done`. `✓` on a subtask means
  already built (carried from the plan).

## Milestones (phase gates)

`v0 = P0 + P1`. P0 is the first integrated demo, not the finished product.

| ID | Milestone | Done when | Feeding epics |
| --- | --- | --- | --- |
| **M0** | Foundations & contracts | Repo scaffolded (`apps/web`, `apps/api`); matter-record + step-definition schemas exist as machine-validated, shared Python/TS types; agent-memory spike started; security foundations chosen | E0, E1, E9 (start), E10 (start) |
| **M1** | Data, engine & content ready | Gazettes ingested + layered corpus; step-aware retrieval + question-bank serving + checks engine over the record; extraction pipeline reads supported docs with evidence spans; examination-of-title workflow + rule catalogue drafted and mentor-verified | E2, E3, E4, E5, E6 |
| **M2** | Static UI clone | Every screen built in React with mock data, matched to the Harvey screenshots; Tiptap editor with FactChip; mock types mirror engine JSON | E7 (UI parts), E8 (Phase 1) |
| **M3** | P0 integrated demo | Examination-of-title + Form 8 (transfer) works end to end through the UI on an anonymized matter: create → upload/extract → verify facts → guided steps → grounded Q&A → checks → generate/approve/export → audit trail. No manual DB edits | E7, E8 (Phase 2–3), E9, E10 |
| **M4** | P1 completes v0 | Drafting, execution, attestation workflows; voice in/out; question bank + frequently-wrong-questions; template governance; monthly-list & licence reminders; collaboration | E4, E6, E7, E8 |
| **M5** | Evaluation & demo | Lawyer-verified holdout frozen; all acceptance gates run and recorded; demo script rehearsed on approved anonymized matters | E11 |

Dependency spine: **M0 → M1 → M2 → M3 → M4 → M5**. Engine/content/extraction
(M1) and the static UI (M2) run in parallel once contracts (M0) are frozen.

---

## E0 — Repo & environment scaffolding

- **Goal:** the skeleton every other epic builds inside.
- **Feeds:** M0 · **Suggested lead:** whoever starts first (shared) ·
  **Owner:** ___ · **Status:** todo

### E0 tasks

1. **E0.1 Monorepo layout** — create `apps/web` (Next.js) and `apps/api`
   (FastAPI) beside the existing `src/draftly`.
   - [ ] Next.js App Router + TypeScript + Tailwind + shadcn/ui + Tiptap +
     lucide-react in `apps/web`
   - [ ] FastAPI project stub in `apps/api` importing `src/draftly.retrieval`
   - [ ] shared `packages/shared` (or equivalent) for cross-language types
2. **E0.2 Dev tooling** — lint/format/test wiring for both apps; `.env.example`;
   run scripts documented in the README.
3. **E0.3 CI check** — build + typecheck + unit tests on push (lightweight).

---

## E1 — Contracts & schemas (shared, do first)

- **Goal:** the versioned contracts every service shares — matter record and
  step definition — as machine-validated schemas with Python **and** TypeScript
  types.
- **Feeds:** M0 (blocks M1–M3) · **Suggested lead:** shared, one primary owner ·
  **Owner:** ___ · **Status:** todo

### E1 tasks

1. **E1.1 Matter-record schema** — all 13 entities from the plan: Matter,
   Document, Source span, Particular, Party, Parcel, Instrument, Interest,
   Finding, Step run, Draft, Approval, Audit event.
   - [ ] Field-level definition per entity
   - [ ] State enums with explicit allowed transitions (matter, document,
     particular, finding, step, draft, approval)
   - [ ] Correction rule: new value preserves the old; never overwrite history
2. **E1.2 Step-definition schema** — ID, version, function, order, title,
   instruction; applicability conditions; required particulars/documents/inputs;
   statutory/Gazette/form/case anchors; automated rule IDs + blocking; allowed
   lawyer decisions; produced outputs; owner/approval/effective/superseded.
3. **E1.3 Contract invariants as validation** — encode all 8 invariants
   (output particular ⇐ approved form; extracted particular ⇐ ≥1 source span;
   only lawyer sets verified/corrected; final draft ⇐ verified/corrected only;
   locked wording changes ⇐ new template version; blocked step ⇐ evidence or
   override; every correction/override/approval/export/template change ⇒ audit
   event; deleted docs stay referenced but unused).
4. **E1.4 Shared types** — generate/share Python + TypeScript types; mock types
   mirror the engine JSON (`StatuteAnswer.to_dict()` / `StatuteHit.to_dict()`
   in `src/draftly/retrieval/models.py`) so UI wiring is a data-source swap.

---

## E2 — Retrieval / answering engine deepening

- **Goal:** wire the existing engine into the app and extend it along the
  methodology's §9 design record where v0 needs it.
- **Feeds:** M1, M3 · **Suggested lead:** Himath (data/corpus/engine) ·
  **Owner:** ___ · **Status:** in-progress (parts built)

### E2 tasks

1. **E2.1 Already built (verify + keep)** — grounded citation-gated answering ✓;
   hybrid BM25 + dense + hints + RRF + graph PageRank ✓; multi-part handling ✓;
   case-law rule layer plumbing ✓.
2. **E2.2 Gazette ingestion** — ingest RTA gazettes as first-class sections.
   - [ ] 2022 Gazette (2308/27) first — in hand, forms index extracted (4–39)
   - [ ] 2014 Gazette (1886/58) after Sinhala font recovery (see E5.6)
   - [ ] 1998 Gazette (1050/10) once obtained (see E6.5)
3. **E2.3 Layered corpus with authority levels** — primary law → derived
   guidance → practice rules → templates → private matter layer; every item
   carries the notes' metadata (authority level, effective date, linked section,
   form number, workflow stage, verification status, personal-data flag).
4. **E2.4 Step-aware retrieval scoping** — each step's anchors + keywords scope
   retrieval; step Q&A defaults to its sections before searching wide.
5. **E2.5 Curated question-bank serving** — serve mentor-verified answers
   verbatim on match; generative path as fallback.
6. **E2.6 Sinhala translate-then-retrieve** — Sinhala questions against the
   English corpus, answers rendered in the UI language.
7. **E2.7 §9 data-model growth (only what v0 needs)** — unified edge list +
   `authority.csv` (feeds the research UI's authority tiers); dated
   section-version model (feeds the case-law temporal fixes in E3).
8. **E2.8 FastAPI endpoint** — expose `/answer`, `/search`, `/topics`,
   `/sources` (serializers exist); `build_index()` once at startup.

---

## E3 — Case-law extraction & rule layer

- **Goal:** finish the extracted-rule pipeline and clear its four correctness
  blockers so rules can rise above the unverified-candidate tier.
- **Feeds:** M1 · **Suggested lead:** Himath + the junior law student (reading
  support) · **Owner:** ___ · **Status:** in-progress

### E3 tasks

1. **E3.1 Finish rule vetting** — resume the judge-then-filter fleet (paused at
   26/57 packs); land `rules_vetted.csv`.
2. **E3.2 Blocker — section matching** — resolve sections deterministically
   against `statute-section-index.json` (3,547 sections); null anything that
   doesn't resolve.
3. **E3.3 Blocker — temporal boundary** — add `enacted_year` / `repealed_year`
   to the source registry; reject case→section links where the case predates the
   statute; flag links to statutes repealed before the case.
4. **E3.4 Blocker — the law changed under the corpus** — download + register the
   repealed historical statutes (Partition Ordinance 1863/1951, Fiscal's
   Ordinance 1867, Courts Ordinance 1889, Public Trustee Ordinance, Privy
   Council appeals); tag each rule with the statutory *regime* it was decided
   under; serve repealed-law rules as historical context only.
5. **E3.5 Blocker — extraction correctness** — stratified lawyer sample as the
   authoritative gate before any rule reaches the research UI.
6. **E3.6 Authority tiers in the UI** — surface binding / persuasive /
   historical / unverified-candidate everywhere case rules appear.

---

## E4 — Checks / rule catalogue & checks engine

- **Goal:** deterministic checks over the verified record, from a versioned,
  lawyer-verified catalogue.
- **Feeds:** M1, M4 · **Suggested lead:** shared (engine owner + content owner) ·
  **Owner:** ___ · **Status:** todo

### E4 tasks

1. **E4.1 Catalogue contract** — one versioned catalogue with the fields from
   the plan (Rule ID+version, function+applicability, required inputs, condition,
   finding, authority, effective period, review state, tests).
2. **E4.2 First catalogue content** — the 9 mandated classes: required-document
   completeness; party identity/capacity/representation/PoA; title-certificate ↔
   cadastral ↔ extent ↔ instrument consistency; current interests/encumbrances;
   prescribed-form selection + mandatory particulars + placeholders; stamp-duty
   valuation & sequencing (inside drafting); execution + s.44; attestation +
   alteration/erasure certification; jurisdiction/division/office warnings.
3. **E4.3 Checks engine** — deterministic evaluation over the verified-facts
   record; grounded citations attached; no unconstrained model output.
4. **E4.4 Lawyer verification** — each active rule's authority, wording,
   severity, and expected result verified; unverified guidance stays `draft`.
5. **E4.5 Rule tests** — positive, negative, missing-input, boundary, and
   superseded-version examples per rule.

---

## E5 — Document intake & extraction

- **Goal:** read supported deeds/matter documents, classify, extract
  particulars with confidence and pinpoint evidence, and place every result
  before the lawyer. No AT-form extraction, no historical title tracking.
- **Feeds:** M1, M3 · **Suggested lead:** Lahiru (OCR/extraction) ·
  **Owner:** ___ · **Status:** todo

### E5 tasks

1. **E5.1 Extraction schema** — the fields the supported document types can
   populate, mapped to matter-record particulars (from E1).
2. **E5.2 OCR / digital-text pipeline** — Sinhala/English; digital text where
   available, OCR where not; recoverable failure states, no silent loss.
3. **E5.3 Document classification** — detected vs verified type per document.
4. **E5.4 Field/particular extraction** — values + confidence + source spans
   (page + bbox/char offsets + excerpt + method).
5. **E5.5 Manual-entry fallback** — unreadable/unsupported docs stay visible;
   manual values share the same verification gate as extracted ones.
6. **E5.6 2014 Gazette Sinhala font recovery** — legacy font mapping or OCR
   (legal-source prep, separate from client-document OCR; unblocks E2.2).
7. **E5.7 Lawyer-labelled examples** — labelled set for building + measuring
   extraction (dev set; feeds E11).

---

## E6 — Content track (workflows + question bank)

- **Goal:** the mentor-loop content: guided step definitions and the Q&A bank
  for the four functions, statutory anchors verified against the Act.
- **Feeds:** M1, M4 · **Suggested lead:** shared with the mentor + junior law
  student · **Owner:** ___ · **Status:** todo

### E6 tasks

1. **E6.1 Examination-of-title question set** — draft → mentor answers →
   AI-augment → file as step definitions + Q&A bank.
2. **E6.2 Remaining functions** — drafting, execution, attestation question sets
   (same loop). Examination first for the P0 demo.
3. **E6.3 Step anchors** — seed from the practical presentation's section groups
   (examination 34/35/37/38/42/49; drafting 28/39/43/46–49/57/63; execution
   43–44; registration 40/41/45), each **verified against the Act** before it
   enters a step definition.
4. **E6.4 Mentor review loop** — weekly printed output packs → mentor markup →
   fold back.
5. **E6.5 Source acquisition** — obtain Gazette 1050/10 (1998); collect official
   Bim Saviya forms (transfer/gift/lease/mortgage) in editable or accurately
   transcribed form; secure lawyer approval for each field set and template.

---

## E7 — Draft editor & templates (Tiptap)

- **Goal:** the Tiptap draft editor and the prescribed-form templates it fills
  from the verified record, with export.
- **Feeds:** M2, M3, M4 · **Suggested lead:** Praveen (templates/outputs) ·
  **Owner:** ___ · **Status:** todo

### E7 tasks

1. **E7.1 Editor foundation** — Tiptap with schema-validated JSON documents;
   locked nodes for prescribed statutory wording; editable schedule/particular
   regions.
2. **E7.2 FactChip node** — inline node carrying `{fact_id, verification_state}`;
   cannot insert an unverified fact; hover shows source document + pinpoint.
3. **E7.3 Versioning** — JSON snapshots; version hash as audit-safe ID;
   `prosemirror-changeset` compare view; restore + read-only previous-version
   banner.
4. **E7.4 Form templates** — encode **Form 8 (transfer) first**, then Forms
   9–11 (gift, lease, mortgage) as fillable JSON templates.
5. **E7.5 Export** — purpose-built converter per form (JSON → `docx`; PDF via
   print CSS); page-accurate output at export (pagination is an export concern,
   not an editor one); lawyer approval gate before export; audit-safe version id.
6. **E7.6 Sinhala rendering QA** — font choice (Noto Sans Sinhala) + rendering
   at 200% zoom.

---

## E8 — Web app (Harvey-clone UI)

- **Goal:** replicate Harvey's workspace layout with Draftly's nouns and tokens,
  then wire the backend screen by screen. Large epic — **split by screen**
  between two owners if you like.
- **Feeds:** M2, M3, M4 · **Suggested lead:** Praveen + one other ·
  **Owner(s):** ___ · **Status:** todo

### Phase 1 — static UI clone (mock data)

1. **E8.1 Shell** — sidebar (workspace mark, ⌘K search, Create, matter selector,
   nav Home/Assistant/Matters/Workflows/History/Library, Settings+Help) + matter
   header + secondary nav (Overview · Documents · Verified facts · Workflow ·
   Checks · Drafts · Activity).
2. **E8.2 Visual system** — Draftly tokens (canvas `#F4F3EF`, ink `#1B211D`,
   forest `#24533D`, status colors, 6 px radius, 1 px borders, 40–44 px rows);
   fonts Source Serif 4 / Inter / Noto Sans Sinhala.
3. **E8.3 Home** — wordmark, composer card, suggested notarial prompts, recent
   matters, obligations.
4. **E8.4 Workflows** — library grid (Functions · Draft templates · Question
   sets · Examples) + three-pane guided run screen.
5. **E8.5 Draft editor screen** — Tiptap toolbar; Revisions + Sources rails;
   FactChip; version pill + restore. (Uses E7.)
6. **E8.6 Assistant** — scope chips, per-part claims + citation chips, evidence
   pane, authority badges, insufficient-authority empty state.
7. **E8.7 Matters** — files table (upload/processing states, confidence, source
   evidence, correction, replacement history); verified-particulars review table
   with the five states; AT forms visible but marked unsupported.
8. **E8.8 Remaining screens** — Checks, History/Activity (audit timeline),
   create-matter stepper, entry screen (four regimes, RTA active).

### Phase 2 — wire the backend

1. **E8.9 API integration** — swap mock layer for API calls: Assistant first
   (engine ready), then matters + particulars, then drafts.

### Phase 3 — rest of P0

1. **E8.10 P0 completion** — minimal auth; protected document upload/storage;
    extraction with evidence spans + manual fallback; DOCX/PDF export; EN/සිං
    switch on the demo path.

---

## E9 — Agent memory (per-matter session layer)

- **Goal:** pick the memory system by spike and wire the winner as the
  episodic/notes layer under the verified record.
- **Feeds:** M0 (start), M3 · **Suggested lead:** Himath ·
  **Owner:** ___ · **Status:** todo

### E9 tasks

1. **E9.1 Spike scaffold** — `experiments/agent-memory/`, the fixed scenario +
   4-question scoring from `memory-system-evaluation.md`.
2. **E9.2 Graphiti spike** — run the scenario; score correction-wins,
   history-survives, provenance, cost.
3. **E9.3 MemMachine spike** — same scenario + scoring.
4. **E9.4 Decision + fallback** — adopt the winner, or build the SQLite ledger
   (REMem model + `superseded_by`) if both fail.
5. **E9.5 Wire the winner** — as the notes layer only; the verified matter
   record stays our own gated two-tier schema; corrections never overwrite.

---

## E10 — Security & privacy (shared, release dependency)

- **Goal:** the controls that make v0 safe to run on confidential documents —
  part of completion, not post-demo hardening.
- **Feeds:** M0 (start), every later milestone · **Suggested lead:** shared,
  one primary owner · **Owner:** ___ · **Status:** todo

### E10 tasks

1. **E10.1 RBAC** — lawyer/reviewer/administrator; every matter limited to
   explicitly assigned users.
2. **E10.2 Encryption** — in transit + at rest for DB, stored docs, backups,
   exports.
3. **E10.3 Protected storage** — object storage; DB stores opaque references,
   not public paths/URLs.
4. **E10.4 Secrets** — from env/secret manager; never committed or logged.
5. **E10.5 PII-safe telemetry** — logs, analytics, notifications, screenshots,
   error reports carry no raw names/NICs/addresses/signatures/images.
6. **E10.6 Data separation** — dev / eval / demo separated; demo uses approved
   anonymized copies, never `data/raw/`.
7. **E10.7 Retention & deletion** — retention, export expiry, user-requested
   deletion, backup restore — documented before lawyer testing.
8. **E10.8 Audit events** — append-only for view/extract/verify/correct/
   override/generate/approve/export/permission-change.
9. **E10.9 External-call minimization** — OCR/translation/speech/embedding/LLM
   calls send only the minimum; record processor/purpose/time; provider training
   & retention disabled where supported.
10. **E10.10 Security tests** — no cross-matter access; no unverified fact in an
    approved export.

---

## E11 — Evaluation & acceptance

- **Goal:** measure the Bim Saviya workflow honestly against fixed gates, on a
  frozen lawyer-verified holdout.
- **Feeds:** M5 · **Suggested lead:** shared, one primary owner ·
  **Owner:** ___ · **Status:** todo

### E11 tasks

1. **E11.1 Development set** — used while building extraction, rules, templates.
2. **E11.2 Lawyer-verified holdout** — frozen, never used to tune; supported
   transaction types, EN + Sinhala docs, low-quality scans, missing-document
   cases, conflicts, clean cases. Per-matter: document labels, field values +
   source locations, expected findings, authorities, workflow decisions,
   approved target form.
3. **E11.3 Acceptance gates** — run and record all 11 gates (document
   processing; classification ≥90% macro F1; field extraction ≥90% / mandatory
   95%; provenance 100%; verification gate zero unverified in drafts; checks
   ≥90% precision / ≥85% recall; grounded answering 100% valid citations / ≥90%
   claim support; draft correctness; export fidelity; workflow completion;
   privacy zero failures). Report counts, not bare percentages.
4. **E11.4 Demo script** — approved anonymized upload→missing-doc→verify→steps→
   deed. A successful demo does not replace the recorded holdout results.

---

## Suggested starting split (optional — change freely)

Not a rule, just a way to start from the historical strengths. Adjust to what
each of you wants:

| Person | Natural epics to consider |
| --- | --- |
| Extraction-minded | E5 (intake/extraction), E5.6 font recovery, half of E8 (Matters/Documents screens) |
| Data/engine-minded | E2 (engine), E3 (case-law), E9 (memory), E4 with content owner |
| Interface/templates-minded | E7 (editor/templates), the other half of E8 (shell, Home, Assistant, Workflows) |
| Shared by all three | E0 (scaffold), E1 (contracts), E6 (content/mentor loop), E10 (security), E11 (evaluation) |

Whoever finishes their M0/M1 work first should pull the next unassigned epic
rather than subdividing someone else's.
