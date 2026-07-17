# Draftly — Research Papers

Reading list behind Draftly's retrieval design and OCR choices, split into two
folders: **`ocr/`** (OCR workstream) and **`data/`** (retrieval / legal-data
workstream). Verified against arXiv metadata (`scripts/download_papers.py`); machine
index in `download-index.csv`. Treat the PDFs as the primary source.

## RAG foundations

- **Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks** — `2005.11401` · [PDF](data/2005.11401-retrieval-augmented-generation-for-knowledge-intensive-.pdf)
- **Improving language models by retrieving from trillions of tokens** — `2112.04426` · [PDF](data/2112.04426-improving-language-models-by-retrieving-from-trillions-.pdf)
- **Atlas: Few-shot Learning with Retrieval Augmented Language Models** — `2208.03299` · [PDF](data/2208.03299-atlas-few-shot-learning-with-retrieval-augmented-langua.pdf)
- **Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection** — `2310.11511` · [PDF](data/2310.11511-self-rag-learning-to-retrieve-generate-and-critique-thr.pdf)

## Hierarchical / tree retrieval (our index shape)

- **Walking Down the Memory Maze: Beyond Context Limit through Interactive Reading** — `2310.05029` · [PDF](data/2310.05029-walking-down-the-memory-maze-beyond-context-limit-throu.pdf)
- **RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval** — `2401.18059` · [PDF](data/2401.18059-raptor-recursive-abstractive-processing-for-tree-organi.pdf)
- **BookRAG: A Hierarchical Structure-aware Index-based Approach for Retrieval-Augmented Generation on Complex Documents** — `2512.03413` · [PDF](data/2512.03413-bookrag-a-hierarchical-structure-aware-index-based-appr.pdf)

## Graph-based retrieval (case↔statute graph)

- **From Local to Global: A Graph RAG Approach to Query-Focused Summarization** — `2404.16130` · [PDF](data/2404.16130-from-local-to-global-a-graph-rag-approach-to-query-focu.pdf)
- **HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models** — `2405.14831` · [PDF](data/2405.14831-hipporag-neurobiologically-inspired-long-term-memory-fo.pdf)
- **LightRAG: Simple and Fast Retrieval-Augmented Generation** — `2410.05779` · [PDF](data/2410.05779-lightrag-simple-and-fast-retrieval-augmented-generation.pdf)

## Agent memory

- **MemGPT: Towards LLMs as Operating Systems** — `2310.08560` · [PDF](data/2310.08560-memgpt-towards-llms-as-operating-systems.pdf)

## Legal RAG · knowledge graphs · holding/statute linking · eval

- **2025.nllp-1.11-nyaygraph-legal-statute-kg.pdf** — `2025.nllp-1.11.pdf` · [PDF](data/2025.nllp-1.11-nyaygraph-legal-statute-kg.pdf)
- **CLERC: A Dataset for Legal Case Retrieval and Retrieval-Augmented Analysis Generation** — `2406.17186` · [PDF](data/2406.17186-clerc-a-dataset-for-legal-case-retrieval-and-retrieval-.pdf)
- **Bridging Legal Knowledge and AI: Retrieval-Augmented Generation with Vector Stores, Knowledge Graphs, and Hierarchical Non-negative Matrix Factorization** — `2502.20364` · [PDF](data/2502.20364-bridging-legal-knowledge-and-ai-retrieval-augmented-gen.pdf)
- **LRAGE: Legal Retrieval Augmented Generation Evaluation Tool** — `2504.01840` · [PDF](data/2504.01840-lrage-legal-retrieval-augmented-generation-evaluation-t.pdf)
- **An Ontology-Driven Graph RAG for Legal Norms: A Structural, Temporal, and Deterministic Approach** — `2505.00039` · [PDF](data/2505.00039-an-ontology-driven-graph-rag-for-legal-norms-a-structur.pdf)
- **UQLegalAI@COLIEE2025: Advancing Legal Case Retrieval with Large Language Models and Graph Neural Networks** — `2505.20743` · [PDF](data/2505.20743-uqlegalai-coliee2025-advancing-legal-case-retrieval-wit.pdf)
- **The Missing Link: Joint Legal Citation Prediction using Heterogeneous Graph Enrichment** — `2506.22165` · [PDF](data/2506.22165-the-missing-link-joint-legal-citation-prediction-using-.pdf)
- **IL-PCSR: Legal Corpus for Prior Case and Statute Retrieval** — `2511.00268` · [PDF](data/2511.00268-il-pcsr-legal-corpus-for-prior-case-and-statute-retriev.pdf)
- **Domain-Partitioned Hybrid RAG for Legal Reasoning: Toward Modular and Explainable Legal AI for India** — `2602.23371` · [PDF](data/2602.23371-domain-partitioned-hybrid-rag-for-legal-reasoning-towar.pdf)
- **Beyond Probabilistic Similarity: Structural, Temporal, and Causal Limitations of Retrieval-Augmented Generation in the Legal Domain** — `2606.09724` · [PDF](data/2606.09724-beyond-probabilistic-similarity-structural-temporal-and.pdf)

## Sinhala / legal-document OCR

- **Deciphering the Underserved: Benchmarking LLM OCR for Low-Resource Scripts** — `2412.16119` · [PDF](ocr/2412.16119-deciphering-the-underserved-benchmarking-llm-ocr-for-lo.pdf)
- **Zero-shot OCR Accuracy of Low-Resourced Languages: A Comparative Analysis on Sinhala and Tamil** — `2507.18264` · [PDF](ocr/2507.18264-zero-shot-ocr-accuracy-of-low-resourced-languages-a-com.pdf)
- **Sri Lanka Document Datasets: A Large-Scale, Multilingual Resource for Law, News, and Policy** — `2510.04124` · [PDF](ocr/2510.04124-sri-lanka-document-datasets-a-large-scale-multilingual-.pdf)
- **SinhaLegal: A Benchmark Corpus for Information Extraction and Analysis in Sinhala Legislative Texts** — `2603.04854` · [PDF](ocr/2603.04854-sinhalegal-a-benchmark-corpus-for-information-extractio.pdf)
- **Cross-Temporal Sinhala OCR: Page-Level Adaptation and Diachronic Analysis** — `2606.29378` · [PDF](ocr/2606.29378-cross-temporal-sinhala-ocr-page-level-adaptation-and-di.pdf)
