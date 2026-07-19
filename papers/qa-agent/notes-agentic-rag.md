# Agentic and Iterative RAG for QA: Paper Notes

Literature collected for the statute-level legal QA agent (closed corpus of ~85 Sri Lankan
conveyancing statutes in markdown). All PDFs live in this folder, named
`<arxivid>-<slug>.pdf`. Papers are ordered chronologically.

## ReAct: Synergizing Reasoning and Acting in Language Models

- arXiv: 2210.03629 (2022, ICLR 2023) — `2210.03629-react.pdf`

Mechanism: the LLM alternates between free-form reasoning steps ("thoughts") and
discrete actions against an external environment (for QA: `search[entity]` and
`lookup[keyword]` calls to a Wikipedia API), with each action's observation appended to
the context before the next thought. The thought steps decompose the question, track
what is known so far, and decide the next lookup; the loop ends with a `finish[answer]`
action. Everything runs from a few-shot prompt — no training. The paper also shows that
switching between ReAct and plain chain-of-thought (fall back to the other when one
fails) beats either alone.

Reported gains: on HotpotQA and FEVER, ReAct cuts the hallucination cases seen with pure
CoT, and ReAct + CoT self-consistency is the best prompting variant; on the interactive
ALFWorld and WebShop benchmarks it beats imitation/RL baselines by 34% and 10% absolute.

Relevance to a closed-corpus statute QA agent: this is the base recipe for any tool-using
retrieval loop — the agent decides per step whether to search the statute index or answer,
and the thought trace doubles as an auditable reasoning record for legal answers.

## IRCoT: Interleaving Retrieval with Chain-of-Thought Reasoning

- arXiv: 2212.10509 (2022, ACL 2023) — `2212.10509-ircot.pdf`

Mechanism: instead of retrieving once with the original question, IRCoT alternates two
steps until the answer is reached: (1) extend the chain-of-thought by one sentence given
the question plus all paragraphs retrieved so far; (2) use that newly generated CoT
sentence as the next retrieval query and add the top-k paragraphs to the pool. The CoT
sentence names the bridge entity or intermediate fact the first-hop query could never
express, so each hop's retrieval is conditioned on partial reasoning. A reader then
answers from the accumulated paragraphs. Prompt-based, works with both GPT-3 and
Flan-T5 down to 3B.

Reported gains: up to 21 points higher retrieval recall and up to 15 points higher answer
F1 over one-shot retrieval on HotpotQA, 2WikiMultihopQA, MuSiQue, and IIRC.

Relevance to a closed-corpus statute QA agent: the cheapest strong fix for cross-statute
questions — when hop 1 finds the Prescription Ordinance rule, the CoT sentence about it
becomes the query that finds the interacting Registration of Documents provision.

## FLARE: Active Retrieval Augmented Generation

- arXiv: 2305.06983 (2023, EMNLP 2023) — `2305.06983-flare.pdf`

Mechanism: retrieve on demand while generating long answers. The model first drafts the
next sentence; if every token in it is above a probability threshold, the sentence is
kept and generation continues without retrieval. If any token falls below the threshold,
FLARE treats the draft as a signal of missing knowledge, builds a query from it — either
by masking the low-confidence spans or by asking the model to generate a question the
sentence would answer — retrieves, and regenerates the sentence with the new evidence in
context. Retrieval timing and query content are thus driven by the model's own
uncertainty about what it is about to say, not by fixed intervals.

Reported gains: superior or competitive against single-retrieval and fixed-interval
multi-retrieval baselines on four long-form tasks, including 2WikiMultihopQA, ASQA, and
open-domain summarization.

Relevance to a closed-corpus statute QA agent: useful for multi-part essay-style answers —
trigger a fresh statute lookup exactly when the drafted clause about notice periods or
priority rules is low-confidence, instead of retrieving once per question part.

## Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection

- arXiv: 2310.11511 (2023, ICLR 2024) — `2310.11511-self-rag.pdf`

Mechanism: fine-tunes a 7B/13B generator to emit reflection tokens inline. A `Retrieve`
token decides whether a segment needs retrieval; for each retrieved passage the model
generates a candidate continuation plus critique tokens scoring passage relevance
(`ISREL`), whether the passage supports the generated segment (`ISSUP`), and overall
utility (`ISUSE`). Decoding runs a segment-level beam search that ranks candidates by a
weighted combination of these critique scores, so unsupported segments are pruned during
generation, not after. Training data comes from a GPT-4-distilled critic model that
annotates corpora with the reflection tokens offline, so no critic runs at inference.

Reported gains: Self-RAG 7B/13B beats ChatGPT and retrieval-augmented Llama2-chat on
PopQA, PubHealth, ARC-Challenge, and biography generation, and substantially improves
citation precision on ASQA.

Relevance to a closed-corpus statute QA agent: the `ISSUP` idea — score every generated
claim against the retrieved statute section and prune unsupported ones — is directly the
grounding check a legal answer needs, even if implemented as a prompted judge rather than
trained tokens.

## CRAG: Corrective Retrieval Augmented Generation

- arXiv: 2401.15884 (2024) — `2401.15884-crag.pdf`

Mechanism: a lightweight retrieval evaluator (fine-tuned T5-large) scores each retrieved
document against the query and maps the confidence to one of three actions. `Correct`:
keep the documents but run knowledge refinement — split each document into fine-grained
strips, score each strip, discard irrelevant strips, and recompose only the relevant
ones. `Incorrect`: discard retrieval entirely and fall back to web search with a
rewritten query. `Ambiguous`: combine both refined strips and web results. The corrected
evidence then goes to any generator, so CRAG bolts onto existing RAG pipelines without
touching the generator.

Reported gains: plugged into standard RAG and into Self-RAG, CRAG improves both across
PopQA, Biography, PubHealth, and ARC-Challenge (e.g. +7 points accuracy on PopQA over
Self-RAG).

Relevance to a closed-corpus statute QA agent: the evaluator-plus-strip-refinement path
fits a small corpus perfectly — detect when the retrieved sections do not actually answer
the question and re-query the corpus (web fallback replaced by query rewriting over the
85 statutes), and strip filtering isolates the operative subsection from long statute
chunks.

## RQ-RAG: Learning to Refine Queries for Retrieval Augmented Generation

- arXiv: 2404.00610 (2024, COLM 2024) — `2404.00610-rq-rag.pdf`

Mechanism: fine-tunes Llama2-7B end-to-end to emit special control tokens that trigger
three query-refinement operations before and during retrieval: rewriting (fix vague
phrasing), decomposition (split multi-hop questions into sub-queries), and
disambiguation (enumerate readings of ambiguous questions). Generation unfolds as a
search tree: each refinement spawns a branch with its own retrieval and continuation,
and the final answer is selected across branches by perplexity, confidence, or an
ensemble score. Training data is built by prompting ChatGPT to annotate existing QA
datasets with refinement trajectories.

Reported gains: surpasses the previous SOTA (including Self-RAG) by 1.9% average on three
single-hop QA datasets and shows larger gains on multi-hop sets (HotpotQA,
2WikiMultihopQA, MuSiQue).

Relevance to a closed-corpus statute QA agent: exam questions bundle several sub-issues
into one prompt; explicit decomposition into one retrieval query per sub-issue is the
main lever RQ-RAG validates, and the disambiguation branch maps to questions that turn on
which statute governs.

## Plan*RAG: Efficient Test-Time Planning for Retrieval Augmented Generation

- arXiv: 2410.20753 (2024) — `2410.20753-plan-rag.pdf`

Mechanism: replaces retrieve-then-reason with plan-then-retrieve. A frozen LM first
generates a reasoning DAG: the question is decomposed into atomic sub-queries with
explicit dependency edges (a sub-query may reference the answers of its parents).
Sub-queries in the same DAG layer are retrieved and answered in parallel by plug-in
"expert" calls, and each sub-query sees only its own retrieved context plus parent
answers (information isolation), which keeps context small and lets every sub-answer be
attributed to specific documents. The final answer is composed by walking the DAG. No
fine-tuning anywhere.

Reported gains: significant reductions in hallucination and improved attribution versus
retrieve-then-reason baselines on multi-hop QA, with efficiency gains from parallelized
retrieval and generation.

Relevance to a closed-corpus statute QA agent: multi-part legal questions are naturally a
DAG (part (b) depends on the statute identified in part (a)); isolating each sub-question
with only its statute sections raises precision and gives per-part section citations.

## Search-o1: Agentic Search-Enhanced Large Reasoning Models

- arXiv: 2501.05366 (2025) — `2501.05366-search-o1.pdf`

Mechanism: wraps a large reasoning model (QwQ-32B) that produces long chains of thought
in an agentic retrieval loop. When the model hits an uncertain knowledge point mid-chain,
it emits a search query inside special tokens; the framework runs the search, but instead
of dumping retrieved documents into the chain, a separate Reason-in-Documents module
reads the documents together with the current reasoning state and distills them into a
short refined note that is injected back. This two-stage design keeps long documents from
derailing the chain of thought and supports multiple retrievals per question. Inference-
time only, no training.

Reported gains: outperforms retrieval-augmented and vanilla reasoning baselines on
GPQA, math benchmarks, and multi-hop QA (HotpotQA, 2Wiki, MuSiQue, Bamboogle), exceeding
human experts on GPQA in some settings.

Relevance to a closed-corpus statute QA agent: the Reason-in-Documents step is the
transferable part — statutes are long and repetitive, so distilling retrieved sections
into a compact note keyed to the current reasoning step protects answer quality on
multi-retrieval questions.

## DeepRAG: Thinking to Retrieval Step by Step for Large Language Models

- arXiv: 2502.01142 (2025) — `2502.01142-deeprag.pdf`

Mechanism: frames retrieval-augmented reasoning as a Markov decision process. At each
step the model generates the next subquery, then makes an explicit binary decision:
retrieve for it, or answer it from parametric knowledge. Training data comes from a
binary-tree search over these decisions that finds trajectories reaching the correct
answer with minimal retrievals; the model is first imitation-trained on those
trajectories, then refined with "chain of calibration," a preference-style objective that
aligns the retrieve/skip decision with the model's actual knowledge boundaries so it
retrieves exactly when it does not know.

Reported gains: 21.99% average answer-accuracy improvement over adaptive-retrieval
baselines while using fewer retrievals, across HotpotQA, 2WikiMultihopQA, and other QA
sets.

Relevance to a closed-corpus statute QA agent: the knowledge-boundary calibration matters
in law with the sign flipped — for statute questions the safe policy is near-always
retrieve, but the stepwise subquery-then-decide structure is a clean template for the
agent loop.

## Search-R1: Training LLMs to Reason and Leverage Search Engines with Reinforcement Learning

- arXiv: 2503.09516 (2025) — `2503.09516-search-r1.pdf`

Mechanism: trains the whole interleaved reason-search-read loop end-to-end with
reinforcement learning (PPO or GRPO). The model generates `<think>` segments and may emit
`<search>query</search>`; the environment returns passages inside `<information>` tags
and generation continues, over multiple turns, until `<answer>` is produced. The only
supervision is an outcome reward (exact match of the final answer) — no annotations of
when or what to search. A key trick is retrieved-token masking: tokens inside
`<information>` blocks are excluded from the policy-gradient loss, which stabilizes
training. The model thus learns query formulation, when to re-search, and how many hops
to take, from reward alone.

Reported gains: average relative improvements of 41% (Qwen2.5-7B) and 20% (Qwen2.5-3B)
over strong RAG baselines across seven QA datasets, including HotpotQA, 2WikiMultihopQA,
MuSiQue, and Bamboogle.

Reported gains come with a cost: it needs an RL training pipeline and a reward signal,
which a small legal project may not have.

Relevance to a closed-corpus statute QA agent: the current ceiling for learned agentic
retrieval — worth revisiting if the project ever gets a graded exam-question dataset large
enough to serve as an outcome reward; until then its loop structure can be imitated with
prompting.

## Ranked: top 3 mechanisms for precision on closed-corpus statute QA

Setting: ~85 statutes, exam-style questions that are multi-part and cross-statute, and a
premium on precise section-level grounding. Prompt-time mechanisms beat trained ones here
because the corpus is small and there is no RL-scale training data.

1. Planned decomposition into dependency-ordered sub-queries (Plan*RAG, with RQ-RAG and
   IRCoT as the interleaved variant). Multi-part questions fail at retrieval, not
   generation: one embedding query cannot cover three sub-issues across two statutes.
   Decomposing into atomic sub-queries — and using earlier sub-answers to form later
   queries, IRCoT-style — is the single biggest precision lever, and the DAG gives
   per-part section attribution for free.
2. Corrective retrieval evaluation with strip-level refinement (CRAG). On a small corpus
   the retriever will often return the right statute but the wrong section, or a
   plausible-but-wrong statute. An explicit evaluator that grades retrieved sections,
   triggers an in-corpus re-query on failure, and filters chunks down to the operative
   subsections directly attacks the dominant error mode.
3. Support verification of each generated claim against retrieved text (Self-RAG's
   `ISSUP` critique, implementable as a prompted judge). Exam answers state rules,
   periods, and conditions; checking every claim against the cited section and pruning
   or re-retrieving for unsupported ones converts retrieval precision into answer
   precision and yields trustworthy citations.

Honorable mention: Search-o1's Reason-in-Documents distillation, as a cheap add-on that
keeps long statute extracts from polluting the reasoning context.
