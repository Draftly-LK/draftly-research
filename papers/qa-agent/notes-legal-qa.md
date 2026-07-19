# Legal QA and Statutory Reasoning: Paper Notes

Literature collected for the statute-level QA agent over Sri Lankan conveyancing
statutes (closed corpus, ~85 statutes, exam-style multi-part questions). PDFs live
in this folder as `<arxivid>-<slug>.pdf`. Downloaded and verified 2026-07-19.

## 1. A Dataset for Statutory Reasoning in Tax Law Entailment and Question Answering (SARA)

- arXiv: [2005.05257](https://arxiv.org/abs/2005.05257) — Holzenberger, Blair-Stanek, Van Durme (2020)
- File: `2005.05257-sara-statutory-reasoning.pdf`

The founding benchmark for statutory reasoning. The authors hand-select nine
sections of the US Internal Revenue Code and write 376 test cases: given the
statute text and a short fact pattern, decide entailment ("section X applies to
this case") or compute a numeric answer (tax owed). They pair the corpus with a
manually built Prolog program encoding the statutes, so a symbolic solver reaches
100% given structured facts, while BERT-style models sit near chance. The key
diagnosis: statutory language concentrates all decisive information in one place
(the statute), is dense with cross-references, defined terms, and exceptions, and
so defeats models that rely on distributional statistics. It frames statutory QA
as rule application over a fixed authoritative text, not open-domain reading
comprehension.

Relevance: our task is exactly SARA's setting — apply fixed statute text with
cross-references and exceptions to fact patterns — so its failure analysis tells
us what the agent must handle explicitly.

## 2. Can GPT-3 Perform Statutory Reasoning?

- arXiv: [2302.06100](https://arxiv.org/abs/2302.06100) — Blair-Stanek, Holzenberger, Van Durme (2023)
- File: `2302.06100-gpt3-statutory-reasoning.pdf`

Follow-up applying GPT-3 (text-davinci-003) to SARA with zero-shot,
chain-of-thought, and dynamic few-shot prompting. Dynamic few-shot with the
statute text in the prompt performs best, but well below the symbolic ceiling.
The revealing experiments: GPT-3 recites the underlying IRC sections imperfectly
when asked, and its accuracy drops sharply on synthetic statutes it has never
seen — the model leans on memorized pretraining knowledge of real statutes rather
than pure in-context rule application. Errors persist even when the correct
statute text is supplied. The practical conclusion is that statute text must
always be provided in context and the model still needs scaffolding for the
reasoning itself.

Relevance: Sri Lankan ordinances are far rarer in pretraining data than the US
tax code, so this paper's warning applies with more force — retrieval-grounded
prompting is mandatory, memory cannot be trusted.

## 3. LegalBench: A Collaboratively Built Benchmark for Measuring Legal Reasoning in LLMs

- arXiv: [2308.11462](https://arxiv.org/abs/2308.11462) — Guha, Nyarko, Ho, Ré, et al. (2023)
- File: `2308.11462-legalbench.pdf`

162 tasks contributed by legal professionals, organized under the IRAC framework
into six reasoning types: issue-spotting, rule-recall, rule-application,
rule-conclusion, interpretation, and rhetorical understanding. The paper
evaluates 20 LLMs and shows performance varies widely by reasoning type —
rule-application and rule-conclusion are markedly harder than classification-style
interpretation tasks. Beyond the scores, its main contribution is a shared
typology and lawyer-validated task designs, and it distinguishes evaluating a
model's stated reasoning (does the explanation apply the rule correctly?) from
its bare conclusion. It has become the standard axis system for reporting legal
LLM capability.

Relevance: gives us the vocabulary and task decomposition — exam questions can be
scored separately on rule-recall (right statute), rule-application (right
analysis), and rule-conclusion (right answer).

## 4. Chain of Logic: Rule-Based Reasoning with Large Language Models

- arXiv: [2402.10400](https://arxiv.org/abs/2402.10400) — Servantez, Barrow, Hammond, Jain (2024)
- File: `2402.10400-chain-of-logic.pdf`

A prompting method for applying compositional legal rules, modeled on the
rule-application step of IRAC. The rule is first decomposed into its elements and
their logical structure (e.g., element 1 AND (element 2 OR element 3)); the model
answers each element as an independent thread of reasoning against the facts;
then the sub-answers are recomposed through the logical expression to reach the
conclusion. Across eight rule-application tasks from LegalBench (three
compositional rules), chain of logic consistently beats chain-of-thought,
self-ask, and zero-shot across open-source and commercial models. Errors become
inspectable: a wrong conclusion traces to a specific element judgment or to the
recomposition.

Relevance: the strongest published recipe for the "apply section X to these
facts" core of conveyancing exam answers — decompose statutory conditions into
elements, judge each, recombine.

## 5. Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models

- arXiv: [2401.01301](https://arxiv.org/abs/2401.01301) — Dahl, Magesh, Suzgun, Ho (2024)
- File: `2401.01301-large-legal-fictions-hallucinations.pdf`

Systematic measurement of hallucination when LLMs (ChatGPT-3.5/4, PaLM 2, Llama
2) answer verifiable questions about US case law without retrieval. Hallucination
rates run from 58% to 88% on specific legal queries, worsening for lower courts
and less prominent cases. The paper documents contra-factual bias (models fail to
correct false premises embedded in questions) and poor calibration (confidence
does not track correctness), and shows models often cannot even predict whether
they know a case. It establishes hallucination as structural in closed-book legal
QA, not an occasional glitch.

Relevance: the baseline pathology our agent must be measured against — closed-book
answers about Sri Lankan statutes will hallucinate at least this badly, so every
claim needs retrieval grounding and calibrated refusal.

## 6. Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools

- arXiv: [2405.20362](https://arxiv.org/abs/2405.20362) — Magesh, Surani, Dahl, Suzgun, Manning, Ho (2024; JELS 2025)
- File: `2405.20362-hallucination-free-legal-rag-tools.pdf`

The first preregistered empirical evaluation of commercial legal RAG products
(Lexis+ AI, Westlaw AI-Assisted Research, Ask Practical Law AI) against GPT-4.
RAG reduces hallucination relative to closed-book chatbots, but the tools still
hallucinate 17–33% of the time. The paper's lasting contribution is its
evaluation typology: an answer must be both *correct* and *grounded* — a citation
that exists but does not support the stated proposition ("misgrounding") counts
as hallucination. Failure sources include retrieval of inapposite authority,
sycophantic agreement with false premises, and fluent text that outruns what the
retrieved source says. It argues for claim-level verification against cited
sources rather than trusting the presence of citations.

Relevance: defines how we should score our agent — correctness and groundedness
separately, with per-claim checks that the cited section actually supports the
statement.

## 7. CLERC: A Dataset for Legal Case Retrieval and Retrieval-Augmented Analysis Generation

- arXiv: [2406.17186](https://arxiv.org/abs/2406.17186) — Hou et al. (2024; NAACL 2025)
- File: `2406.17186-clerc-case-retrieval-generation.pdf`

Built on the Caselaw Access Project, CLERC defines two tasks: retrieve the
authorities a passage of legal analysis should cite, and generate the analysis
given the retrieved authorities. Zero-shot IR models manage only 48.3%
recall@1000 — legal citation retrieval is much harder than generic passage
retrieval. On generation, GPT-4o gets the best ROUGE but hallucinates the most
citations, exposing the fluency/faithfulness trade-off. The paper introduces
citation-level metrics (citation precision/recall, false-positive citation rate)
alongside text-overlap scores, treating each generated citation as a checkable
claim.

Relevance: supplies the citation-grounded generation framing and citation
precision/recall metrics we can apply to statute pincites in exam answers.

## 8. LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain

- arXiv: [2408.10343](https://arxiv.org/abs/2408.10343) — Pipitone, Houir Alami (2024)
- File: `2408.10343-legalbench-rag.pdf`

The first benchmark isolating the retrieval step of legal RAG: 6,858 queries over
a 79M-character corpus (contracts, NDAs, M&A agreements, privacy policies), each
with human-annotated ground-truth character spans. The design argument: legal RAG
needs minimal, precisely relevant snippets, because whole documents blow the
context window and imprecise chunks induce hallucination downstream. Their
ablations show chunking strategy materially changes precision/recall@k (recursive
text splitting beats naive fixed-size chunks), and reranking helps precision but
is not a cure-all. Precision/recall are reported at the span level, so a system
gets no credit for retrieving the right document at the wrong granularity.

Relevance: directly shapes our index design — chunk statutes at section/subsection
granularity with span-level gold annotations, and evaluate retrieval separately
from generation.

## 9. A Reasoning-Focused Legal Retrieval Benchmark (Bar Exam QA / Housing Statute QA)

- arXiv: [2505.03970](https://arxiv.org/abs/2505.03970) — Zheng, Guha, Arifov, Zhang, Skreta, Manning, Henderson, Ho (2025; CS&Law 2025)
- File: `2505.03970-reasoning-focused-legal-retrieval-barexamqa.pdf`

Introduces two benchmarks built to mimic real legal research rather than keyword
lookup: Bar Exam QA (US bar exam questions with lawyer-annotated gold supporting
passages) and Housing Statute QA (yes/no questions over state housing statutes
with gold statute sections). Both are reasoning-intensive: the query is a fact
pattern whose vocabulary barely overlaps the controlling passage, so standard
lexical and dense retrievers score far below their results on conventional IR
benchmarks. Supplying gold passages lifts answer accuracy substantially over both
closed-book and retrieved-passage conditions, quantifying how much of the QA gap
is a retrieval problem. The paper positions bridging the fact-pattern-to-authority
gap (query expansion, reasoning-aware retrievers) as the open problem.

Relevance: the closest published analogue to our task — exam fact patterns
retrieved against statute sections — and its gold-passage/retrieved/closed-book
comparison is the ablation structure we should copy.

## 10. Self-Verification is All You Need To Pass The Japanese Bar Examination

- arXiv: [2601.03144](https://arxiv.org/abs/2601.03144) — Shin (2026)
- File: `2601.03144-self-verification-japanese-bar-exam.pdf`

Reports the first LLM pass of the Japanese bar examination under the exam's
original question structure and official scoring, without reformatting questions
into simpler true/false pieces. The core mechanism is a trained self-verification
(consistency-verification) step: the model checks its own candidate answers for
internal consistency across the jointly evaluated propositions of each question
before committing. Comparisons show that more elaborate alternatives —
multi-agent inference and decomposition-based supervision — fail to reach
comparable performance, and the author argues "format-faithful supervision"
matters more than pipeline complexity for high-stakes exam formats. Evaluation is
on the actual exam scale against the official passing score.

Relevance: supports adding a verification pass over drafted answers and scoring
on the real exam's marking scheme rather than a simplified proxy.

## 11. SCaLe-QA: Sri Lankan Case Law Embeddings for Legal QA

- CEUR-WS Vol-3822 (SICSA REALLM Workshop 2024), not on arXiv — Jayawardena, Wiratunga, Abeyratne, Martin, Nkisi-Orji, Weerasinghe (RGU / IIT Sri Lanka)
- File: `ceurws-scale-qa-sri-lankan-case-law.pdf`

The only published retrieval system we found targeting Sri Lankan legal QA. The
authors scrape 1,541 Sri Lankan Supreme Court judgments (2009–2024), OCR and
clean them, apply semantic chunking (384-token chunks following the Open
Australian Legal QA setup), and build training triplets by ranking sentences
within each judgment with BM25 as weak supervision. They then fine-tune AnglE-BERT
embeddings with contrastive, angle, and in-batch-negative losses to improve
retrieval for a planned RAG/case-based-reasoning QA pipeline. Results are
preliminary (improved retrieval accuracy over the base embedder); no end-to-end
QA evaluation yet. The broader SigmaLaw line from University of Moratuwa (de
Silva et al.) covers Sri Lankan/US legal sentiment and information extraction but
not statute QA.

Relevance: confirms no prior system does Sri Lankan statute QA — our corpus is
novel — and shows domain-specific embedding fine-tuning with weak supervision is
feasible for Sri Lankan legal English.

## What SOTA looks like for statute QA in 2026

The literature converges on a pipeline with four layers, each independently
evaluated.

### 1. Retrieval design

- Chunk the corpus at statute section/subsection granularity, preserving act
  name, section number, and heading in each chunk; span-precise retrieval beats
  document- or page-level retrieval and reduces downstream hallucination
  (LegalBench-RAG 2408.10343).
- Use hybrid retrieval: BM25 plus a dense embedder, with a reranker. Plain
  retrievers fail on exam-style queries because fact-pattern vocabulary does not
  overlap statutory language, so add a query-transformation step — have the model
  restate the fact pattern as the legal issue / hypothetical statutory language
  before retrieving (2505.03970; COLIEE statute-retrieval systems use the same
  multi-stage filter-then-rerank pattern).
- Domain fine-tuning of embeddings on the closed corpus with weak supervision
  (BM25-derived triplets, contrastive loss) is cheap and works for Sri Lankan
  legal text (SCaLe-QA).
- Always put the retrieved statute text in context; never let the model answer
  from parametric memory — it misremembers even the heavily trained US tax code
  (2302.06100), and closed-book legal hallucination rates are 58–88%
  (2401.01301).

### 2. Reasoning structure

- Structure answers as IRAC — the field's own decomposition of legal reasoning
  into issue-spotting, rule-recall, rule-application, and conclusion
  (LegalBench 2308.11462).
- For the rule-application step, use Chain-of-Logic: extract the section's
  elements and their AND/OR structure, judge each element against the facts as a
  separate reasoning thread, then recompose through the logical expression
  (2402.10400). This is the published SOTA for compositional rule application
  and makes errors attributable to a specific element.
- Resolve cross-references and exceptions explicitly (retrieve the referenced
  section too); these are the documented failure points of statutory reasoning
  (SARA 2005.05257).
- Keep the exam's own multi-part question format rather than flattening it;
  format-faithful handling outperformed decomposition pipelines on the Japanese
  bar exam (2601.03144).

### 3. Grounding and citation enforcement

- Require a pinpoint citation (act, section, subsection) for every legal
  proposition, and treat each citation as a checkable claim (CLERC 2406.17186).
- Enforce the correct-AND-grounded standard: a real citation that does not
  support the stated proposition is still a hallucination ("misgrounding",
  2405.20362). Check support claim-by-claim against the retrieved span, not
  answer-by-answer.

### 4. Verification

- Add a post-draft verification pass: re-check each cited section against the
  claim it supports, and check internal consistency across the sub-parts of a
  multi-part answer before finalizing (2601.03144; 2405.20362).
- Calibrate refusal: when retrieval returns nothing on point, say so — models
  cannot self-assess from parametric knowledge (2401.01301).

### Evaluation criteria used in the field

Score the agent on the same axes the literature reports, with retrieval and
generation measured separately:

1. **Retrieval quality**: precision/recall@k against annotated gold statute
   spans, at span (not document) granularity (LegalBench-RAG 2408.10343;
   2505.03970).
2. **Answer accuracy**: graded on the real exam's marking scheme, with
   closed-book vs retrieved vs gold-passage ablations to isolate the retrieval
   contribution (2505.03970; 2601.03144).
3. **Hallucination / groundedness rate**: fraction of answers containing an
   incorrect or misgrounded claim, using the correctness-plus-groundedness
   typology (2405.20362; 2401.01301).
4. **Citation quality**: citation precision/recall and false-citation rate
   (CLERC 2406.17186).
5. **Reasoning-type breakdown**: report rule-recall, rule-application, and
   rule-conclusion accuracy separately per the LegalBench taxonomy (2308.11462),
   including element-level correctness where Chain-of-Logic decomposition applies
   (2402.10400).
