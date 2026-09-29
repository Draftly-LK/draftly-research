# Draftly: Grounded Legal Retrieval and a Lawyer-Controlled Conveyancing Matter Workflow for Sri Lanka

## Abstract

Preparing a land transaction in Sri Lanka requires a notary to reconcile property evidence, locate the law that applied on the relevant date, and record decisions that remain the lawyer's responsibility. These tasks are spread across scanned matter documents, principal and amending Acts, gazetted material, and judgments. Draftly combines a statutory retrieval study with a matter-centred workbench for post-certificate transactions under the Registration of Title Act. The research built a deterministic corpus of 52 principal and 60 amending Acts, containing 4,557 sections and 6,346 typed relationships. A benchmark of 50 Law College scenario questions mapped each question to the provisions proposed as indispensable to a complete answer. Seven retrieval systems were tested on a 40-question, 32-matter test split. Hierarchical retrieval reached complete-indispensable recall at 20 of 0.375, hybrid lexical and dense fusion reached 0.344, and the tested structure-aware variant reached 0.312; the reported pairwise intervals among these systems include zero. No system completed a test question requiring four or more provisions. The platform implements matter records, evidence-linked candidate facts, a governed Registration of Title Act rule pack, deterministic checks, research citations, audit history, and human decision gates. Its September test cycle recorded 3,906 passing backend tests at 85.4 percent line coverage, while also identifying gaps in browser testing. The deployed system is a synthetic-data demonstration with lexical-only retrieval and stub document extraction. Its form wording has not been legally approved, so a registration-ready export remains blocked. Benchmark labels and extracted case-law rules also await attorney review. The outcome is an evaluated retrieval foundation and a tested, lawyer-controlled matter workflow, with a clear boundary between demonstrated software behaviour and legal validation still required.

## 1 Introduction

### 1.1 Background of the Application Domain

Conveyancing involves establishing the legal position of land and parties before a transaction is prepared, executed, attested, and registered. A notary may need to compare a title certificate with a cadastral plan, identify registered interests, check the parties' capacity, determine the applicable instrument and prescribed particulars, and find the statutory provisions governing each step. The same matter can contain scanned documents in Sinhala, Tamil, and English. The law is spread across principal enactments, amendments, regulations, and judgments. Draftly begins with post-certificate transactions under the Registration of Title Act, No. 21 of 1998 [1]. This bounded regime allowed the team to model a concrete matter workflow while recording where other registration regimes would need different rules and forms.

### 1.2 Motivation

Three consultations with lawyers and legal experts, recorded in the mid-evaluation materials, described how junior practitioners assemble legal authority and client evidence across several publishers and formats. The difficulty is more than locating a document. A partial answer can look well supported while omitting a definition, exception, or procedural provision on which the transaction turns. The corpus assembled for this project contains 112 principal and amending Acts. In the separate case-law linking work, some judgments refer to statutory provisions that changed after the decision, which also makes the date of the question material. Scanned evidence creates another source of uncertainty: reading a parcel identifier incorrectly can change the subject of the matter. These observations motivated two linked tasks: measure whether retrieval supplies complete statutory authority, and make every machine-produced candidate reviewable in a lawyer-owned workflow.

### 1.3 Purpose and Scope

The project purpose is to support a conveyancing matter from legal research and document intake through evidence review, checks, and recorded professional decisions. The system is designed to present citations and evidence spans, keep machine outputs unverified, require a lawyer to resolve consequential findings, and retain an audit history. The research paper accepted at the NeurIPS 2026 GlobalSouthAI workshop studies one part of that purpose: retrieval of every indispensable statutory provision for a scenario question [2]. The software platform addresses the surrounding matter workflow. Draft generation exists as an experimental downstream component, but the legal wording of its forms has not been verified and a registration-ready export is not a demonstrated project outcome.

### 1.4 Approach and Outcome

The work ran in two repositories. The research repository built the legal corpus, case-law and document-processing pipelines, benchmark, retrieval experiments, and retrieval service. The platform repository built the web workbench, backend domain services, rule-pack governance, persistence, background jobs, audit controls, and a synthetic-data deployment. The measured retrieval result guided the engine design but should not be mistaken for the configuration currently deployed: the live demo uses a lexical index, while dense fusion remains a research configuration. The main outcomes are a versioned benchmark with provisional labels, a reported comparison of seven retrievers, a working matter-centred demonstration, and test evidence for the platform's safety rules. Legal validation, document-field accuracy, and a complete approved export remain open.

## 2 Literature Review

Prior legal retrieval work often scores individual cases or passages. IL-PCSR retrieves cases and statutes jointly from Indian judgments [3], while LegalBench-RAG evaluates the passages supplied to legal question answering [4]. Scenario-based statutory resources expose a harder setting because a question may use language unlike the governing text [5]. KoBLEX includes multi-hop, provision-grounded legal questions [6], GreekBarRetrieval pairs bar-examination questions with officially cited articles [7], and recent work investigates structure-aware [8] and temporal [9] statutory retrieval. These resources informed the decision to score a complete set of required provisions rather than a single relevant hit.

For Sri Lankan law, LawChain combines lexical, dense, and graph retrieval over Acts, but its reported questions are generated from legislative text and require one provision each [10]. Other local work has used retrieval-augmented generation for legal guidance [11] or trained case-law embeddings without a section-level statutory benchmark [12]. These tasks differ from a conveyancing scenario in which several provisions may jointly govern the answer. Draftly's research contribution is a benchmark that marks proposed indispensable provisions separately from supporting material, together with a complete-indispensable recall measure and matched retrieval comparisons. The platform contribution is the controlled use of legal authority and matter evidence in a workflow that leaves decisions to the lawyer.

The retrieval design uses BM25 as a lexical baseline [13], BGE embeddings for semantic matching [14], reciprocal rank fusion to combine ranking channels [15], a compact cross-encoder for one reranking variant [16], [17], and document-then-passage routing inspired by hierarchical retrieval [18]. These methods were tested rather than assumed to improve legal completeness. The benchmark found that the graph edges used in this project did not supply most of the missing provisions, so the final analysis treats structure-aware expansion as a measured negative result, not a product advantage.

## 3 System Models

### 3.1 System Requirements

The matter workflow must let an authorised user create and classify a Registration of Title Act matter, upload source documents, inspect a candidate fact beside its evidence, verify or correct it, and run rule-pack checks. A lawyer must be able to resolve or waive a finding with a reason, inspect cited statutory passages, and review the audit history. Legal-content administrators govern the rule pack and its source status. Draft and export services must refuse unsafe transitions; their existence does not establish that the legal instrument itself has been validated. Fig. 1 shows the main actors and operations. The lawyer retains verification and approval authority, the clerk prepares material, and the content administrator governs rules.

[[FIG:report-fig-01-use-cases.png|Fig. 1. Main use cases and human authority in the Draftly workbench. This is a system-design view.]]

The principal quality requirements follow from this authority boundary. Organisation and matter isolation must be enforced on the server. Original evidence must remain immutable; corrections create new fact versions. Machine confidence cannot make a value verified, and a later correction must invalidate dependent work. Research must return cited material or state that authority is insufficient. The system records material mutations in an append-only, hash-chained audit log. These are engineering requirements tested at the service and database layers; they do not certify any legal answer or document wording.

### 3.2 System Design

#### 3.2.1 Architecture

Draftly uses a Next.js browser workbench and a FastAPI backend arranged as domain modules. The backend stores matter data in PostgreSQL and processes asynchronous work through an outbox worker. It calls a separate retrieval service over the internal network. The demonstration deployment uses Caddy for TLS and routing, Clerk for sign-in, a BM25 lexical index in the retrieval container, and Gemini for approved research-answer composition. Document extraction remains on a stub provider in that deployment. Fig. 2 depicts the observed demo configuration; it deliberately separates that configuration from the wider provider-neutral design and the hybrid system evaluated in the paper [19]–[23].

[[FIG:deployment-demo.png|Fig. 2. Synthetic-data demonstration deployment as recorded in September 2026. Document extraction is stubbed and the internal retrieval index is lexical only.]]

The domain modules follow a fixed dependency direction: an API router calls an application service, that service applies domain policy through a port, and infrastructure adapters provide storage or external integrations. This permits a rule about verification or approval to be tested without depending on a browser screen. It also prevents a retrieval or model response from writing an authoritative fact directly.

#### 3.2.2 Logical and Process Views

A Matter scopes Parties, SourceFiles, candidate ExtractedFacts, EvidenceReferences, ReviewDecisions, Findings, and AuditEvents. A candidate is supported by a file hash and location in the evidence. A correction supersedes the previous fact instead of silently replacing it. ResearchClaims link to ResearchCitations; requirements and checks are instantiated from a versioned RulePack. The conceptual associations appear in Fig. 3. The diagram includes downstream draft and approval classes because the schema and refusal gates exist, although no legally verified form is available for a complete export.

[[FIG:report-fig-03-domain-classes.png|Fig. 3. Conceptual classes connecting a matter, evidence, review decisions, governed rules, research citations, and downstream controls.]]

Fig. 4 follows a transfer matter. A user creates the matter and supplies documents; processing produces candidates; the lawyer verifies or corrects them; rule-pack checks surface mismatches and missing evidence; and the lawyer records a resolution. The final part of the diagram is a designed gate: a draft may be prepared for review only under its prerequisites, and approved export remains unavailable while prescribed wording lacks legal verification. The process therefore ends at an explicit human decision rather than silently promoting machine output.

[[FIG:report-fig-04-rta-transfer-activity.png|Fig. 4. Designed Registration of Title Act matter activity with lawyer review and blocking checks. The approved-export path awaits legal verification of form wording.]]

### 3.3 Database Design

The database separates source evidence, derived candidates, lawyer decisions, governed content, and audit records. Fig. 5 shows the core relations. A source file carries a content hash; a derived file points to its origin, preserving the original. An extracted fact records source provenance and version. Review decisions store who accepted or corrected a value and the reason. Findings remain separate from facts so a detected mismatch cannot itself resolve the matter. Audit events link to the preceding event hash. Optimistic version fields reject stale writes, and the transactional outbox lets work resume after a worker interruption. The database and migrations were tested on PostgreSQL rather than only on an in-memory substitute [21].

[[FIG:report-fig-05-core-er.png|Fig. 5. Core matter and research entity relationships. Solid lines represent database foreign keys; dashed lines represent logical references.]]

The research data has a different storage pattern. Structured Acts, sections, provisions, and typed edges are held in versioned JSON Lines with a corpus fingerprint and per-file hashes. The retrieval index uses SQLite FTS5 for lexical search. A changed corpus fingerprint causes a rebuild rather than reusing an old index. This separation lets the paper's frozen benchmark be inspected without treating provisional research labels as authoritative matter data.

### 3.4 Machine Learning and Data Science System Design

#### 3.4.1 Statutory Corpus and Benchmark

The research corpus contains 52 principal enactments and 60 amending Acts, 4,557 sections, 17,854 sub-section provisions, and 6,346 typed edges. Edges encode definitions, exceptions, qualifications, procedural requirements, cross-references, and amendments. The 16 Law College examination papers were split into 667 atomic questions. After eligibility review and two-agent annotation, 50 statute-only questions in 40 matters formed the scored benchmark, with 84 distinct provisions proposed as indispensable. A deterministic validator checked section identifiers and verbatim excerpts. This verifies that a label points to text in the frozen corpus; it does not establish that the provision is legally indispensable. The planned three-attorney validation has not run.

#### 3.4.2 Retrieval and Grounded Research

Seven retrievers share the same questions and corpus. The lexical systems use ordinary and field-weighted BM25. Dense retrieval ranks overlapping windows of long sections. Hybrid retrieval fuses lexical and dense ranks. A further variant reranks candidates with a cross-encoder. Hierarchical retrieval first selects likely Acts, while the structure-aware variant expands selected section seeds along typed edges and applies a temporal filter. Fig. 6 shows the corpus, tested alternatives, and the all-or-nothing evaluation rule. It is a research diagram, not a diagram of the currently deployed lexical index.

[[FIG:research-corpus-retrieval-paperbanana.png|Fig. 6. Frozen statutory corpus and retrieval systems evaluated in the research paper; the proposed indispensable bundle defines a complete result.]]

The research-answer path composes an answer from retrieved passages and requires each emitted claim to name a returned authority identifier. It rejects claims with citations outside that returned set and abstains when the engine supplies no usable authority. The platform also turns retrieval timeouts into an insufficient-authority response. These checks limit unsupported output but do not prove the legal correctness of an answer; the answer-generation stage has not received attorney scoring.

#### 3.4.3 Case Law and Document Reading

A deterministic headnote reader recovered a verbatim rule from 3,521 of 3,703 reported judgments. Cases it could not parse, and unreported judgments, entered a bounded model-assisted route using Llama 3.1 8B through NVIDIA NIM. That route required a quotation occurring verbatim in the judgment and rejected section references outside a closed catalogue [24], [25]. A held-out evaluation found that the accepted output was still below the project's usability threshold, so extracted rules remain unverified. Case-law ranking is not part of the scored statutory benchmark.

For scanned matter documents, the research team compared OCR engines on multilingual pages and chose Google Cloud Vision for the pipeline design [22]. The pipeline checks page quality and orientation, groups pages into logical documents, and produces string-valued candidate fields for human review. Sinhala and Tamil character recovery and page rotation were observed, but field-level accuracy has not been established: the paid extraction evaluation did not complete, and only one matter had a small set of labelled fields. The deployed demo uses stub extraction. This distinction keeps a research pipeline design from becoming an unsupported claim about live matter processing.

## 4 System Implementation

### 4.1 Implementation Procedure

The research code is written in Python and uses deterministic corpus builds, content hashes, versioned experiment configurations, and stored per-question rankings. Its retrieval service exposes a bounded search interface to the platform. The benchmark systems were run on a laptop processor, with identical test questions and corpus inputs across configurations. Corpus and split fingerprints, software versions, and run manifests were recorded so that a score refers to one frozen build. The public release contains the benchmark questions and provisional labels with a small evaluator; it does not include the frozen full-text corpus or all retrieval implementations, so publication of the labels alone does not reproduce the paper's experiment.

The platform backend uses FastAPI, SQLAlchemy, Alembic and PostgreSQL; its frontend uses Next.js, React and TypeScript [19]–[21]. Domain rules are implemented in services rather than in screen components. A server-side tenancy boundary protects each organisation's matters. Facts are promoted through explicit review decisions, while the content-governance service records where each workflow requirement came from. An outbox worker claims jobs with leases and retries, and a hash-chained audit log records material actions. The frontend provides matter, document, facts, workflow, checks and research views in English and Sinhala. A Docker Compose stack deploys a synthetic demonstration on one virtual private server. A research-service failure produces an insufficient-authority response. The single-server and demo-mode provider decisions limit claims about production readiness.

The Registration of Title Act rule pack is versioned data. Its exported contract records nine transaction families, 33 matter subtypes, 145 checklist requirements, 25 deterministic checks, 52 document classes, and 32 form templates. Each requirement identifies a source class so that an Act obligation can be distinguished from registry operations or professional practice. The form templates are transcriptions awaiting legal verification. The current implementation tests their refusal gates, not the substantive accuracy of a completed legal document.

Table 1. Implemented areas and their demonstrated boundary.

| Area | Demonstrated work | Boundary |
| --- | --- | --- |
| Legal corpus and benchmark | Deterministic build, proposed provision labels and seven-system comparison | Attorney validation pending |
| Research interface | Retrieved passages, citation identifiers and abstention on unavailable authority | Answer correctness not lawyer-scored |
| Matter workbench | Matter records, evidence-linked candidates, rule-pack steps, findings and audit | Demo uses synthetic data |
| Document processing | Multilingual OCR pipeline and engine comparison in research | Deployed extraction is stub; field accuracy unmeasured |
| Draft controls | Review and export refusal rules | Form wording unverified; no registration-ready export |

### 4.2 Materials

The research corpus was assembled from Sri Lankan statutes and amending Acts available through official and republisher sources. Reported judgments came from the CommonLII archive of the New Law Reports and Sri Lanka Law Reports; official court material supplied unreported judgments. The benchmark questions came from sixteen Sri Lanka Law College conveyancing examinations, which were structured into 667 atomic questions. The rule pack cites ten governed sources across law, regulation, registry operations, local-authority operations, professional practice, product rules, and material awaiting verification. Scanned conveyancing documents used in document-reading experiments contain personal information, so this report gives aggregate characteristics only and does not reproduce their pages, identifiers or OCR overlays. Synthetic matter data supplies the platform demonstration and interface figures.

Table 2. Materials and their role in the project.

| Material | Scale or format | Use and restriction |
| --- | --- | --- |
| Statutes and amendments | 52 principal and 60 amending Acts in the frozen benchmark corpus | Section retrieval and typed relationships; structural checks do not equal legal approval |
| Law College questions | 16 papers, 667 atomic questions, 50 scored questions | Proposed benchmark labels; attorney validation pending |
| Reported judgments | 3,703 CommonLII full-text judgments | Headnote rule recovery; outputs unverified |
| Unreported judgments | 5,474 Supreme Court and Court of Appeal documents | Bounded extraction and linking; no lawyer-verified rule set |
| Registration of Title Act rule pack | Ten governed sources, version 1.0.0 | Checklist and checks; form wording unverified |
| Matter documents | Scanned PDF and image files held outside public outputs | OCR research in aggregate only; no client material in figures |

### 4.3 The Algorithms

The first algorithm tested whether statutory relationships improve the retrieval of complete provision sets. It begins with lexical and dense rankings, routes the query to a small set of Acts, and takes high-ranked sections as seeds. It then adds sections linked by enabled edge types, removes material outside the question's reference date, and reranks the candidates. Fig. 7 gives the essential procedure without implementation code. The temporal step measures one useful control, although the tested edge expansion did not improve complete recall against the strongest comparison methods.

[[ALGO:RETRIEVE]]

The second procedure is the research answer boundary. Returned passages become an allowlist of authority identifiers. A generated claim is retained only if it points to an identifier in that allowlist; failure to retrieve material or to retain a cited claim results in an abstention. Fig. 8 shows that control. It is a provenance check rather than a legal-validity test. A lawyer still needs to inspect the cited provision and the proposed interpretation.

[[ALGO:ANSWER]]

### 4.4 Main Interfaces

The interface follows the order of a matter rather than opening with a general chatbot. A matter holds documents, facts, workflow steps, checks, research and activity history. Fig. 9 shows a July 2026 synthetic prototype of the fact-review view: candidates have status, confidence, source page and a separate verification action. The side-by-side evidence area makes it possible to compare conflicting values before a lawyer chooses one. This figure demonstrates interface design; it does not establish OCR accuracy or current live-screen fidelity.

[[FIG:ui-prototype-fact-review.png|Fig. 9. Fact-review prototype with synthetic matter data, captured 22 July 2026. The evidence panel and verification controls are interface examples.]]

Fig. 10 shows the corresponding checks view. It groups missing evidence and conflicting particulars, states the source or affected fact, and offers a recorded resolution or waiver. A check finding is a prompt for review, not a determination of title. The screenshot is a dated synthetic prototype, so the final testing claims below are taken from the September backend and browser suites rather than inferred from the image.

[[FIG:ui-prototype-checks.png|Fig. 10. Checks prototype with synthetic matter data, captured 22 July 2026. Findings require a lawyer-owned response.]]

The implemented research view returns cited passages or an explicit insufficient-authority state. Draft-related screens and services also exist, but their form wording lacks legal approval; they are therefore treated as a partial downstream experiment rather than the outcome on which this report rests. The platform test report records that the full approved-export journey was stopped at that gate.

## 5 System Testing and Analysis

### 5.1 Testing Approach

Testing targeted each rule at the layer that enforces it. Domain policies were unit-tested, repositories and service transactions were tested against PostgreSQL, and route sweeps checked organisation isolation, concurrency conditions and API conventions. The frontend logic and components were tested with Vitest; browser tests exercised selected refusal behaviour with Playwright. Synthetic data was used throughout. The platform test report records the scope and deviations: full authenticated browser journeys, load and failover tests, external paid-service runs, and lawyer acceptance tests were not completed in that cycle. A full approved export could not be used as a happy-path test because no prescribed template had been legally verified.

### 5.2 Platform Test Results

The dated backend and frontend runs on 19 September 2026 collected 3,922 backend tests, of which 3,906 passed, ten were expected failures, one was skipped, and five live-service tests were excluded. All 348 frontend unit and component tests passed. Three refusal tests covering one browser journey passed. These figures do not mean that the entire browser suite passed: the separate 20 September single-worker run recorded four passed, nine failed and two skipped across the older and new browser tests. Table 3 keeps the results and coverage boundaries separate.

Table 3. Platform test execution and coverage recorded in September 2026.

| Measure | Recorded result | Interpretation |
| --- | --- | --- |
| Backend pytest | 3,906 passed; 0 failed; 10 expected failures; 1 skipped; 5 live tests excluded | Real PostgreSQL used for database and security suites |
| Frontend Vitest | 348 passed | Logic-layer coverage 93.3%; whole frontend line coverage 27.0% |
| Browser refusal tests | 3 passed for one journey | Whole browser suite had other failures and was not in CI |
| Backend coverage | 85.4% lines; 63.9% branches | Line target met; branch target of 70% not met |
| Defects found and fixed | 15, including 2 critical | 12 appeared only with real PostgreSQL behaviour |

The seven named safety rules were traced to passing tests: cross-organisation isolation, material-action audit, privacy of client identifiers at rest, role and capability enforcement, consistent API behaviour, reliable outbox delivery, and quota accounting. A forged pagination cursor and malformed webhook were also tested as refusals. Hash-chain concurrency testing found and fixed a case in which two writers could fork an audit log. These results support the engineering boundaries of the workbench; they do not certify legal correctness, field extraction, or the wording of an instrument.

### 5.3 Performance, Security and Failure Behaviour

On the research laptop, the BM25 retrieval baseline took about 16 ms per query, hybrid fusion 17 ms, the structure-aware system about 0.9 s, and the cross-encoder variant about 6.8 s. These are experiment measurements on a fixed corpus and processor, not end-to-end response times of the deployed web application. The deployment record describes a single virtual private server and a lexical-only retrieval index. If that service is unreachable, the research path returns insufficient authority. The same record states that document extraction is stubbed and that the deployment remains limited to synthetic data. The platform test plan included load, failover and real-client use only as later work.

### 5.4 Evaluation of Machine Learning and Data Science Components

Retrieval was scored on 40 test questions grouped into 32 matters. Indispensable recall at 20, R@20, averages the fraction of each question's indispensable sections retrieved. Complete-indispensable recall at 20, C@20, credits a question only when all of its indispensable sections appear in the first 20 results. Question scores were averaged within each matter and then across matters; 95 percent intervals used 2,000 matter-level bootstrap resamples. All labels are agent-produced proposed gold and remain subject to attorney review. Table 4 reports the seven main systems.

Table 4. Main-test retrieval results (matter-macro means; proposed labels).

| System | R@20 | C@10 | C@20 | MRR | Act@10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| BM25 | 0.491 | 0.250 | 0.281 | 0.503 | 0.719 |
| Field-weighted BM25 | 0.482 | 0.250 | 0.281 | 0.540 | 0.672 |
| Dense BGE | 0.379 | 0.125 | 0.188 | 0.316 | 0.562 |
| Hybrid rank fusion | 0.546 | 0.266 | 0.344 | 0.543 | 0.625 |
| Hybrid plus cross-encoder | 0.413 | 0.125 | 0.234 | 0.223 | 0.562 |
| Hierarchical | 0.496 | 0.297 | 0.375 | 0.509 | 0.469 |
| Hierarchical plus typed expansion | 0.480 | 0.281 | 0.312 | 0.495 | 0.469 |

Hybrid fusion produced the highest R@20 and MRR, whereas hierarchical retrieval had the highest observed C@20 and BM25 had the highest Act@10. The paired C@20 differences among hybrid, hierarchical and structure-aware retrieval were uncertain on this small test split; the structure-aware minus hybrid difference was −0.031 with a 95 percent interval from −0.156 to +0.078. The cross-encoder variant reduced MRR from 0.543 to 0.223. The structure-aware temporal filter removed out-of-force sections from its top ten results, while the flat systems retained some; this is a tested filtering result rather than a claim that all historical law is represented perfectly. Fig. 11 shows why aggregate recall hides the hardest questions: no system completed any of the 20 test questions requiring four or more indispensable sections.

[[FIG:report-fig-13-recall-by-bundle-size.png|Fig. 11. C@20 by the number of indispensable sections on the 40-question test split; all provision labels are provisional.]]

Only two of the 114 indispensable sections missed by the structure-aware system were reachable by a single typed edge from a retrieved seed. The graph therefore lacks most of the dependencies a complete answer needs, even when its edges are valid descriptions of explicit textual relationships. Scenarios enriched with relevant conditions scored better than the original wording, which suggests that identifying legally operative facts may matter more than adding more of the same one-hop edges. This remains a research inference, not a proven improvement in the deployed platform.

The case-law extraction study accepted 74 of 100 held-out cases under the quote-grounding gate. A language-model judge, used only as a provisional proxy, rated 58.1 percent of those accepted rules fully usable, below the pre-registered 90 percent threshold. No extracted rule has been signed off by a lawyer. The multilingual OCR comparison informed the design choice, but the field-level extraction experiment could not be scored after paid runs failed on credentials. Accordingly, this report makes no field-accuracy claim. Answer generation itself has not been graded for legal correctness. These gaps define the boundary of the evaluation rather than being filled with assumptions from a working interface.

## 6 Conclusion and Future Work

Draftly addressed a practical conveyancing problem: a lawyer must reconcile evidence and find the complete, applicable legal authority before making a professional decision. The project produced a structured statutory corpus and a provisional scenario benchmark, tested seven retrieval systems, and built a matter-centred workbench that keeps candidates, citations, checks and human decisions separate. The measured retrieval result was mixed. Hybrid fusion improved average indispensable recall, hierarchical retrieval recorded the highest observed complete recall, and the tested typed-edge expansion did not improve completeness. Most missed provisions lacked an explicit one-hop relationship to a retrieved seed. Temporal filtering removed out-of-force sections in the tested ranking, while no system completed a question needing four or more provisions.

The platform's strongest demonstrated outcome is controlled workflow behaviour on synthetic data. Real PostgreSQL tests exercised tenancy, audit, privacy, concurrency and refusal gates, and the deployed demo connects the interface, API, database, worker and internal lexical search. The work has not yet demonstrated a legally approved instrument, validated extraction of client-document fields, or attorney-scored legal answers. The form templates remain unverified, the demo's extraction provider is stubbed, the browser suite has unresolved failures, and the benchmark labels are provisional. Future work should first complete attorney review of the proposed indispensable provisions and legal content, then re-score retrieval and evaluate document fields on an approved holdout. It should also connect and test the dense retrieval channel in deployment, finish authenticated browser journeys, and seek legal approval for prescribed-form wording before attempting a registration-ready export.

## References

The numbered reference list is copied from the existing draft report, with the accepted paper's author line and status corrected in the delivered DOCX.
