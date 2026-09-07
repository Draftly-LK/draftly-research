You are the lead research engineer responsible for building and evaluating a statute-grounded Sri Lankan legal QA benchmark for a four-page research paper.

Read this entire brief before acting.

# 1. Research objective

The proposed paper is narrowly focused on statutory information retrieval:

> Can hierarchical and structure-aware retrieval improve the retrieval of legally indispensable statutory provisions for scenario-based questions in a low-resource jurisdiction?

Possible paper title:

> Evidence-Grounded Statutory Information Retrieval for a Low-Resource Jurisdiction: A Sri Lankan Case Study

The project has three intended contributions:

1. A structured Sri Lankan statutory corpus connecting enactments, provisions, amendments, temporal versions and cross-references.
2. A lawyer-validated scenario-based legal QA benchmark with gold Acts, provisions, indispensable statutory authorities and claim-level provenance.
3. A hierarchical hybrid retrieval method that identifies the relevant Act before retrieving provisions.

This short paper does not evaluate:

* Case-law retrieval
* Common-law or Roman-Dutch-law retrieval
* Case-rule extraction
* Judgment-holding extraction
* OCR
* Client-document processing
* Synthetic legal document generation
* The complete Draftly platform

Do not add those components to the core experiment.

Case-law-dependent questions may be detected and reserved, but they must not be included in the main statute-only benchmark.

# 2. Existing inputs

The existing past-paper dataset contains 667 atomic questions.

The classification summary currently reports:

```text
keep: 119
enrich: 91
review: 50
drop_candidate: 399
repair: 8
```

The candidate pool for this project is:

```text
keep + enrich = 210 candidate atomic questions
```

Expected approximate structure previously observed:

```text
210 candidates
133 potential matter/background units

Clean, high-confidence subset:
84 keep questions
60 enrich questions
144 total questions
approximately 92 matter/background units
```

Verify every count from the actual files. Do not hardcode these numbers or force the data to match them.

The classification output is currently marked `unverified`. A validation-problem count of zero means only that structural validation passed. It does not mean the classifications, legal issues or answers were validated by a lawyer.

# 3. First inspect the repository

Before editing anything:

1. Read every applicable `CLAUDE.md`, `AGENTS.md` and repository instruction.

2. Locate the actual paths of:

   * `atomic-questions.jsonl`
   * `atomic-classifications.jsonl`
   * `selected-matters.jsonl`, if already generated
   * Statute registry
   * Finalized statute trees
   * Finalized statute source packages
   * Amendment data
   * Temporal provision data
   * Cross-reference data
   * Existing BM25 indexes
   * Dense retrieval code
   * Existing evaluation datasets
   * Existing retrieval and evaluation scripts

3. Inspect the current repository state and preserve unrelated user changes.

4. Do not overwrite source datasets.

5. Audit the statutory corpus before claiming its size.

Do not describe the corpus as containing “200 laws” unless the repository audit demonstrates that count and clearly defines whether it means:

* Enactments
* Amendment Acts
* Source documents
* Parsed trees
* Consolidated Acts
* Individual provisions

Report separate counts.

# 4. Overall pipeline

Implement this pipeline:

```text
667 atomic questions
→ Select 210 keep/enrich candidates
→ Data-quality and matter-boundary review
→ Identify statutory legal issue
→ Classify authority requirement
→ Exclude case-dependent questions from main benchmark
→ Find candidate Acts and provisions
→ Verify exact provision text and temporal version
→ Determine indispensable provisions
→ Enrich minimal scenarios using legally controlled facts
→ Draft claim-supported gold answer
→ Independent verification
→ Lawyer-review packet
→ Freeze lawyer-approved gold set
→ Run retrieval baselines
→ Evaluate indispensable-provision retrieval
→ Produce tables, figures and error analysis
```

Do not run retrieval evaluation against unverified gold labels.

# 5. Candidate selection

Select records where:

```python
candidate_action in {"keep", "enrich"}
```

Preserve all 210 as the broad candidate pool, subject to verification.

Create two queues.

## Tier A: immediate processing

```python
candidate_action in {"keep", "enrich"}
and extraction_quality == "clean"
and confidence >= 0.80
and context_dependency in {"required", "partial"}
```

Expected approximate count:

```text
144 questions
```

## Tier B: manual review

All remaining `keep` and `enrich` questions.

Expected approximate count:

```text
66 questions
```

Tier B records must not enter the gold dataset automatically. Their OCR, background boundaries, question boundaries and inherited context must be reviewed first.

Do not include:

* `drop_candidate`
* `repair`
* `review`

unless a later manual repair produces a new, explicitly reviewed record.

# 6. Matter-level grouping

Questions sharing the same factual background belong to the same matter.

Use the existing `matter_id` where reliable.

If `matter_id` is missing:

```python
grouping_key = "atomic:" + atomic_id
```

Never split questions sharing a background across research agents, dataset partitions or bootstrap samples.

Preserve:

* Original matter ID
* Benchmark matter ID
* Atomic IDs
* Paper number
* Question number
* Part identifiers
* PDF page
* Source quotation
* Original background
* Original question
* Classification metadata

The final number of matters must be derived from the data. Do not continue calling it a 44-matter dataset after including the enrichment pool.

# 7. Authority-requirement classification

Before performing detailed gold annotation, classify every candidate:

```text
statute_only
mixed_statute_and_case
case_only
unclear
```

Definitions:

* `statute_only`: A complete legally supported answer can be produced using verified statutory provisions.
* `mixed_statute_and_case`: Statutes are relevant, but a complete answer also requires judicial authority or a non-statutory doctrine.
* `case_only`: The answer principally depends on case law or non-statutory doctrine.
* `unclear`: Available evidence is insufficient to classify it.

The main benchmark may contain only:

```text
statute_only
```

Store other questions in reserve files:

```text
reserved-mixed.jsonl
reserved-case-only.jsonl
reserved-unclear.jsonl
```

Do not research or annotate gold cases in this project.

If a question explicitly requests case law, depends on precedent, or cannot be answered completely from verified statutes, reserve it.

Do not pretend that a statute-only answer is complete when case authority is indispensable.

# 8. Multi-agent orchestration

Use subagents for bounded, independent research tasks. Do not use one giant prompt for all questions.

## Main orchestrator

The main Claude Code agent must:

* Read repository instructions itself.
* Audit inputs and sources.
* Define schemas.
* Select pilot matters.
* Assign matter-level tasks.
* Validate subagent results.
* Merge outputs.
* Run deterministic checks.
* Maintain manifests.
* Prevent concurrent writes to shared files.
* Present the pilot results.

Only the main orchestrator may modify aggregate JSONL files.

## Data-curation agent

Use one subagent for:

* Checking question/background boundaries
* Reviewing Tier B items
* Detecting duplicate or near-duplicate questions
* Checking matter grouping
* Identifying malformed OCR
* Checking whether an enrichment candidate has enough stable legal intent

This agent must not research legal answers.

## Primary statute-research agents

Assign each complete matter to one primary statute-research agent.

Each agent receives:

* Matter background
* All questions belonging to that matter
* Source quotations
* Relevant corpus-search tools
* Required output schema

Partition work by matter, not by individual question.

Use no more than four legal-research agents concurrently unless the environment demonstrably supports more without rate limits or output inconsistency.

Each researcher writes only to its assigned per-matter directory.

## Independent authority-verification agents

Every proposed gold Act and provision must be checked by a different agent.

A primary researcher cannot verify its own proposed authorities.

The verifier checks:

* Formal enactment title
* Act, Ordinance or Law number and year
* Section and subsection
* Exact wording
* Applicable temporal version
* Amendment history
* Whether the provision supports the proposed claim
* Whether it is indispensable or merely supporting
* Whether relevant definitions or cross-references were omitted

Verification decisions:

```text
verified
partially_verified
rejected
unresolved
```

A rejected or unresolved indispensable provision blocks the question from the gold set.

## Scenario-enrichment agents

Use these agents only for questions classified `enrich`, and only after candidate statutory provisions have been identified.

They may add:

* Fictional party names
* Fictional property addresses
* Controlled dates
* Instrument identifiers
* Transaction ordering
* Capacity information
* Registration status
* Other missing fact categories identified in classification

Every addition must be labelled:

```text
synthetic_neutral
synthetic_decisive
```

A decisive addition requires an explanation of:

* Why it is necessary
* Which legal rule it activates
* How changing it could change the answer

The enrichment agent must preserve the original legal issue. It must not turn the question into a different problem.

## Gold-answer agents

Use a separate agent to draft the answer only after authorities are independently verified.

Run this agent on Claude Opus 5. Record the model identifier, the prompt hash
and the date of every call. The answer must be legally grounded: every
sentence that states a rule must point at a verified provision excerpt, and
every sentence that applies a rule must point at a scenario fact. An answer
that cannot be grounded that way is not drafted; the question is marked
`blocked_missing_authority` or reserved.

The answer agent may use only:

* Verified scenario facts
* Approved enriched facts
* Verified statutory authorities
* Exact provision excerpts

It may not introduce unsupported legal rules.

## Red-team agents

Use a different agent to audit:

* Unsupported claims
* Incorrect sections
* Missing definitions
* Temporal mistakes
* Contradictory scenario facts
* Question-answer mismatch
* Enrichment that changes the intended issue
* Accidental dependence on case law
* Gold-answer leakage
* Duplicate questions

## When not to use subagents

Do not use subagents for:

* JSON joins
* Counting
* ID generation
* File formatting
* Schema validation
* Dataset merging
* Metric calculation
* Deterministic retrieval evaluation
* Work where two agents would modify the same file

Do not parallelize dependent stages within the same matter.

For one matter, use this sequential order:

```text
issue classification
→ candidate statute retrieval
→ independent authority verification
→ scenario enrichment if required
→ gold-answer drafting
→ red-team audit
→ lawyer-review packet
```

# 9. Retry and disagreement policy

Do not repeatedly ask the same model until it produces a confident-looking answer.

When a legal research or verification stage fails:

1. Preserve the failed attempt.
2. Identify the missing evidence.
3. Reformulate the retrieval query.
4. Retry once with improved evidence.
5. Send unresolved issues to an independent verifier.
6. If still unresolved, mark the question blocked or lawyer-review-required.

Use explicit disagreement fields:

```json
{
  "disagreement_type": "",
  "researcher_position": "",
  "verifier_position": "",
  "supporting_sources": [],
  "status": "lawyer_adjudication_required"
}
```

Model agreement is not legal validation.

# 10. Statutory source hierarchy

Use the strongest available sources.

Preferred order:

1. Official Gazette or official legislative source
2. Repository source package traceable to an authoritative publication
3. Structurally verified finalized statute tree
4. Other local parsed statute text
5. Secondary legal website only as a candidate locator

A gold provision must include:

* Enactment title
* Number and year
* Section and subsection
* Exact relevant excerpt
* Source path or official URL
* Page or structural locator
* Source hash for local files
* Effective-from date
* Effective-to date
* Applicable matter date
* Amendment chain
* Structural-verification status
* Legal-verification status

Never use an untraceable LLM quotation.

If the authoritative provision text cannot be found, mark:

```text
blocked_missing_authority
```

# 11. Gold legal map

Create one legal map per question:

```json
{
  "benchmark_question_id": "M001-Q01",
  "benchmark_matter_id": "M001",
  "atomic_id": "P01-Q01-P01",
  "authority_requirement": "statute_only",
  "legal_issues": [
    {
      "issue_id": "ISS-M001-Q01-01",
      "issue": "",
      "status": "verified"
    }
  ],
  "indispensable_provision_ids": [],
  "supporting_provision_ids": [],
  "legal_hop_count": 1,
  "reasoning_chain": [],
  "gold_answer_draft": {
    "issue": "",
    "rule": "",
    "application": "",
    "conclusion": ""
  },
  "answer_claims": [],
  "research_status": "proposed_gold",
  "lawyer_validation_status": "pending"
}
```

## Provision record

```json
{
  "provision_id": "PROV-M001-Q01-001",
  "enactment_id": "",
  "formal_title": "",
  "number_and_year": "",
  "section": "",
  "subsection": "",
  "version_id": "",
  "effective_from": null,
  "effective_to": null,
  "applicable_to_matter_date": true,
  "relevant_excerpt": "",
  "source_path": "",
  "source_hash": "",
  "locator": "",
  "authority_role": "indispensable",
  "verification_status": "verified",
  "verified_by": ""
}
```

## Claim-level provenance

Every answer claim must be represented separately:

```json
{
  "claim_id": "CL-M001-Q01-001",
  "claim_text": "",
  "claim_type": "rule | application | conclusion",
  "supporting_provision_ids": [],
  "supporting_fact_ids": [],
  "support_strength": "direct | combined | inferential",
  "verification_status": "verified"
}
```

No answer claim may exist without supporting provisions or an explicit fact-based inference.

# 12. Indispensable-provision definition

A provision is indispensable if removing it would:

* Make a required legal claim unsupported
* Remove a necessary statutory condition
* Break the reasoning chain
* Potentially change the legal conclusion

Other relevant provisions are supporting.

The gold set must distinguish:

```text
indispensable
supporting
background
```

The main retrieval metric must evaluate indispensable provisions.

# 13. Legal hop count

Calculate hop count using indispensable reasoning dependencies:

* `1`: One directly applicable provision
* `2`: Provision plus definition, exception, amendment or required linked provision
* `3`: Three necessary linked statutory steps or cross-enactment reasoning
* `4+`: Longer necessary statutory chain

Do not increase hop count merely because several supporting sections were found.

Store the explicit reasoning edges:

```json
{
  "from_provision_id": "",
  "to_provision_id": "",
  "relationship": "defines | qualifies | excepts | amends | cross_references | jointly_required"
}
```

# 14. Scenario enrichment

For `keep`:

* Preserve original facts.
* Normalize only mechanical OCR and whitespace issues.
* Do not add facts unless required for clarity.
* Record every change.

For `enrich`:

1. Identify the legal issue.
2. Find and verify the relevant statutes.
3. Identify factual conditions required by those statutes.
4. Compare those conditions against the original scenario.
5. Add only the missing facts necessary to make the scenario determinate.
6. Add neutral descriptive facts only after decisive facts are frozen.
7. Run a counterfactual check.
8. Preserve original and enriched versions.

Enrichment schema:

```json
{
  "original_background": "",
  "enriched_background": "",
  "added_facts": [
    {
      "fact_id": "FACT-M001-001",
      "fact": "",
      "origin": "synthetic_neutral | synthetic_decisive",
      "reason": "",
      "activates_provision_ids": [],
      "counterfactual_effect": "",
      "approval_status": "pending"
    }
  ]
}
```

Do not expose statute names, section numbers or the gold conclusion through artificial wording unless they existed in the original question.

# 15. Gold-answer drafting

Draft a concise lawyer-style answer using:

```text
Issue
Rule
Application
Conclusion
```

Requirements:

* Address the exact question.
* Use only verified statutes.
* Cite exact sections.
* Apply each indispensable condition to the scenario.
* State uncertainty where facts remain unresolved.
* Avoid unnecessary doctrinal discussion.
* Do not cite cases.
* Do not claim that the answer is lawyer validated.

If a complete answer cannot be produced without case authority, reclassify the item as `mixed_statute_and_case` and reserve it.

# 16. Lawyer review

Claude cannot perform lawyer validation.

Generate review packets containing:

* Original background
* Enriched background, if applicable
* Original question
* Proposed legal issues
* Verified statutes and provision excerpts
* Temporal version information
* Indispensable/supporting labels
* Legal hop count
* Draft answer
* Claim-to-provision matrix
* Added facts
* Counterfactual analysis
* Researcher/verifier disagreements
* Approval form

Approval fields must remain empty:

```json
{
  "reviewer_id": null,
  "review_date": null,
  "background_approved": false,
  "enrichment_approved": false,
  "issues_approved": false,
  "provisions_approved": false,
  "gold_answer_approved": false,
  "required_corrections": [],
  "overall_status": "pending"
}
```

Only an actual lawyer review may change `overall_status` to `approved`.

# 17. Final benchmark eligibility

A question may enter the final benchmark only when:

```text
candidate_action is keep or enrich
extraction is reviewed and usable
scenario is coherent
authority_requirement is statute_only
all indispensable provisions are verified
temporal version is resolved
every answer claim has provenance
enrichment is approved where applicable
lawyer validation is complete
```

Do not force the benchmark to contain 200 items.

The intended target is approximately 180–200 final questions, but quality and legal validity take precedence.

Report the complete attrition funnel:

```text
667 source questions
→ 210 keep/enrich candidates
→ clean/repaired candidates
→ statute-only candidates
→ authority-verifiable candidates
→ lawyer-approved final benchmark
```

# 18. Public and private dataset separation

Create separate views.

## Public input

Contains only:

* Matter ID
* Question ID
* Background
* Question
* Source-paper metadata allowed for release

## Private gold

Contains:

* Gold Acts
* Gold provisions
* Indispensability labels
* Gold answer
* Claim-level provenance
* Legal hop count
* Authority verification
* Lawyer-review data

Do not leak gold section identifiers into retriever input unless they appeared naturally in the original question.

# 19. Retrieval systems

Evaluate every system over exactly the same frozen statutory corpus, the same
query text and the same gold set. The lineup is chosen so that each step
tests one claim about statutory structure. Do not add systems that test
something else.

| # | System | What it tests |
| --- | --- | --- |
| 1 | BM25 | Plain lexical baseline |
| 2 | Field-weighted BM25 | Whether Act title, headings and body deserve separate weights |
| 3 | Dense retriever | Semantic baseline |
| 4 | BM25 + dense RRF | Hybrid baseline |
| 5 | Hybrid + cross-encoder reranker | Strong flat baseline |
| 6 | Hierarchical Act to provision | The core method |
| 7 | Hierarchical + provision-bundle expansion | The complete proposed method |

## System 1: Standard BM25

Index a plain textual representation of each provision. Record the tokenizer,
stopword list, k1 and b.

## System 2: Field-weighted BM25

Use separate fields and record the exact weights:

* Enactment title
* Part or chapter heading
* Section heading
* Provision body
* Definitions
* Cross-reference text

Tune weights only on the development set.

## System 3: Dense retrieval

Use one fixed, documented embedding model. Record the model name and version,
the pooling and index configuration, the query format, the provision
representation and the similarity function.

## System 4: BM25 + dense RRF

Fuse the lexical and dense rankings with Reciprocal Rank Fusion. Record the
exact `k` constant and the component weights.

## System 5: Hybrid + cross-encoder reranking

Retrieve the top 50 to 100 provisions with System 4, then score every
question-provision pair jointly with a cross-encoder and keep the top 20.

```text
Question
-> BM25 + dense top 100
-> cross-encoder reranker
-> final top 20
```

This is the strong baseline. A method that does not beat it has not shown
that structure matters. Record the reranker model, the candidate depth and
the final cutoff.

## System 6: Hierarchical Act to provision retrieval

First retrieve candidate enactments, then retrieve provisions only inside
those enactments.

Record:

* Number of Acts retained
* Act-scoring method
* Section-scoring method
* Behaviour when the correct Act is not retrieved
* Latency

## System 7: Hierarchical retrieval with provision-bundle expansion

This is the proposed method and the main contribution. Instead of treating
every section as an independent document, retrieve a seed provision and
expand it into a statutory bundle along legally typed edges.

```text
Seed provision
+-- referenced definition
+-- applicable exception
+-- amendment
+-- cross-referenced procedure
```

Worked example:

```text
Question
-> identify Act
-> retrieve section 10
-> follow definition in section 2
-> follow exception in section 12
-> return the complete provision bundle
```

The bundle targets the principal metric directly: did the system retrieve
every indispensable provision?

### Typed expansion edges

When a retrieved provision contains wording such as "subject to section 15",
"unless otherwise provided" or "within the meaning of section 2", retrieve
the connected sections automatically. Use explicit relation types rather than
generic graph neighbourhoods:

```text
defines
excepts
qualifies
amends
cross_references
procedurally_requires
```

Typed edges are preferred over generic graph expansion because each edge
carries a legal meaning that can be inspected and ablated.

### Statutory graph reranking

Build the graph Act, Part, Section, Subsection, Definition, Amendment,
Cross-reference. Combine textual relevance with graph relationships:

```text
score(s) = alpha * lexical(s)
         + beta  * dense(s)
         + gamma * act_prior(s)
         + delta * graph_support(s)
```

Tune the four weights on the development set only and report them.

### Temporal filtering

Resolve each provision to the version in force at the matter date. Exclude
or down-weight provisions inserted after that date. Record how many gold
provisions the filter removed, if any.

### Reranking

Apply the same cross-encoder as System 5 to the expanded bundle so the
comparison isolates the expansion step.

## Optional components

### Legal query decomposition

Convert the scenario into several retrieval queries, retrieve for each,
deduplicate and rerank:

```json
{
  "issue_query": "validity of transfer by minor",
  "actor_query": "minor transferor legal capacity",
  "instrument_query": "execution of deed by minor",
  "condition_queries": [
    "guardian consent",
    "age of majority"
  ]
}
```

Use this either as a separate row or as an ablation inside System 7. If a
language model writes the sub-queries, record the model, prompt hash and
every generated query, and cache the outputs so the run is repeatable.

### SPLADE

A learned sparse retriever keeps interpretable term matching while learning
term expansion. Add it as a baseline only if the implementation is
straightforward. It is not essential for the four-page paper.

## Recommended final configuration

Run these seven rows in the main table:

1. BM25
2. Field-weighted BM25
3. Dense retrieval
4. BM25 + dense RRF
5. Hybrid + cross-encoder reranking
6. Act routing, then section retrieval
7. Act routing, then section retrieval, then provision-bundle expansion, then reranking

The novelty claim is:

> Hierarchical statutory bundle retrieval that retrieves an initial provision
> and expands through legally typed definition, exception, amendment and
> cross-reference relationships.

That is a narrower and more testable claim than "we use hierarchical RAG",
and it fits the structured corpus and the complete-indispensable-provision
metric.

Do not include case-rule or judgment retrieval in any system.

## Related work to cite

* Structure-aware statutory retrieval over flat chunk retrieval: SEARCHFIRESAFETY, ACL 2026 (`https://aclanthology.org/2026.acl-long.2112.pdf`).
* Retrieve per sub-question, merge and rerank for multi-hop QA: Findings of EMNLP 2025 (`https://aclanthology.org/anthology-files/pdf/findings/2025.findings-emnlp.236.pdf`).
* Legal knowledge-graph retrieval where reranking quality still matters: NyayGraph, NLLP 2025 (`https://aclanthology.org/2025.nllp-1.11.pdf`).
* SPLADE v2 (`https://arxiv.org/abs/2109.10086`).

Verify every reference against the actual PDF before it enters the paper.

# 20. Dataset split

Split by complete matter, never by atomic question.

Questions sharing a background must remain in the same split.

Create:

* Development set for tuning retrieval parameters
* Held-out test set for final reporting

Suggested policy:

```text
15–20% of matters: development
80–85% of matters: test
```

Stratify where possible by:

* Legal topic
* Keep versus enrich origin
* Legal hop count
* Number of indispensable provisions
* Examination year

If the final statute-only benchmark contains too few matters for a stable split, use a small fixed development set and retain the majority for testing. Document the limitation.

# 21. Evaluation metrics

Report:

* Recall@5
* Recall@10
* Recall@20
* MRR
* nDCG@10
* Act-identification accuracy
* Indispensable-provision Recall@k
* Complete-indispensable-authority Recall@k
* Temporal-version accuracy
* Abstention accuracy
* Retrieval latency

Definitions:

## Indispensable-provision recall

Measure the proportion of gold indispensable provisions retrieved.

## Complete-indispensable-authority recall

A question receives success only when every indispensable provision is retrieved within the cutoff.

This must be the principal metric.

## Act-identification accuracy

Measure whether the first-stage retriever includes every enactment containing an indispensable provision.

# 22. Statistical reporting

Questions from the same matter are not statistically independent.

Compute:

* Macro averages by matter
* 95% confidence intervals using matter-level bootstrap
* Paired matter-level bootstrap comparisons between systems
* Per-topic results
* Per-hop-count results
* Keep-versus-enrich results

Do not claim meaningful improvements from tiny score differences without uncertainty analysis.

# 23. Ablations

Ablate System 7 one component at a time, holding everything else fixed:

* Without Act routing
* Without field weights
* Without the dense component
* Without temporal filtering
* Without definition expansion
* Without exception and qualification expansion
* Without cross-reference expansion
* Without amendment expansion
* Without reranking
* Without query decomposition, if decomposition is part of the final system

Run only ablations for components that are actually implemented. Report each
ablation with the same matter-level bootstrap as the main table.

# 24. Error analysis

Create an auditable error taxonomy:

* Correct Act missed
* Correct Act retrieved but provision missed
* Definition omitted
* Exception omitted
* Amendment/version error
* Cross-reference not followed
* Lexical mismatch
* Dense semantic false positive
* Multiple indispensable provisions only partially retrieved
* Enriched scenario introduced ambiguity
* Gold annotation uncertainty
* Corpus incompleteness
* Appropriate abstention
* Inappropriate abstention

Provide representative examples without exposing private reviewer information.

# 25. Reproducibility

Record:

* Input file hashes
* Corpus snapshot hash
* Code commit
* Model names and versions
* Retrieval parameters
* Random seeds
* Environment information
* Run timestamp
* Query text supplied to each system
* Raw rankings
* Gold relevance sets
* Metric implementation version

All dataset construction and experiment outputs must be deterministic where possible.

Do not overwrite previous runs. Use versioned run directories.

# 26. Required artifacts

Adapt paths to repository conventions, but produce equivalent artifacts:

```text
data/evaluvation/statutory-qa-v1/
  candidates/
    keep-enrich-candidates.jsonl
    tier-a.jsonl
    tier-b-review.jsonl
  reserved/
    mixed-statute-case.jsonl
    case-only.jsonl
    unclear-authority.jsonl
  annotations/
    issue-maps.jsonl
    candidate-provisions.jsonl
    verified-provisions.jsonl
    proposed-gold.jsonl
  review/
    lawyer-review-packets/
    lawyer-review-status.jsonl
  benchmark/
    public-input.jsonl
    private-gold.jsonl
    development-ids.json
    test-ids.json
  audits/
    candidate-funnel.json
    authority-coverage.json
    corpus-audit.json
    annotation-disagreements.jsonl
    validation-report.json
  experiments/
    configs/
    raw-rankings/
    metrics/
    figures/
    tables/
    error-analysis/
  schemas/
  manifests/
```

Create reusable scripts for:

* Candidate selection
* Matter grouping
* Schema validation
* Legal annotation merging
* Corpus auditing
* Gold-set construction
* Dataset splitting
* Retrieval execution
* Metric calculation
* Matter-level bootstrap
* Table generation
* Figure generation
* Error-report generation

Add focused automated tests.

# 27. Pilot-first execution

Do not immediately process all 210 candidates.

First select a pilot containing approximately:

```text
3–5 matters
6–10 questions
```

The pilot must include:

* At least one `keep` matter
* At least one `enrich` matter
* At least one one-hop question
* At least one multi-provision question
* Different statutory topics

Process the pilot through:

```text
lawyer_review_pending
```

Also run a small retrieval smoke test, but clearly label all results preliminary and based on unapproved gold.

Then stop and report:

1. Pilot matter IDs
2. Candidate and final pilot question counts
3. Statute-only/mixed/case-only classification
4. Authorities found
5. Authority-verification failures
6. Enrichment changes
7. Claim-provision completeness
8. Proposed legal hop counts
9. Corpus gaps
10. Files created
11. Tests executed
12. Estimated cost and time for the complete candidate pool
13. Whether the schema should be revised
14. Exact blockers requiring a lawyer

Do not process the remaining candidates until the user approves the pilot.

# 28. Final report requirements

At every major stage, report actual measured values rather than estimates.

The final project summary must state:

* Candidate count
* Matter count
* Statute-only count
* Reserved mixed/case count
* Enriched count
* Excluded count with reasons
* Lawyer-approved count
* Number of statutes represented
* Number of indispensable provisions
* Legal-topic distribution
* Hop-count distribution
* Corpus coverage
* Retrieval results
* Confidence intervals
* Ablation results
* Error distribution
* Known limitations

Never describe unverified, agent-generated annotations as lawyer validated.

Begin by inspecting the repository, auditing the relevant files and producing a concise implementation plan. Then implement the deterministic scaffolding and execute only the pilot.

# 29. Reference implementations

`paper-implementations/` holds two reference codebases used only as reading
material:

* `paper-implementations/LOFin-bench-HiREC/`: the HiREC hierarchical retrieval
  and evidence curation loop. `experiments/HiREC-inspired-retrieval/` is the
  repo's existing port over a 21-Act smoke corpus.
* `paper-implementations/KoBLEX/`: the KoBLEX statutory QA pipeline.
  `experiments/koblex-inspired-retrieval/` is the existing port and holds the
  flat BM25 and query-generation baselines.

Treat these as dummy implementations. Do not copy their numbers, their
20-question smoke set or their evaluation into the paper. Build the systems
in Section 19 against the frozen corpus and the benchmark from Sections 5 to
18, and run every row and every ablation yourself.

# 30. Writing rules

Every piece of prose produced for this project (plan updates, README text,
run reports, error analysis, the paper) is written with
`.agents/skills/avoid-ai-writing/SKILL.md` applied. In practice:

* No em dashes. Use a comma, a full stop or brackets.
* Sentence-case headings. No emoji.
* Bold at most once per section, or not at all.
* No filler transitions ("Moreover", "It is worth noting"), no hollow
  intensifiers, no "not X but Y" pivots.
* Bullets only for list-shaped content; otherwise write paragraphs.
* State measured numbers. Do not describe unmeasured behaviour.

Run `npx markdownlint-cli2` on every Markdown file touched. If it cannot run,
do the check by hand and say so.

# 31. Paper update

When the experiments have run, update `research-paper/neurips_2026.tex` from
the template into the four-page paper: title, abstract, introduction, corpus
and benchmark, method, experiments, results, limitations. Every number in the
paper must come from a file under
`data/evaluvation/statutory-qa-v1/experiments/` and the paper must name the
run directory it was read from. Keep the lawyer-validation status honest: if
the gold set is still `proposed_gold`, the paper says so in the abstract, the
benchmark section and the limitations.

# 32. Final review

After the paper and this plan are updated, review the whole deliverable five
times, one pass each for:

1. Numbers. Every count, metric and interval in the paper, the README and this
   plan matches the files it cites.
2. Claims. No sentence claims lawyer validation, verified legal fact or
   significance that the data does not support.
3. Reproducibility. Every run directory has its config, hashes, seeds, raw
   rankings and gold set, and the commands in the README rebuild it.
4. Writing. Apply `.agents/skills/avoid-ai-writing/SKILL.md` in detect mode
   to the paper, the README and this plan; fix what it flags.
5. Privacy and scope. No client data, no reviewer identities, no case-law
   retrieval in the main experiment, no gold section identifiers leaked into
   retriever input.

Record the outcome of each pass in
`data/evaluvation/statutory-qa-v1/audits/final-review.md` with the date and
what changed.

# 33. Execution record, 5 September 2026

What was run against this plan, with the numbers the files report.

Corpus (`data/evaluvation/statutory-qa-v1/corpus/`): 52 principal
enactments and 60 amending Acts, 4,557 sections, 17,854 provisions, 6,346
typed edges. Built by `scripts/statutory-qa/build_corpus.py`.

Candidates: 667 atomic questions, 210 keep or enrich, 18 quarantined for
background-boundary problems, 66 Tier B, 144 Tier A questions in 92 matters.

Annotation: every Tier A matter was researched by one Claude Opus 5 agent
(`scripts/statutory-qa/prompts/researcher.md`) and every matter with a
statute-only proposed-gold question was checked by a second, independent
Opus 5 agent (`prompts/verifier.md`). 106 questions were classified
statute-only, 36 mixed with case law, 2 unclear. Verification sent 27
proposed-gold questions to legal review. The main benchmark holds 50
questions in 40 matters; an extended set adds the 23 legal-review questions
whose indispensable provisions the verifier confirmed (73 questions, 61
matters). Lawyer approvals: 0.

Departures from the plan, all recorded in the data:

* The pilot-first stop in Section 27 was not observed; the user asked for the
  full run under a submission deadline. The pilot outputs and the full run
  are the same files.
* Enrichment, gold-answer drafting and the red-team audit were folded into
  the researcher and verifier prompts rather than run as separate agents.
* The cross-encoder is `cross-encoder/ms-marco-MiniLM-L-6-v2`; a run with
  `BAAI/bge-reranker-base` was started and stopped because CPU throughput
  under twenty concurrent agents would not finish before the deadline.
* Two design choices (the short rerank query and the scoring of expanded
  sections) were fixed on a 23-question interim subset before the gold set
  was frozen; hyper-parameters were tuned on the development split only.
* Query decomposition and SPLADE were not run.

Experiments: `experiments/configs/tune-dev.selected.json` records the chosen
parameters; `experiments/metrics/main-test/summary.json` and
`experiments/metrics/extended-all/summary.json` hold the results the paper
reads through `scripts/statutory-qa/make_paper_numbers.py`.
