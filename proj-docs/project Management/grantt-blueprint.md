# Draftly — Gantt blueprint (CS3501 project schedule)

This file is the source of truth for the project schedule. The rendered chart
lives at `proj-docs/gantt/draftly-gantt.html`; its `PLAN` array should always
match the work-package tables below. Module rule: every work package has
exactly one owner. Owner cells are left blank here; claim them the same way
as the epics in `v0-tasks.md` and fill the names before the schedule
submission.

The plan is built from `project Management/v0-implementation.md` /
`v0-tasks.md` and the current research state in `.agents/context/CONTEXT.md`,
compressed into the CS3501 semester window (July to mid-October 2026).

## Module anchors (as stated on Moodle)

Dates are copied as the LMS states them. Two entries contradict each other;
confirm both with the TA before the schedule submission.

| Anchor | Stated date | Status |
| --- | --- | --- |
| Project idea | 8 July | Done |
| Project proposal | mid July | Done |
| Feasibility report | late July | Done (submitted 23 July) |
| Project schedule submission (this Gantt) | current phase | In progress |
| SRS + Software architecture document | "Project design phase — current week" | Next |
| Data collection and preparation | August | Largely done for the corpus track |
| Model development and initial testing | August–September | In progress |
| Progress evaluation | "6th Sept – 19th Sept, 2025" (sic) | Confirm year with TA |
| Progress-eval penalty note | "hold the evaluation before the 21st of August, 2026" (sic) | Contradicts the line above; confirm |
| Test plan → test report | September | Planned |
| Final evaluations and demos | 28 September – 2 October | Fixed |
| Final report / one-slider / video / code zip | weekly buckets run to 13–19 October | Planned |

Evaluations are individual even though the project is a group build, so the
schedule keeps each person's ownership legible: every work package below maps
to one name, and the logbook (weekly, individual) records the rest.

## The shape of the plan

CS3501 is a Data Science *and* Engineering project, and the plan keeps the
two sides explicit and parallel:

- The research side (data science) — the retrieval engine: corpus, rule
  layer, benchmark, baselines, evaluation. This is what the supervisor's
  publication interest rides on.
- The SE side — the platform and document intake: contracts, backend
  services behind every frontend surface, checks engine, templates/export,
  Document AI intake integration, deployment, and testing. This is what
  makes the work a product rather than a notebook.

The two sides meet at the verified matter record (the shared contract) and
at the P0 integrated demo. Concretely the work runs as three tracks after
the design documents land, joined by recurring lawyer-verification gates:

1. Research track — the retrieval engine is the research deliverable, and
   the supervisor's interest is a publishable result, so the engine must be
   battle-tested, not just working: a frozen benchmark scaled up from the
   past-paper collection (ten years of Law College papers, roughly 100
   questions) plus lawyer-contributed questions and a question set generated
   from the case-law corpus, double-annotated gold labels with an agreement
   score, external baselines run on our corpus (not just us-vs-earlier-us),
   ablation runs over the engine's switches, and error analysis. The
   headline result is lawyer-verified correctness on the frozen holdout;
   machine citation-support is a secondary automatic metric. This is the
   final showcase at the evaluations.
2. Product track — the platform. The M2 static UI clone is already built in
   `draftly-platform`; the remaining product work is contracts, the FastAPI
   backend wrapping `src/draftly/retrieval`, the checks engine, and the
   Form 8 draft/export path, ending in the P0 integrated demo.
3. Extraction track (SE) — document classification plus Document AI field
   extraction with pinpoint evidence, feeding the verified matter record and
   the holdout evaluation. There is no custom OCR build, which is what makes
   this integration work rather than research: the demo path targets clean,
   machine-readable documents, with the existing Document AI route
   (2,000-page ceiling, 208 used) for the scanned ones we choose to include.

Lawyer verification is a scheduled activity, not a background hope. The
mentor's availability paces the research labels, the rule catalogue wording,
Form 8 prescribed text, and the demo scenario, so reviews are batched into
three checkpoints (below) and booked in advance.

Descoped from the module window: the v0-plan M4 reminders, collaboration,
and template governance beyond the prescribed forms; the registration
function; and degraded-scan OCR. They stay on the roadmap for the symposium
build but do not appear in this schedule. Voice AI integration and the
agent-memory layer stay in scope as platform work packages.

## Work packages

Dates are week-granular targets, not promises; the fixed points are the
module anchors. Percentages in the chart mirror these tables.

### Track D — module documentation

| WP | Work package | Owner | Start | End | Deliverable |
| --- | --- | --- | --- | --- | --- |
| D1 | Project idea | ___ | 1 Jul | 8 Jul | Submitted (done) |
| D2 | Project proposal | ___ | 9 Jul | 15 Jul | Submitted (done) |
| D3 | Feasibility report | ___ | 16 Jul | 23 Jul | Submitted (done) |
| D4 | Project schedule + Gantt chart | ___ | 24 Jul | 31 Jul | This blueprint + rendered chart, submitted |
| D5 | Software requirement specification | ___ | 27 Jul | 7 Aug | SRS on the IEEE template |
| D6 | Software architecture document | ___ | 3 Aug | 14 Aug | SAD covering engine + platform + extraction |
| D7 | Individual logbooks | each member (individual) | weekly | weekly | Entries per significant task |
| D8 | Progress-evaluation pack | ___ | 31 Aug | 11 Sep | Slides, schedule update, individual work distribution |
| D9 | Test plan | ___ | 7 Sep | 18 Sep | Test plan on the module template |
| D10 | Test report | ___ | 14 Sep | 25 Sep | Executed test results |
| D11 | Final report (group) | ___ | 28 Sep | 19 Oct | On the module template |
| D12 | Final presentation, one-slider, video, code zip | ___ | 21 Sep | 2 Oct | Uploaded before the viva slot |

### Track R — research side: retrieval engine

| WP | Work package | Owner | Start | End | Deliverable |
| --- | --- | --- | --- | --- | --- |
| R1 | Corpus hardening | ___ | 28 Jul | 14 Aug | Re-extract the 42 fused OCR mega-sections; add the missing repealed statutes (Partition Ordinances 1863/1951, Fiscal's Ordinance 1867, Courts Ordinance 1889, Public Trustee, Privy Council appeals); section-node segmentation with frontmatter |
| R2 | Case-law rule layer completion | ___ | 4 Aug | 28 Aug | Track B (bounded LLM, naive window + applied fixes) over the 445 CommonLII abstentions and the 1,418 unreported judgments; deterministic section resolution; temporal-boundary checks on case→statute links |
| R3 | Benchmark construction (scaled) | ___ | 11 Aug | 4 Sep | Frozen eval sets: past-paper question bank mined from the ten-year collection in `past-papers/` (~100 questions; includes OCR + subject split of the scanned Final Year bundles for LW 307 Conveyancing), lawyer-contributed questions, case-law-derived questions (mask-a-citation generation from judgments), template/drafting cases (prescribed-form fills checked against the supervised ground-truth matter), populated `evaluation/retrieval-gold.csv` |
| R4 | Gold labelling + agreement | ___ | 17 Aug | 11 Sep | Two annotators (mentor + junior law student) label the gold answers independently; inter-annotator agreement (kappa) reported; verdicts on the 60-row headnote-rule sample and the 30-edge case↔statute sample; precision by confidence method recorded |
| R5 | Battle-testing and ablations | ___ | 31 Aug | 25 Sep | Full runs on the frozen benchmark; ablations over the dense/graph/corrective switches; authority-aware ranking experiment; error analysis and hardening loop. Headline metric: lawyer-verified correctness on the frozen holdout, reported as counts; machine citation-support demoted to a secondary automatic metric |
| R6 | External baselines | ___ | 7 Sep | 25 Sep | Plain BM25, dense-only, and hybrid baselines plus one published structure-aware system (LightRAG or HippoRAG; RAPTOR if time allows), all run on our corpus against the same frozen benchmark |
| R7 | Lawyer-labelled extraction dev set | ___ | 24 Aug | 11 Sep | Labelled examples for building and measuring extraction quality; feeds the holdout gates |

### Track P — SE side: platform

The frontend in `draftly-platform` is already built against mocks, so the
backend work is one work package per surface the frontend gives access to,
and they run in parallel once P1 lands.

| WP | Work package | Owner | Start | End | Deliverable |
| --- | --- | --- | --- | --- | --- |
| P1 | Contracts and scaffold (M0) | ___ | 28 Jul | 14 Aug | Matter-record + step-definition schemas as shared Python/TS types; FastAPI stub in `draftly-platform/backend/` |
| P2 | Wiring — Assistant + grounded research | ___ | 10 Aug | 4 Sep | FastAPI wrapping `src/draftly/retrieval`; Assistant screen off mocks first |
| P3 | Wiring — matters, documents, verified facts | ___ | 17 Aug | 11 Sep | Matter CRUD, document upload/storage, particular review states served from the API |
| P4 | Wiring — workflow runs, drafts, history/audit | ___ | 31 Aug | 18 Sep | Guided step runs, draft versioning, audit timeline served from the API |
| P5 | Checks engine + first rule catalogue | ___ | 24 Aug | 18 Sep | Deterministic checks over the verified record; the nine mandated check classes drafted and sent to the mentor for wording |
| P6 | Form 8 + template library, export, approval gate | ___ | 31 Aug | 18 Sep | Fillable Form 8 and the shared deed schedule with locked prescribed wording (from the mentor), DOCX/PDF export, lawyer approval gate |
| P7 | Agent memory (per-matter session layer) | ___ | 17 Aug | 11 Sep | Spike per `memory-system-evaluation.md` (Graphiti → MemMachine → own SQLite ledger), winner wired as the notes layer under the verified record |
| P8 | Voice AI integration | ___ | 7 Sep | 25 Sep | Speech in/out on the demo path (Sinhala/English), grounded answers only |
| P9 | Deployment and monitoring | ___ | 7 Sep | 27 Sep | Hosted demo instance with the E10 security controls (RBAC, encrypted storage, PII-safe logs); basic health/error monitoring; matches the module's deployment-and-monitoring phase |

### Track X — SE side: document intake and extraction

| WP | Work package | Owner | Start | End | Deliverable |
| --- | --- | --- | --- | --- | --- |
| X1 | Extraction schema + document classification | ___ | 28 Jul | 21 Aug | Field schema mapped to matter-record particulars; document-type detection over machine-readable bundles |
| X2 | Document AI field extraction | ___ | 17 Aug | 18 Sep | Document AI (cloud) extraction for particulars with confidence and pinpoint source spans; manual-entry fallback; no custom OCR build |
| X3 | Intake wired into the platform | ___ | 7 Sep | 25 Sep | Upload → extract → review flow live on the demo path |

### Track I — integration, evaluation, demo (both sides meet here)

| WP | Work package | Owner | Start | End | Deliverable |
| --- | --- | --- | --- | --- | --- |
| I1 | P0 demo path end to end | ___ | 7 Sep | 25 Sep | Create matter → upload/extract → verify facts → guided steps → grounded Q&A → checks → Form 8 draft → approve/export → audit trail, on an anonymized matter |
| I2 | Alpha testing | ___ | 14 Sep | 25 Sep | Whole-team walk-through of every wired surface; bug triage feeding the test report (D10) |
| I3 | Holdout evaluation + acceptance gates | ___ | 14 Sep | 27 Sep | Frozen lawyer-verified holdout run against the plan's 11 gates; counts reported, not bare percentages |
| I4 | Demo rehearsal + final evaluations | ___ | 21 Sep | 2 Oct | Rehearsed demo script on approved anonymized matters; viva 28 Sep – 2 Oct |

## Lawyer-verification checkpoints

Three batched review packs, booked with the mentor now:

1. Mid August — headnote-rule sample (60 rows), case↔statute link sample
   (30 edges), first extraction labels. Feeds R4 and R7.
2. Early September — benchmark gold answers (double-annotated, agreement
   scored), rule-catalogue wording, Form 8 and deed-schedule prescribed
   text, Sinhala terminology for `si.json`. Feeds R3, R4, P5, P6.
3. Late September — holdout labels and the demo scenario sign-off. Feeds I3
   and I4.

If a pack slips a week, the dependent work package slips with it; nothing
unverified is promoted in its place.

## Risks that shape the dates

- Mentor availability is the pacing constraint on every verification gate.
  Mitigation: batch the packs, book the slots at the start of August, and
  keep the deterministic pipelines running on unverified data in the
  meantime (clearly labelled as such).
- Free-tier model quotas (Gemini for the QA evals, NVIDIA NIM for Track B)
  have already stalled runs once. Mitigation: run the long evaluations early
  in each window and checkpoint everything for resume.
- The Moodle dates disagree with each other (2025 vs 2026, and the
  21 August penalty note vs the 6–19 September window). Mitigation: confirm
  at the next Thursday session before submitting this schedule.
- Three people, five tracks. The split holds only if the M4 descope holds;
  any new feature request goes to the post-module roadmap, not this chart.

## Keeping the chart in sync

The rendered chart reads its data from the `PLAN` array at the top of the
script in `proj-docs/gantt/draftly-gantt.html`. When a work package moves,
edit both the table here and that array; the render recomputes the timeline,
month grid, and group bars on load. Print to PDF in A4 landscape for the
submission.
