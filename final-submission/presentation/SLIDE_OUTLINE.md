# Draftly: 20-slide academic presentation outline

Working duration: **20 minutes**, with **18:00** of planned speech, including a 2:30 product demonstration. Stable IDs below are for the eventual deck and presenter notes. Visible copy is intentionally short; the cues are spoken, not projected. Projected figures should be fitted without cropping important text except where an older design's obsolete storage lane is deliberately excluded and labelled.

## 01 · `draftly-cover` · Draftly makes conveyancing decisions traceable

- **On slide:** Draftly; *Grounded legal retrieval and a lawyer-controlled conveyancing matter workflow for Sri Lanka*; Group 06, University of Moratuwa; Dhanapalage Himath Nimpura Dhanapala, Lahiru Dilshan, B. K. Praveen De Silva; supervisor Dr. Nisansa de Silva.
- **Visual/layout:** Quiet typographic cover and existing Draftly logo. Style B cover; no stock legal imagery.
- **Time:** 20 s.
- **Speaking cues:** State the project scope. Name the two outputs: retrieval study and matter workbench. Promise evidence for both.
- **Transition:** Start with the work a notary actually faces.
- **Source:** Final report title page and abstract.

## 02 · `matter-before-form` · A transfer starts with uncertain evidence, not a blank form

- **On slide:** Property evidence → applicable law → professional decision. Small callout: scanned documents, amendments, judgments.
- **Visual/layout:** Three-stage pipeline with a document bundle at left and a lawyer decision at right; no invented client document.
- **Time:** 40 s.
- **Speaking cues:** A title certificate, plan, parties, and registered interests must be reconciled. Law may be spread across different sources and effective dates. A wrong identifier or missing rule changes the matter.
- **Transition:** The team checked that workflow with practitioners.
- **Source:** Final report §§1.1–1.2; mid-evaluation slides 4–8.

## 03 · `practitioner-constraints` · Practitioner consultations turned risks into design constraints

- **On slide:** Three consultations; verify identity and title; track source and date; keep lawyer judgment.
- **Visual/layout:** Three constraints in a sparse grid, with the consultation count as a small provenance label.
- **Time:** 40 s.
- **Speaking cues:** Describe the three recorded consultations and the notary/lecturer consultation. Explain that practitioners wanted workflow guidance and verifiable evidence, not a generic legal answer. State that review is a design requirement.
- **Transition:** Those constraints demanded a bounded first use case.
- **Source:** Final report §1.2; mid-evaluation slides 7–8.

## 04 · `rta-scope` · Post-certificate RTA matters give the first build a clear boundary

- **On slide:** RTA No. 21 of 1998; post-certificate transactions; no initial title settlement or other registration regimes.
- **Visual/layout:** One highlighted RTA lane among the registration contexts from mid-evaluation slide 19; label other lanes “outside first scope.”
- **Time:** 35 s.
- **Speaking cues:** State why the RTA was chosen: structured, statute-driven workflow. Distinguish post-certificate transactions from historical title compilation and disputes. Avoid implying a universal conveyancing system.
- **Transition:** Existing research and products each address only part of this scoped task.
- **Source:** Final report §§1.1, 1.3, 2; mid-evaluation slides 19–20.

## 05 · `gap` · The unresolved unit is a complete, reviewable matter

- **On slide:** Prior work: legal retrieval, document extraction, form filling. Draftly's question: can these feed one evidence-linked RTA decision path?
- **Visual/layout:** Three narrow columns converging on one matter record. Cite IL-PCSR/LegalBench-RAG and Orbital/Clio as relevant comparators in a small source footer.
- **Time:** 40 s.
- **Speaking cues:** Retrieval benchmarks often judge a relevant passage, while a scenario can need several provisions. Property workflow products already link documents and drafting, so avoid a broad novelty claim. The project tests statutory completeness and implements RTA-specific review controls.
- **Transition:** That gives us two contributions to examine separately.
- **Source:** Final report §2; `current-platform-system.md` related-systems section.

## 06 · `two-contributions` · Draftly contributes a retrieval study and a governed workbench

- **On slide:** **Research:** proposed indispensable-provision benchmark; seven retrievers. **System:** persistent matter, versioned evidence, rule-pack checks, lawyer gates.
- **Visual/layout:** Two linked vertical panels; shared word “provenance” at the join.
- **Time:** 40 s.
- **Speaking cues:** The paper measures a bottleneck; the product controls use of uncertain outputs. Distinguish evaluated methods from live deployment. State that the lawyer decides what is verified.
- **Transition:** Follow a matter through the system first.
- **Source:** Final report abstract and §1.4.

## 07 · `matter-route` · The matter is the unit of work from intake to audit

- **On slide:** Intake → evidence → lawyer verification → checks and research → draft → approval record.
- **Visual/layout:** `../figures/matter-workflow.png`, enlarged and simplified if needed; highlight the human gates.
- **Time:** 55 s.
- **Speaking cues:** Walk the audience through the sequence without presenting an invented client case. The outcome is a recorded decision path, not an autonomous deed. Approval and export are separate events.
- **Transition:** The decisive boundary occurs when a candidate becomes a fact.
- **Source:** Final report §3.2; figure `matter-workflow.png`.

## 08 · `fact-provenance` · A machine candidate cannot silently become a verified fact

- **On slide:** Source hash + evidence location → candidate → lawyer correction/approval → fact version → dependent form.
- **Visual/layout:** Build a clean provenance chain from the final report's conceptual model; small dated synthetic prototype crop may show side-by-side evidence review.
- **Time:** 50 s.
- **Speaking cues:** Original evidence is immutable. A correction creates a new fact version and can stale a downstream draft. Confidence is a hint to review, never an approval.
- **Transition:** These facts live in a deployed, persistent architecture.
- **Source:** Final report §§3.1–3.3, Fig. 3; `current-platform-system.md` evidence section.

## 09 · `deployed-architecture` · The hosted workbench persists matters and uses lexical search

- **On slide:** Next.js + FastAPI + outbox worker; self-hosted PostgreSQL 18; internal BM25 retrieval; source-file volume. MinIO planned.
- **Visual/layout:** `../figures/deployment-demo.png` fitted on one side; current/planned legend large enough to read.
- **Time:** 55 s.
- **Speaking cues:** Name the current VPS components and API-backed matter screens. Explain that the research's hybrid and dense systems are offline results, while the hosted search index is BM25. The stored files are currently on a VPS volume.
- **Transition:** Storage alone does not make scanned evidence trustworthy.
- **Source:** Final report §3.2 architecture; `current-platform-system.md` live deployment.

## 10 · `document-processing` · Document reading stops at reviewable candidates

- **On slide:** Earlier OCR design → hosted intake today → lawyer review. Status line: “OCR path designed; hosted extraction uses a stub.”
- **Visual/layout:** Pair the *upper process stages only* of `../figures/platform-document-processing-v1-pipeline.png` with `../figures/document-processing-current-target.png`. Label the first “earlier design reference” and the second “current hosted boundary”; omit the old GCS/Neon storage lanes from the crop.
- **Time:** 55 s.
- **Speaking cues:** The research pipeline explored multilingual OCR, orientation, grouping, and structured candidate extraction. The hosted service records uploads and processing runs but uses stub candidates. No field-level extraction accuracy is established; review remains mandatory.
- **Transition:** The matter assistant follows the same authority boundary.
- **Source:** Final report §3.4 case law and document reading; figure inventory; `current-platform-system.md`.

## 11 · `agent-boundary` · The assistant proposes; server controls and lawyers decide

- **On slide:** Matter session → allowlisted tools → pending action/abstention → user confirmation. Callout: “No direct model write to verified facts.”
- **Visual/layout:** Cropped central/upper portion of `../figures/platform-matter-agent-service-architecture.png`, labelled “design reference.” Exclude the older Neon/GCS persistence lanes and reserved research-tool box; add a small current-status strip from the platform record.
- **Time:** 50 s.
- **Speaking cues:** The implemented assistant is scoped to a matter and uses an allowlisted tool executor. Consequential proposed actions require confirmation; legal research returns cited material or insufficient authority. This diagram's provider and storage labels are earlier design details, not proof of current deployment.
- **Transition:** The formal controls also appear in the rule pack and draft gates.
- **Source:** `current-platform-system.md` implemented product areas and safety boundaries; named design figure.

## 12 · `rules-and-gates` · Governed rules block unsafe draft progression

- **On slide:** Versioned RTA rule pack; evidence-linked checks; unresolved statutory blockers stop progression; lawyer approval before approved export.
- **Visual/layout:** Four-step gate diagram with one red “stop” path; no hypothetical legal determination.
- **Time:** 45 s.
- **Speaking cues:** A matter pins the rule-pack version used to compile its checklist. Findings prompt review; they do not establish title. Form wording still needs legal verification, so registration-ready export is refused.
- **Transition:** The same concern about incomplete authority motivates the research experiment.
- **Source:** Final report §§3.1, 4; `current-platform-system.md` rule-pack and safety sections.

## 13 · `research-question` · Retrieval must recover the whole indispensable bundle

- **On slide:** Question → proposed required set `{s₁, s₂, …}`. **C@20 = 1** only when *all* required sections are in the first 20 results.
- **Visual/layout:** Simple three-provision illustration clearly marked “metric illustration,” with one omitted provision causing an incomplete result.
- **Time:** 55 s.
- **Speaking cues:** Ordinary top-hit metrics can reward a partial legal answer. Explain complete-indispensable recall at 20 as an all-or-nothing per-question measure. Do not claim the proposed labels are validated legal gold.
- **Transition:** The benchmark makes this question reproducible.
- **Source:** Final report §§2, 5.4; accepted research paper methodology.

## 14 · `benchmark` · A frozen corpus and proposed labels define the experiment

- **On slide:** 52 principal + 60 amending Acts; 4,557 sections; 6,346 typed edges; 50 scenario questions; 40-question test split in 32 matters.
- **Visual/layout:** Corpus-to-question-to-proposed-bundle flow; optional `../figures/research-benchmark-construction-preview.png`, with planned attorney review clearly marked.
- **Time:** 55 s.
- **Speaking cues:** Questions came from Law College examination scenarios. Agent proposals were checked for valid identifiers and verbatim excerpts, which is not legal adjudication. Three-attorney validation remains pending.
- **Transition:** Seven systems then faced the same frozen test.
- **Source:** Final report §3.4 statutory corpus and benchmark; §5.4.

## 15 · `retrievers` · Seven retrievers test lexical, dense, hybrid, and structural routes

- **On slide:** BM25 / field BM25 / dense / hybrid / hybrid + reranker / hierarchical / hierarchical + typed expansion.
- **Visual/layout:** One horizontal family map, grouped by retrieval route; small note “same corpus and questions.”
- **Time:** 55 s.
- **Speaking cues:** Explain BM25 exact terminology, dense semantic matching, rank fusion, Act-first routing, and typed-edge expansion at a conceptual level. The structure-aware system also applies a temporal filter. These are offline comparisons, not seven live product modes.
- **Transition:** The metric reveals mixed winners.
- **Source:** Final report §3.4 retrieval design and Table 4.

## 16 · `retrieval-results` · Observed complete recall peaked at 0.375, with uncertain differences

- **On slide:** C@20: BM25 **0.281**; hybrid **0.344**; hierarchical **0.375**; typed expansion **0.312**. Footer: “40 test questions / 32 matters; provisional labels; offline.”
- **Visual/layout:** `retrieval-c20-results-slide.png` as the primary chart; use a fitted image, not a cropped evidence graphic.
- **Time:** 60 s.
- **Speaking cues:** Hierarchical has the highest observed C@20; hybrid has the highest R@20. Pairwise intervals among leading systems include zero, so avoid winner certainty. Hosted search still uses BM25.
- **Transition:** Aggregate scores hide a sharper failure mode.
- **Source:** Final report Table 4 and Fig. 13; `retrieval-c20-results-slide.png`.

## 17 · `hard-bundles` · No system completed a question needing four or more sections

- **On slide:** **0 / 20** hard test questions completed at C@20; only **2 / 114** missed indispensable sections were one explicit edge from a seed.
- **Visual/layout:** `../figures/report-fig-13-recall-by-bundle-size.png` with a large two-number callout. Caption: “Proposed labels, offline test.”
- **Time:** 60 s.
- **Speaking cues:** The graph can encode valid explicit relationships while failing to connect the provisions a scenario needs. The one-hop analysis explains why adding these edges did not fix completeness. Enriching queries with relevant conditions is a research lead, not a proven deployed gain.
- **Transition:** Return from the offline benchmark to the product assessors can inspect.
- **Source:** Final report §5.4 failure analysis.

## 18 · `product-demo` · A synthetic RTA matter exposes the evidence-to-decision path

- **On slide:** Demonstration path: matter → documents → candidate/fact review → checks → cited research → draft/preflight. Small status line: “Synthetic data; hosted OCR stub; BM25 retrieval.”
- **Visual/layout:** Minimal agenda slide behind the live or recorded app view. Prepare a synthetic matter before the session; use a recorded walkthrough or labelled screenshots if the hosted step fails. Keep any real client files out of the presentation.
- **Time:** 150 s.
- **Speaking cues:** Show that matter and document records persist across screens. Open a candidate with its source and explain where a lawyer verifies or corrects it. Show a finding or preflight refusal and a citation or insufficient-authority state; do not promise an approved export. Identify which visible candidate values are stubbed.
- **Transition:** The demo shows the behavior; the test record shows how much of it was verified.
- **Source:** Final report §§4–5; `current-platform-system.md` implemented areas and limits; `DEMO_RUNBOOK.md`.

## 19 · `evidence-and-gates` · Tests support the controls; legal readiness needs further validation

- **On slide:** **3,906** backend tests passed; **85.4%** backend line coverage; **348** frontend tests passed. Next: attorney labels, document fields, form wording, complete browser journeys.
- **Visual/layout:** Left: compact test evidence. Right: four next validation gates. Footer: “Three browser refusal tests passed for one journey; broader suite had failures.”
- **Time:** 70 s.
- **Speaking cues:** PostgreSQL tests exercised access control, audit, privacy, concurrency, and refusals. The separately run browser suite was not fully passing. Explain that provisional retrieval labels, stub extraction, unapproved wording, and unscored answer correctness limit legal use.
- **Transition:** Close by showing the workstreams that produced the two project outputs.
- **Source:** Final report §§5.2, 5.4, 6; `current-platform-system.md` verification limits.

## 20 · `team-and-takeaway` · Three workstreams delivered one reviewable foundation

- **On slide:** **Himath:** corpus and retrieval evaluation. **Lahiru:** OCR and extraction research. **Praveen:** templates, output flow, lawyer-facing interface. Closing line: “Measured retrieval. Versioned evidence. Lawyer-owned decisions.”
- **Visual/layout:** Three equal contributor columns above one shared project result. Label the ownership split “documented workstreams; final allocation to confirm.”
- **Time:** 50 s.
- **Speaking cues:** Tie each workstream to a concrete artifact already shown, rather than a generic role label. Explain how the streams meet in the matter workflow. End with the bounded contribution and invite questions. Confirm final individual ownership with the team before presenting.
- **Transition:** Q&A.
- **Source:** `.agents/context/CONTEXT.md` team split; final report implementation and conclusion.

## Timing and construction notes

The slide times total **1,080 seconds (18:00)**, exactly 90% of the assumed 20-minute slot, including **2:30** for the final-product demonstration. If the assessment allocates 15 minutes, condense slides 03–06 and 09–11 while preserving the demo and results. Presenter handoffs and final individual ownership need team confirmation. The content here is the `$paper-talk` Phase 1 checkpoint; the deck and full word-for-word script are not yet built.
