# Draftly Retrieval Engine — End-to-End Plan

Design for the retrieval engine over `data/processed/`, grounded in a deep read
of 12 papers (three parallel review passes, 2026-07-17) evaluated against our
actual corpus. Every design choice below carries its evidence.

## 0. Our position (why we can beat the papers)

Every paper we read fights an **open-world** problem: thousands of candidate
statutes, unknown citation graphs, uncurated topics. They spend their machinery
*approximating* what we already own:

| They build (noisily) | We own (curated) |
| --- | --- |
| HNMFk topic induction (2502.20364) | 20 lawyer-curated topic→statute tables (174 edges) |
| LLM entity-extracted KGs (2602.23371: 5,056 edges from ~6,400 docs) | 14,665 deterministic, quote-backed case→section links from 5,121 judgments |
| GNN link prediction because only 16% of refs were linkable (2506.22165) | closed registry: ~57 statutes + 18 amendments, complete by construction |
| Statute identification over 936 open sections (2511.00268) | bounded classification over a known menu |

The engine design principle follows: **deterministic structure does the legal
work; lexical search does recall; the graph does multi-hop; embeddings are a
fallback linker only; a bounded LLM classifies and extracts but never asserts.**

## 1. Verdicts from the literature (adopt / reject)

### Adopt (with the number that justifies it)

- **Scope-first retrieval through topic partitions.** Topic-partitioned
  sub-indexes lifted MRR/top-10 from ~29–42% to ~75–95% across source types
  (2502.20364, Fig 8). Our 20 topics are that partition, curated for free.
- **Multi-hop = Personalized PageRank over the real citation graph.** HippoRAG's
  ablation: removing the graph walk drops avg R@5 from 72.9 → 56.2; its weakest
  component is the LLM-built KG (2405.14831). We run PPR on *ground-truth* edges
  instead — damping 0.5, seeds weighted by node specificity (1/citation-count).
- **Graph expansion for recall, then re-rank.** NyayGraph's 3-hop expansion
  (cited-by → cites → same-topic siblings) bought **+136.8% recall** via edge
  joins alone; but raw KG context dumped into an LLM prompt *dropped* F1
  0.072→0.059 — expansion demands a re-ranking stage (2025.nllp-1.11).
- **Cross-task injection.** When resolving a statute for case X, inject the
  statutes cited by the cases X cites (a file join over our link table). This was
  IL-PCSR's SOTA trick: +4.3 F1, biggest on rare statutes (2511.00268).
- **Metadata-as-nodes.** Court, topic, parent statute, decade as graph *nodes*
  with membership edges, in the same flat edge file — makes multi-hop and
  authority ranking emerge from plain traversal (2506.22165).
- **Year filtering + calibrated k.** A case cannot cite a later case; fixed
  output size calibrated to observed citations-per-case. Load-bearing
  post-processing in COLIEE's 2nd-place system (2505.20743).
- **Temporal model: dated section-versions + Action nodes.** Amendment events as
  first-class records: (amending act §) → terminates old version → produces new
  version; consolidated state at date T = interval join with pointer-reuse for
  unchanged siblings; `SnapshotLast` validity predicate
  (`valid_start ≤ t < valid_end`) (2505.00039). Refuse, don't approximate, when
  nothing is in force (2606.09724).
- **BM25 as the lexical workhorse.** Best zero-shot retriever on legal text;
  general-domain dense retrievers and rerankers *underperform or actively harm*
  (2406.17186; confirmed by 2504.01840 and 2511.00268 for case↔case).
- **Collapsed multi-granularity pool.** Rank topic rows, sections, case-rules,
  and paragraphs in ONE pool under a token budget — the query picks its own
  abstraction level (RAPTOR's one transferable finding, 2401.18059).
- **Eval: mask-a-citation gold set + closed-corpus hallucination metric.**
  CLERC's recipe: the paragraph around a real citation (citation masked) is the
  query; the cited authority is gold. Metrics: recall@k, nDCG@10,
  **All-Recall@k** (every gold authority in top-k), and Citation
  Recall/Precision/False-Positive — CFP is *exactly* computable on a closed
  corpus (2406.17186). Always report against a no-retrieval baseline
  (2504.01840).

### Reject (and why)

- **GNNs / trained retrievers / contrastive models** — exist to predict missing
  links or learn relevance without labels. Our links are deterministic ground
  truth; their ceilings sit below zero-training LLM re-rankers anyway
  (2511.00268: fine-tuned ceiling ~39 F1 vs 46 for the re-ranker).
- **LLM-extracted knowledge graphs** — noisier and sparser than what we own
  (their ~5k unvalidated edges vs our 14.6k quote-backed).
- **RAPTOR's cluster-summarize tree** — nondeterministic (UMAP/GMM), unvalidated
  summaries as retrieval surface, and it *loses to plain BM25* on cross-document
  lookup (HippoRAG Table 2). Our curated topics are a better upper layer.
- **Vector DBs / Neo4j / Milvus / pyserini stacks** — our whole graph is two CSV
  files; NyayGraph's entire KG was 1,225 nodes. File-based holds to ~100× our
  scale.
- **Silent vector fallback** — "default to highest-confidence vector passages
  when the KG fails" (2502.20364) is the exact fluent-failure mode the theory
  papers warn about. We flag or refuse instead: deterministic systems fail
  loudly, probabilistic ones fail fluently (2606.09724).
- **Full bitemporal modeling, LRMoo/Akoma Ntoso ontologies, agentic RAG loops**
  — national-legislature machinery; our corpus doesn't need it (and off-the-shelf
  agentic RAG *reduced* accuracy in LRAGE's tests: 76.1 → 61.5).

### Why not plain vector similarity (the three-tier argument for the report)

1. **Theoretical** (2606.09724): legal correctness = *validity* (in force, on a
   date, by which act) — similarity cannot express it; similarity is symmetric
   while legal structure is directional; successive amended versions are
   near-identical in embedding space, so similarity cannot pick the version in
   force.
2. **Architectural** (2505.00039): flat retrieval conflates temporal states
   (anachronism) and cannot scope hierarchically ("which provisions belong to
   Part II").
3. **Empirical** (2602.23371, 2502.20364): vector-only RAG scores high
   *relevance* but low *correctness/completeness* (hybrid 70% vs RAG-only 37.5%
   pass rate); frontier LLMs + vector context hallucinate citations and refuse
   aggregates.

## 2. The data model (extends `data/processed/`)

```text
data/processed/
  docs/…                          (done — 9,295 normalized markdown docs)
  cases.jsonl                     (done — 9,177 case records)
  case_statute_section_links.csv  (done — 14,665 edges, unverified)
  topics*, topic-sources.csv      (done — rule tables)
  NEW:
  sections.jsonl        one record per statute section VERSION:
                        {section_id, source_id, section_no, heading, text_anchor,
                         valid_from, valid_to, produced_by_action, topics[]}
  actions.csv           amendment events: {action_id, amending_source_id,
                        amending_section, target_section_id, old_version,
                        new_version, effect: amend|repeal|insert, date}
  edges.csv             ONE unified graph edge list:
                        case→section (from links), case→case (citations),
                        statute→statute (cross-references parsed from statute text),
                        topic→statute, case→court, case→topic, statute→amendment
  aliases.csv           statute short titles / Sinhala names / common abbreviations
  rules.csv             (planned) rule-per-case: {rule_id, statement,
                        supporting_quote, section_id, topics, case_ref,
                        confidence, status=unverified}
  authority.csv         per case: {case_id, court, level: SC|CoA|HC,
                        binding_rank: 3|2|1, reported: bool, slr_citation?, year}
  eval/gold.csv         the ~50-question gold set
```

Node identities are canonical (registry `source_id`s, normalized section
numbers, case citations) — no embedding-linked aliases; `aliases.csv` is the
hand-curated synonym table (replaces HippoRAG's synonymy edges).

## 3. Query taxonomy → routing

The router is a keyword table first (mentor's step keywords + topic keywords),
bounded-LLM classification only as fallback. Classes and their plans:

| # | Class | Example | Plan |
| --- | --- | --- | --- |
| Q1 | Doctrinal lookup | "requisites of a valid deed" | topic route → sections + rules (scoped BM25 pool) |
| Q2 | Authority lookup | "cases on s.2 Prevention of Frauds" | exact graph join: `cases_for_section`, authority-ranked |
| Q3 | Temporal / in-force | "stamp duty law as at 2003" | `statesAt(section, date)` → version + provenance chain; refuse if none |
| Q4 | Procedural / step | "what to check in examination of title" | topic-09 step tables (mentor's 6 functions) → each step's sections + cases |
| Q5 | Multi-hop / relational | "cases citing s.66 Partition Law AND prescription" | seed extraction → PPR over edges.csv → re-rank |
| Q6 | Aggregate | "how many cases applied s.X" | exact count from links (the 2502.20364 demo pattern — LLMs refuse or fabricate these) |
| Q7 | Matter-grounded | red flag in a case_record → authority | red-flag rule table → governing sections + leading cases (POC authority panel) |

## 4. The engine (typed, deterministic primitives)

A small Python package reading only `data/processed/` — per 2606.09724's C4:
fixed, typed retrieval primitives, never LLM-generated queries or raw top-K:

```text
resolve_statute(name_or_alias)            → source_id            (aliases.csv)
sections_for_topic(topic_id)              → section nodes        (topic tables)
statesAt(section_id, date)                → version-in-force + provenance π
cases_for_section(section_id, date?, k)   → cases, authority-ranked
related_cases(case_id)                    → co-citation Jaccard over links
expand(seeds)                             → NyayGraph 3-hop: +cited-by, +cites,
                                            +same-topic siblings (recall layer)
ppr(seed_nodes, k)                        → Personalized PageRank over edges.csv
                                            (damping .5, seeds × 1/cite-count)
pool(query, scopes, budget)               → collapsed multi-granularity BM25 pool
answer(query)                             → route → plan → evidence → grounded
                                            answer + machine-readable provenance
```

**Ranking** (deterministic weighted merge; Skyline as tiebreak): topic-scope
match → binding rank (SC 3 > CoA 2 > HC 1) → reported bonus → in-force status →
PPR score → BM25 score → recency → year filter (candidate.date < query-context
date where applicable). Fixed k calibrated from citations-per-case statistics.

**Generation contract:** every claim must carry a resolvable citation; any
citation that doesn't resolve against the closed corpus is a hard error (CFP);
the answer discloses the temporal policy used and ships a JSON provenance annex;
**no evidence → abstain**, never paraphrase from parametric memory.

## 5. Authority ranking (and the binding question)

Correction worth keeping on record: **Court of Appeal decisions ARE binding** on
all courts below it (High Courts, District Courts, Magistrates) until the SC
overrules them; they are persuasive only *to the SC itself*. High Court
decisions are persuasive. And practically: most land litigation (partition,
title, RPA) terminates at HCCA/CoA — SC leave is discretionary — so CoA
authority is frequently the operative final word, and title examination is a
prediction of outcomes in courts *bound by* the CoA. Therefore: **authority is a
ranking signal and a display label ("binding" / "binding on trial courts" /
"persuasive"), never a filter.**

None of the 12 papers implements judicial-hierarchy-aware ranking (2505.00039
names it as an open extension; 2602.23371 treats SC and HC flat). **This is our
most novel component relative to the literature** — worth a highlighted place in
the report.

## 6. Bounded-LLM enrichment (the only model calls in the system)

All three are classification/extraction over closed sets, validated, and
`unverified` until lawyer sign-off:

1. **Citation disambiguation** (62k queue): deterministic pre-filter (drop
   Roman-law/Digest noise) → candidates = full ~57-statute catalogue (the menu
   fits — the published SOTA pattern per 2511.00268 and 2025.nllp-1.11) + case
   context + **cross-task injection** (statutes cited by cited cases) + abstain
   → validate section exists in that act. Restricted-output prompt + deterministic
   normalizer ("294(b)"→"294B") per NyayGraph.
2. **Rule extraction** (`rules.csv`): headnote-first for the 3,703 reported
   cases; quote-backed extraction for the 1,418 unreported (quote must appear in
   the judgment verbatim; abstain when no clean rule). Spot-check against
   RAPTOR's observed ~4% summary-hallucination rate.
3. **Router fallback**: query classification only, into the 7 classes above.

Model: cheap and swappable (OpenAI-compatible client; NVIDIA NIM 8B-class
default, local Ollama alternative). Small models are safe because **the
validation layer, not the model, guards correctness.**

## 7. Evaluation harness

- **Gold set (~50):** ~30 auto-mined by masking real citations in judgment
  paragraphs (CLERC recipe — our 14,665 edges generate these for free), ~20
  lawyer-written from the topic tables. Each item: {question, gold sections,
  gold cases, the proposition each supports}.
- **Metrics:** recall@k, nDCG@10, All-Recall@k (multi-authority questions),
  CR/CP/**CFP** on generated answers (exact on a closed corpus). LRAGE
  discipline: every config cell (scope × retriever × k) reported against a
  no-retrieval baseline.
- **Diagnostic suite** (from 2606.09724): ancestor-closure (never a subsection
  without its parent), descendant-completeness ("all subsections of s.X" is
  exhaustive, not top-K), point-in-time recovery, provenance reconstruction,
  claim-level auditability — run as unit tests, not benchmarks.
- **Secondary judged layer:** per-question rubrics drafted from the gold
  authority's own reasoning, lawyer-verified on 10, "cites the correct section"
  mandatory (2504.01840).

## 8. Build order

| Phase | Deliverable | Effort |
| --- | --- | --- |
| **P1 — Graph + temporal layer** | `edges.csv` (unified, metadata-as-nodes), `sections.jsonl` versions, `actions.csv` for the 18 amendments, `aliases.csv`, `authority.csv` | days — file joins over what exists |
| **P2 — Engine core** | the typed primitives + BM25 (rank_bm25) + router tables + ranking; CLI: `draftly ask "…"` returning cited answers | the heart; small |
| **P3 — Eval harness** | gold set v1 (30 auto + seed lawyer set), metrics, ablation grid, diagnostic unit tests | proves it works; feeds the report |
| **P4 — Bounded-LLM passes** | 62k disambiguation queue → validated links; `rules.csv` (headnote-first, then 1,418 quote-backed) | the enrichment |
| **P5 — Multi-hop polish + integration** | PPR tuning on gold set, NyayGraph expansion, collapsed pool; wire to `legal-source-lookup` skill + the POC "Relevant Law & Authority" panel | |
| **P6 — Lawyer verification loop** | verification-sample sign-off → promote links/rules `unverified → verified`; measure per-method precision | the trust gate |

Dense embeddings (bge-small, local) enter **only if** P3's gold set shows recall
gaps that lexical + graph can't close — as a linking fallback, never the primary
path.

## 9. One-paragraph summary (for the report / supervisor)

Draftly's retrieval engine is a **deterministic, authority-aware hybrid** over a
closed legal corpus: curated topic partitions scope the search (empirically worth
double-digit retrieval gains), a ground-truth citation graph provides multi-hop
reasoning via Personalized PageRank (adopting HippoRAG's walk while discarding
its noisy LLM-built graph), a dated section-version model with amendment Action
nodes answers point-in-time questions deterministically (adopting SAT-Graph RAG),
BM25 supplies lexical recall inside scopes, and a bounded, validated LLM handles
only closed-set disambiguation and quote-backed rule extraction. Judicial-
hierarchy-aware ranking (SC binding > CoA binding-below > persuasive) is, to our
knowledge, absent from the published hybrid legal-RAG literature — it is the
engine's most novel contribution, alongside the first open case→statute-section
citation graph for Sri Lankan conveyancing law.
