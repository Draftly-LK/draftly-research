# Graph and hierarchical RAG: reading notes

Papers collected 2026-07-19 for the statute-level QA agent. PDFs live in this
folder (`papers/qa-agent/`), named `<arxivid>-<slug>.pdf`. Context: closed corpus
of ~85 Sri Lankan conveyancing statutes in markdown with section structure, an
existing statute section index, and a 14,665-edge case-to-statute-section
citation graph.

## RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval

- arXiv: 2401.18059 (2024, ICLR 2024)
- File: `2401.18059-raptor.pdf`

RAPTOR builds a tree over a flat chunked corpus bottom-up: it embeds chunks,
clusters them with Gaussian mixture models over UMAP-reduced embeddings, has an
LLM summarize each cluster, then repeats on the summaries until one root remains.
At query time the "collapsed tree" strategy searches all levels at once, so a
question can match either a fine-grained leaf or a mid-level summary. The tree is
synthetic: cluster membership and summaries both come from models, not from any
structure in the source document. Reported gains: 20% absolute accuracy over
retrieval baselines on QuALITY with GPT-4, plus state-of-the-art results on
NarrativeQA and QASPER.

Relevance to a closed-corpus statute QA agent: the multi-granularity retrieval
idea transfers, but statutes already have the tree (act, part, section,
subsection), so clustering should be replaced by the real hierarchy and only the
per-node summarization step kept.

## GraphRAG: From Local to Global (Microsoft)

- arXiv: 2404.16130 (2024)
- File: `2404.16130-graphrag-local-to-global.pdf`

An LLM pass over all chunks extracts entities, relationships, and claims into a
knowledge graph. Leiden community detection partitions the graph into a hierarchy
of communities, and the LLM writes a summary for each community. Global
"sensemaking" questions are answered map-reduce style: every relevant community
summary produces a partial answer, which a final call merges. Reported gains:
70-80% head-to-head win rates on comprehensiveness and diversity against vector
RAG on ~1M-token corpora; the paper does not target precise fact lookup, and
indexing cost is high because every chunk passes through the LLM.

Relevance to a closed-corpus statute QA agent: the community-summary idea only
pays off for broad survey questions ("how do these statutes treat X overall");
for exam-style section-specific questions the LLM-built entity graph adds noise
and cost over the deterministic structure already in hand.

## HippoRAG: Neurobiologically Inspired Long-Term Memory

- arXiv: 2405.14831 (2024, NeurIPS 2024)
- File: `2405.14831-hipporag.pdf`

Modeled on hippocampal indexing theory. Offline, an LLM runs open information
extraction over passages to build a schemaless phrase-node graph, with synonym
edges added by an embedding model. Online, query entities are linked to graph
nodes and Personalized PageRank spreads activation from those seeds; passages are
ranked by the summed scores of their nodes. This makes multi-hop retrieval a
single graph operation instead of an iterative retrieve-reason loop. Reported
gains: up to ~20% over strong retrievers on MuSiQue and 2WikiMultiHopQA in
single-step mode, while being 10-30x cheaper and 6-13x faster than IRCoT.

Relevance to a closed-corpus statute QA agent: the PPR-over-a-graph retrieval
step is directly reusable, and it works even better when the edges are
deterministic (cross-references, citations) instead of noisy OpenIE triples.

## LightRAG: Simple and Fast Retrieval-Augmented Generation

- arXiv: 2410.05779 (2024)
- File: `2410.05779-lightrag.pdf`

LightRAG also extracts an entity-relation graph with an LLM, but stores each
entity and relation as a key-value pair whose value is a short textual profile.
Retrieval is dual-level: the query is decomposed into low-level keywords (matched
to entities) and high-level keywords (matched to relations and themes), and both
result sets are merged with their one-hop neighborhoods. The index supports
incremental updates without a full rebuild. Reported gains: beats GraphRAG on
comprehensiveness and diversity win rates across four domains at a fraction of
the token cost and API calls.

Relevance to a closed-corpus statute QA agent: the dual-level query decomposition
(specific section lookup vs. thematic question) is the useful part; the LLM-built
entity graph itself is again replaceable by the statute structure.

## HippoRAG 2: From RAG to Memory

- arXiv: 2502.14802 (2025)
- File: `2502.14802-hipporag2-rag-to-memory.pdf`

HippoRAG 2 keeps the OpenIE graph plus Personalized PageRank backbone and fixes
HippoRAG's weakness on simple factual questions. It adds passage nodes to the
graph alongside phrase nodes (so dense passage retrieval and graph search
reinforce each other), links queries to whole triples rather than just entities,
and inserts an LLM "recognition memory" filter that discards bad seed triples
before PPR runs. Reported gains: +7 points over the strongest embedding retriever
(NV-Embed-v2) on associative multi-hop tasks while matching it on factual and
sense-making QA, and it outperforms GraphRAG, LightRAG, and RAPTOR across all
three question categories.

Relevance to a closed-corpus statute QA agent: the design lesson is to combine
dense retrieval with graph propagation in one scoring pass and to filter seeds
before propagating; both apply directly to a section index plus citation graph.

## HiRAG: Retrieval-Augmented Generation with Hierarchical Knowledge

- arXiv: 2503.10150 (2025, EMNLP 2025 Findings)
- File: `2503.10150-hirag-hierarchical-knowledge.pdf`

HiRAG builds an LLM-extracted knowledge graph, then adds hierarchy: entity
embeddings are clustered (GMM) and the LLM generates summary entities for each
cluster, layer by layer, so semantically similar but structurally distant
entities become connected through higher layers. Retrieval returns local
entity-level evidence, global community-level evidence, and "bridge" paths that
connect the two across layers. Reported gains: higher win rates than GraphRAG,
LightRAG, and FastGraphRAG on multi-domain QA benchmarks.

Relevance to a closed-corpus statute QA agent: confirms that hierarchy in the
index is what closes the local-vs-global gap, but its synthetic layers are an
expensive approximation of the part/section hierarchy statutes already declare.

## SAT-Graph RAG: An Ontology-Driven Graph RAG for Legal Norms

- arXiv: 2505.00039 (2025, Hudson de Martim)
- File: `2505.00039-sat-graph-rag-legal-norms.pdf`

A structural, temporal, and deterministic graph model for legislation, grounded
in an LRMoo/FRBR-style ontology. Abstract norms (Works) are distinguished from
their versioned texts (Expressions); articles, paragraphs, and items are
first-class hierarchical component nodes; temporal states are aggregations that
reuse the versions of unchanged components; and amendment events are reified as
Action nodes so causality and point-in-time questions become graph queries. The
graph is built deterministically from document structure, not from LLM
extraction, so retrieval provenance is exact. This is an architecture paper: it
reports no QA benchmark numbers, and its value is the data model.

Relevance to a closed-corpus statute QA agent: the closest blueprint in this
list; the structural component modeling maps one-to-one onto the markdown
section tree, and the temporal layer matters only if amended statute versions
enter the corpus.

## BookRAG: Hierarchical Structure-Aware Index for Complex Documents

- arXiv: 2512.03413 (2025)
- File: `2512.03413-bookrag.pdf`

BookRAG targets documents with an intrinsic hierarchy (books, handbooks). Its
BookIndex has three parts: a tree extracted from the document's logical
structure (its table of contents), an entity graph capturing relations in the
text, and a mapping from entities to tree nodes so the two views stay linked. An
agent-based query method grounded in Information Foraging Theory classifies each
query and picks a tailored retrieval workflow over the tree and graph (for
example, fact lookup vs. summary). Reported gains: state-of-the-art retrieval
recall and QA accuracy on three benchmarks against GraphRAG-family baselines,
at competitive cost.

Relevance to a closed-corpus statute QA agent: the strongest overall template
here; replace "table of contents" with the statute section tree and route
queries the same way.

## DeepRead: Document Structure-Aware Reasoning for Agentic Search

- arXiv: 2602.05014 (2026)
- File: `2602.05014-deepread-structure-aware-agentic-search.pdf`

DeepRead argues that chunk retrieval throws away document organization, and
instead builds a paragraph-level, coordinate-based navigation system over the
document hierarchy. The LLM agent gets two tools: Retrieve, which localizes
relevant coordinates, and ReadSection, which reads sequentially within a
structural scope, producing a locate-then-read loop that mirrors how people scan
then read. No knowledge graph is constructed at all; the index is the document
structure itself. Reported gains: +10.3% on average over Search-o1-style agentic
search baselines across four benchmarks, with analysis showing the agent adopts
human-like reading strategies.

Relevance to a closed-corpus statute QA agent: locate-then-read over a section
index is exactly the right interaction pattern for exam questions that hinge on
reading a full section with its provisos rather than an isolated chunk.

## LegalGraphRAG: Multi-Agent Graph RAG for Reliable Legal Reasoning

- arXiv: 2605.28120 (2026, ACL 2026)
- File: `2605.28120-legalgraphrag.pdf`

Addresses the heterogeneity of legal corpora (cases, articles, interpretations)
with two components. First, a hierarchical legal graph organizes sources at
multiple abstraction levels so retrieval can enter at the right granularity.
Second, a multi-agent pipeline separates roles: a Researcher retrieves candidate
evidence, an Auditor verifies each piece against the source documents before it
is admitted, and an Adjudicator synthesizes only the verified evidence into a
judgment. Reported gains: state-of-the-art over GraphRAG baselines on legal
reasoning benchmarks, with the audit step credited for the reliability gain.

Relevance to a closed-corpus statute QA agent: the audit step (verify every
claimed section citation against the actual section text before answering) is a
cheap, high-value addition given the corpus is small and every section is
addressable.

## Recommendation: index design for the 85-statute corpus

The corpus is small, closed, and already structured. That inverts the economics
of most of these papers: their hardest problem, building a reliable graph from
unstructured text with an LLM, is already solved here deterministically. The
design that should give the highest answer precision on exam-style questions:

1. Structural backbone (deterministic, copy from SAT-Graph RAG and BookRAG).
   Parse the markdown into an explicit tree: statute, part, section, subsection,
   schedule. Every node carries its canonical citation string (act number, year,
   section) and full text. This is the primary retrieval unit; never retrieve a
   chunk without its section path.
2. Deterministic edge layer (copy HippoRAG's retrieval, skip its extraction).
   Three edge types, none LLM-built: (a) parent/child and sibling edges from the
   tree; (b) cross-reference edges parsed with regex from section text
   ("section 12", "Act No. 7 of 1871", "this Ordinance"); (c) the existing
   14,665 case-to-section citation edges, usable both as an importance prior
   (frequently cited sections rank higher on ties) and as a bridge for questions
   that mention a case. Run Personalized PageRank over this graph with the
   dense-retrieval seeds, as HippoRAG 2 does over its noisier graph.
3. Summary layer (RAPTOR's idea on the real tree, not a clustered one).
   One LLM-written summary per statute and per part, stored as extra retrievable
   nodes. This handles the minority of broad comparison questions without paying
   for GraphRAG-style community detection. Skip full GraphRAG/LightRAG/HiRAG
   entity extraction: on 85 statutes it adds cost and hallucinated edges while
   duplicating information the tree and cross-references already encode.
4. Query routing and reading (copy BookRAG and DeepRead). Classify each
   question: direct section lookup, multi-section synthesis, or case-linked.
   For lookups, hybrid BM25 + dense retrieval over section nodes, then expand
   one hop through tree and cross-reference edges so definitions sections and
   provisos come along. Give the agent a ReadSection tool that returns a full
   section (or its parent part) verbatim, so it reads complete legal text
   instead of embedding-truncated chunks.
5. Verification (copy LegalGraphRAG's Auditor). Before finalizing an answer,
   check every cited section id against the index and confirm the quoted or
   paraphrased text appears in that section. With a closed corpus this is a
   string lookup, and it converts most residual hallucinations into detectable
   failures.

What to skip: LLM-built entity graphs (GraphRAG, LightRAG, HiRAG, and the graph
half of BookRAG), GraphRAG community detection, RAPTOR's clustering, and
SAT-Graph's temporal versioning unless amended consolidations are added later.
What to copy: SAT-Graph's deterministic structural node model, HippoRAG/
HippoRAG 2's PPR-with-dense-seeds retrieval, RAPTOR's summaries applied to real
hierarchy nodes, BookRAG's query routing, DeepRead's locate-then-read tools, and
LegalGraphRAG's citation audit.
