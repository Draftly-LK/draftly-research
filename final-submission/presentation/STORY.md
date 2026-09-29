# Draftly final presentation: story treatment

## Brief

- **Audience:** academic project evaluators in data science and engineering.
- **Format:** 20 slides, 16:9. Working assumption: a 20-minute slot, with 18 minutes of planned speech (including a 2:30 demonstration) and two minutes for handovers, pauses, or questions.
- **Thesis:** Draftly connects a measured statutory retrieval problem to a persistent, lawyer-controlled Registration of Title Act (RTA) matter workflow. It makes evidence, proposed facts, legal authority, checks, and professional decisions traceable.
- **Tone:** an academic project account: question, method, implemented artifact, evidence, negative result, and next validation. Avoid a startup sales pitch or claims of legally ready automation.
- **Visual direction for the eventual deck:** `$guizang-ppt-skill` Style B, International Klein Blue preset, with restrained typography, concise claim titles, and large source figures. Keep detailed methods and caveats in presenter notes. This is a visual plan, not a finished deck.

## The through-line

A conveyancer does not begin with an empty form. A matter arrives as a bundle of title and party evidence, while the applicable legal rules may be distributed across principal Acts, amendments, and judgments. A missing provision or an incorrect parcel identifier can change the work. Three practitioner consultations shaped the choice to start with post-certificate RTA transactions rather than claim every land-registration regime.

The presentation then poses two connected questions. **Research:** can retrieval return *every* proposed indispensable provision for a scenario, rather than one plausible hit? **Engineering:** can a workbench keep machine-produced evidence and legal suggestions separate from verified facts and lawyer decisions? The contribution is the combination of a reproducible statutory benchmark and a deployed matter system with explicit review and refusal gates. The presentation should show each contribution on its own evidence.

The audience follows one *generic workflow*, not an invented client case: open an RTA matter; upload evidence; inspect candidate fields alongside their source; verify or correct facts; run governed checks; review cited research; prepare a draft; pass preflight and lawyer approval gates; record export and audit events. This sequence gives the architecture, document pipeline, and agent design a reason to appear. The original document-processing and matter-agent figures supplied for this talk are earlier **design references**. Their Neon and Google Cloud Storage labels are no longer the hosted storage arrangement. Use the cropped process/decision portions with an explicit design-reference caption, then show the current hosted diagram where deployment is discussed.

The research chapter changes the scale from one matter to 50 scenario questions and 112 Acts. Proposed indispensable provision sets become the unit of evaluation. Seven retrievers face the same 40-question, 32-matter test split. The highest observed complete-indispensable recall at 20 was 0.375 for hierarchical retrieval; hybrid fusion recorded 0.344 and typed expansion 0.312. Pairwise uncertainty intervals among the leading systems include zero. More importantly, none completed a test question needing four or more provisions. Only two of 114 sections missed by the structure-aware system were one explicit edge away from a retrieved seed. The negative result explains why adding the available graph edges is insufficient and why fact interpretation and human adjudication remain open research work. The labels are proposed by agents and await attorney review.

Return to the built system for a **demonstration**, then verification. A prepared synthetic RTA matter should show persistent matter and document records, source-linked candidate review, a check or preflight refusal, and cited research or an insufficient-authority response. The demo should expose the difference between a stub candidate and a lawyer-verified fact. A recorded walk-through and labelled screenshots can preserve the same proof points if a live step fails. The hosted platform has API-backed matter records, a PostgreSQL database, an outbox worker, internal BM25 retrieval, rule-pack checks, draft controls, and a reviewable audit trail. The September cycle recorded 3,906 passing backend tests at 85.4% line coverage, 348 passing frontend unit/component tests, and three passing browser refusal tests for one journey. The broader browser suite had failures. Hosted document extraction is stubbed, dense/hybrid retrieval is an offline experiment, and registration-ready form wording has not been signed off. These are precisely the next evaluation targets, not details to conceal.

The closing claim is bounded: Draftly has made the *path to a lawyer decision* inspectable and has measured one important research bottleneck. It has not established that automated document reading, legal answers, or final instruments are attorney-validated. The next phase requires attorney adjudication of provision labels, field-level document evaluation, form wording review, and complete authenticated browser journeys. The final slide maps the team's documented workstreams to these artifacts; confirm the individual allocation before presenting it as final.

## Story beats and handoffs

| Beat | Slides | Audience should understand |
| --- | --- | --- |
| Stakes and scope | 01–05 | Why a legal matter requires more than search or template filling, and why RTA is the bounded first regime. |
| Artifact | 06–12 | How matter evidence, verified facts, governed rules, the assistant, and lawyer gates fit together. |
| Experiment | 13–17 | What was measured, how systems compared, and why the hard provision bundles remain unsolved. |
| Demonstration and delivery | 18–20 | What assessors can inspect in a synthetic matter, what the tests support, what still requires validation, and which team workstreams produced the result. |

## How the marking rubric is made visible

| Criterion (10 points each) | Slides and evidence |
| --- | --- |
| Understanding of the problem and objectives | 02–04: practitioner task, three consultations, bounded post-certificate RTA objective. |
| Quality of analysis and results | 13–17: frozen benchmark, seven-system comparison, uncertainty, hard-bundle and graph-reachability analysis; 19: platform test boundaries. |
| Innovation and creativity | 05–06: precise research and workflow contributions relative to prior work; 08 and 11–12: evidence provenance and controlled agent/draft decisions. |
| Appropriate use of technology and tools | 09–11 and 14–15: deployed stack, designed OCR/agent paths, reproducible corpus, and retrieval methods with current/planned labels. |
| Presentation | One claim per slide, figure-led explanation, 18-minute pacing, and distinct visual status for research, deployed, and planned components. |
| Demonstration of the final product or solution | 18 and `DEMO_RUNBOOK.md`: prepared synthetic matter, persisted data, review control, and a refusal/citation path with a fallback recording. |
| Completeness of allocated tasks | 06 and 20: concrete project outputs and documented Himath/Lahiru/Praveen workstreams, with final ownership confirmation pending. |

## Figure treatment

| Asset | Use in the talk | Status to state aloud or on slide |
| --- | --- | --- |
| `final-submission/figures/platform-document-processing-v1-pipeline.png` | Slide 10, cropped to the process stages and human review; do not display its obsolete storage lanes without context. | Earlier OCR and extraction **design reference**; not the live hosted pipeline. |
| `final-submission/figures/platform-matter-agent-service-architecture.png` | Slide 11, cropped to the turn loop, tool executor, decision band, and service outputs. | Earlier **design reference**; storage/provider labels and reserved research tool are not current deployment claims. |
| `final-submission/figures/deployment-demo.png` | Slide 09. | Current documented VPS layout: self-hosted PostgreSQL, source-file volume, BM25; MinIO planned. |
| `final-submission/figures/document-processing-current-target.png` | Slide 10, paired with the earlier design. | Solid paths are hosted; dashed paths are designed or planned. |
| `final-submission/figures/matter-workflow.png` | Slide 07. | Conceptual lawyer-controlled matter flow. |
| `final-submission/presentation/retrieval-c20-results-slide.png` | Slide 16. | Offline benchmark, provisional labels; never present as hosted search quality. |
| `final-submission/figures/report-fig-13-recall-by-bundle-size.png` | Slide 17. | Offline benchmark, provisional labels. |

## Source and claim boundaries

The content is grounded primarily in `final-submission/final-report.tex`, `final-submission/current-platform-system.md`, the figure inventory `final-submission/figures/README.md`, the documented team split in `.agents/context/CONTEXT.md`, and the mid-evaluation deck. The Google Slides draft URL provided by the user was inaccessible to the available browser and web tools, so its wording has not been reused. The mid-evaluation deck is a source for the original domain argument and project framing; its older corpus, implementation, and evaluation status is replaced by the September final report.

The platform and retrieval study have different evidence. **Offline** hybrid and hierarchical scores do not describe the hosted **BM25** index. Passing service tests do not establish end-to-end legal correctness. The held-out case-law extraction and multilingual OCR work are supporting research streams, not attorney-validated production capabilities. Only synthetic matter data is within the hosted demo's current operating policy.

## Checkpoint

This story and `SLIDE_OUTLINE.md` are the Phase 1 content checkpoint. The `$paper-talk` skill sets `AUTO_PROCEED = false` and calls for review of the outline before deck construction. The user also asked to write the story first. Build the HTML/PPTX, full talk script, and visual QA only after the content direction is approved or revised.
