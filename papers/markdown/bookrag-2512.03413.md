## BookRAG: A Hierarchical Structure-aware Index-based Approach for Retrieval-Augmented Generation on Complex Documents

Shu Wang

The Chinese University of Hong

Kong, Shenzhen shuwang3@link.cuhk.edu.cn

## Abstract

As an effective method to boost the performance of Large Language Models (LLMs) on the question answering (QA) task, RetrievalAugmented Generation (RAG), which queries highly relevant information from external complex documents, has attracted tremendous attention from both industry and academia. Existing RAG approaches often focus on general documents, and they overlook the fact that many real-world documents (such as books, booklets, handbooks, etc.) have a hierarchical structure, which organizes their content from different granularity levels, leading to poor performance for the QA task. To address these limitations, we introduce BookRAG, a novel RAG approach targeted for documents with a hierarchical structure, which exploits logical hierarchies and traces entity relations to query the highly relevant information. Specifically, we build a novel index structure, called BookIndex, by extracting a hierarchical tree from the document, which serves as the role of its table of contents, using a graph to capture the intricate relationships between entities, and mapping entities to tree nodes. Leveraging the BookIndex, we then propose an agent-based query method inspired by the Information Foraging Theory, which dynamically classifies queries and employs a tailored retrieval workflow. Extensive experiments on three widely adopted benchmarks demonstrate that BookRAG achieves state-of-the-art performance, significantly outperforming baselines in both retrieval recall and QA accuracy while maintaining competitive efficiency.

## 1 Introduction

Large Language Models (LLMs) such as Qwen 3 [60] and Gemini 2.5 [13] have revolutionized the Question Answering (QA) system [15, 61, 65]. The industry has increasingly adopted LLMs to build QA systems that assist users and reduce manual effort in many applications [65, 67], such as financial auditing [29, 37], legal compliance [8], and scientific discovery [56]. However, directly relying on LLMs may lead to missing domain knowledge and generating outdated or unsupported information. To address these issues, Retrieval-Augmented Generation (RAG) has been widely adopted [17, 22] by retrieving relevant domain knowledge from external sources and using it to guide the LLM during response generation. On the other hand, in real-world enterprise scenarios, domain knowledge is often stored in long-form documents, such as technical handbooks, API reference manuals, and operational guidebooks [49]. A notable feature of such documents is that they follow the structure of books, characterized by intricate layouts and rigorous logical hierarchies (e.g., explicit tables of contents, nested chapters, and multi-level sections). In this paper, we aim to design an effective RAG system for QA over long and highly structured documents.

Yingli Zhou

The Chinese University of Hong Kong, Shenzhen yinglizhou@link.cuhk.edu.cn Yixiang Fang The Chinese University of Hong Kong, Shenzhen fangyixiang@cuhk.edu.cn

Figure 1: Comparison of existing methods and BookRAG for complex document QA.

<!-- image -->

· Prior works. The existing RAG approaches for documentlevel QA generally fall into two paradigms, as illustrated in Figure 1. The first paradigm relies on OCR (Optical Character Recognition) to convert the document into plain text, after which any text-based RAG method can be directly applied. Among text-based RAG methods, state-of-the-art approaches increasingly adopt graph-based RAG [6, 62, 66], where graph data serves as an external knowledge source because it captures rich semantic information and the relational structure between entities. As shown in Table 1, two representative methods are GraphRAG [16] and RAPTOR [45]. Specifically, GraphRAG first constructs a knowledge graph (KG) from the textual corpus, and then applies the Leiden community detection algorithm [51] to obtain hierarchical clusters. Summaries are generated for each community, providing a comprehensive, global overview of the entire corpus. RAPTOR builds a recursive tree structure by iteratively clustering document chunks and summarizing them at each level, enabling the model to capture both fine-grained and high-level semantic information across the corpus.

In contrast, the second paradigm, layout-aware segmentation [5, 52], first parses the document into structured blocks that preserve the original layout and information of the document, such as paragraphs, tables, figures, or equations. By doing so, it not only avoids the fixed chunk size used in the first paradigm, which often leads to fragmented information, but also retains document-native structural information. These blocks often exhibit multimodal characteristics, and a typical approach is to apply multimodal retrieval to obtain relevant content for answering queries. Recently, a state-ofthe-art method in this category, DocETL [47], provides a declarative interface that allows users to manually define LLM-based processing pipelines to analyze the retrieved blocks. These pipelines consist of LLM-powered operations combined with task-specific optimizations.

Table 1: Comparison of representative methods and our BookRAG.

| Type             | Representative Method     | Core Feature                                                 | Multi-hop Reasoning   | Document Parsing   | Query Workflow   |
|------------------|---------------------------|--------------------------------------------------------------|-----------------------|--------------------|------------------|
| Graph-based      | RAPTOR [45] GraphRAG [16] | Recursive summarization Global community detection           |                       |                    | Static Static    |
| Layout segmented | MM-Vanilla DocETL [47]    | Multi-modal retrieval LLM-based document processing pipeline |                       |                    | Static Manual    |
| Doc-Native       | BookRAG (Ours)            | Structure-award Index & Agent-based retrieval                |                       |                    | Dynamic          |

· Limitations of existing works. However, these methods suffer from two fundamental limitations ( L for short): L1: Failure to capture the deep connection of document structure and semantics. Text-based approaches cannot capture the structural layout of the document, resulting in the loss of important relationships stored in the hierarchical blocks, such as tables nested within a specific section. While layout-segmented methods preserve document structure, they cannot capture the relationships between different blocks in the document, which limits their capability for multi-hop reasoning across these blocks and ultimately affects their overall performance. L2: Static of query workflows. In real-world QA scenarios, user queries are highly heterogeneous, ranging from simple keyword lookups to complex multi-hop questions that require synthesizing evidence scattered across different parts of the document. Applying a uniform strategy, such as static or manually predefined workflows, to diverse needs is inefficient; for example, complex queries often require question decomposition, whereas simple queries do not.

· Our technical contributions. To bridge this gap, we introduce BookRAG , the first retrieval-augmented generation method built upon a document-native BookIndex , designed to document QA tasks. Specifically, to capture the deep connection of the relation in the document, BookIndex organizes information through two complementary structures. First, to preserve the document's native logical hierarchy, we organize the parsed content blocks into a hierarchical tree structure, which serves as the role of its table of contents. Second, to capture the intricate relations within these blocks, we construct a KG containing fine-grained entities. Finally, we unify these two structures by mapping the KG entities to their corresponding tree nodes.

However, effective multi-hop reasoning on the graph relies on a high-quality KG [62, 66], which is often compromised by entity ambiguity (e.g., distinct entities with names like 'LLM' and 'Large Language Model'). To address this, we propose a novel gradient-based entity resolution method that analyzes the similarity distribution of candidate entities. By identifying sharp drops in similarity scores, we can efficiently distinguish and merge coreferent entities, thereby ensuring graph connectivity and enhancing reasoning capabilities.

Building upon the BookIndex, we address the static of query workflows ( L2 ) by implementing an agent-based retrieval . Specifically, our agent first classifies user queries based on their intent and complexity, and then dynamically generates tailored retrieval workflows. Grounded in Information Foraging Theory [42], our retrieval process mimics foraging by using Selector to narrow down the search space via information scents and Reasoner to locate highly relevant evidence.

We conduct extensive experiments on three widely adopted datasets to validate the effectiveness and efficiency of our BookRAG, comparing it against several state-of-the-art baselines. The experimental results demonstrate that BookRAG consistently achieves superior performance in both retrieval recall and QA accuracy across all datasets. Furthermore, our detailed analysis validates the critical contributions of our key features, such as the high-quality KG and the agent-based retrieval mechanism.

We summarize our contributions as:

- We introduce BookRAG , a novel method that constructs a document-native BookIndex by integrating a hierarchical tree of document layout blocks with a KG storing finegrained entity relations.
- We propose an Agent-based Retrieval approach inspired by Information Foraging Theory, which dynamically classifies queries and configures optimal retrieval workflows to locate highly relevant evidence within documents.
- Extensive experiments on multiple benchmarks show that BookRAG significantly outperforms existing baselines, attaining state-of-the-art performance in solving complex document QA tasks while maintaining competitive efficiency.

Outline. We review related work in Section 2. Section 3 introduces the problem formulation, IFT, and RAG workflow. In Section 4, we present the structure of our BookIndex and its construction. Section 5 presents our agent-based retrieval, elaborating on the query classification and operators used in the structured execution of BookRAG. We present the experimental results and detailed analysis in Section 6, and conclude the paper in Section 7.

## 2 Related Work

In this section, we review the related works, including LLM in document analysis and the modern representative RAG approaches.

- LLM in document analysis. Recent advances in LLMs have offered opportunities to leverage LLMs in document data analysis. Due to the robust semantic reasoning capabilities of LLMs, there is an increasing number of works focusing on transferring unstructured documents (e.g., HTML, PDFs, and raw text) into structured formats, such as relational tables [1, 7, 25, 38]. For example, Evaporate [1] utilizes LLMs to synthesize extraction code, enabling cost-effective conversion of semi-structured web documents into structured databases without heavy manual annotation. In addition, several LLM-based document analysis systems have been proposed to equip standard data pipelines with semantic understanding [28, 40, 47, 53]. For instance, LOTUS [40] extends the relational model with semantic operators, allowing users to execute SQL-like queries with LLM-powered predicates (e.g., filter, join) over unstructured text corpora. Similarly, DocETL [47] introduces an agentic framework to optimize complex information extraction tasks. Furthermore, another line of research proposes to directly analyze or parse documents by viewing the document pages as images, thereby preserving critical layout and visual information [26, 31, 54].

· RAG approaches. RAG has been proven to excel in many tasks, including open-ended question answering [24, 48], programming context [9, 10], SQL rewrite [30, 50], and data cleaning [35, 36, 43]. The naive RAG technique relies on retrieving query-relevant contexts from external knowledge bases to mitigate the 'hallucination' of LLMs. Recently, many RAG approaches [16, 18, 19, 21, 27, 32, 32, 45, 55, 58, 66] have adopted graph structures to organize the information and relationships within documents, achieving improved overall retrieval performance. For more details, please refer to the recent survey of graph-based RAG methods [41]. Besides, the Agentic RAG paradigm has been widely studied, employing autonomous agents to dynamically orchestrate and refine the RAG pipeline, thus significantly boosting the reasoning robustness and generation fidelity [2, 23, 59].

## 3 Preliminaries

This section formalizes the research problem of complex document QA, introduces the foundational Information Foraging Theory (IFT), and briefly reviews the general workflow of RAG systems

## 3.1 Problem Formulation

We study the problem of Question Answering (QA) over complex documents, which aims to answer user queries based on long-form documents [5, 11, 33]. Formally, a document 𝐷 is represented as a sequence of 𝑁 pages, 𝐷 = { 𝑃 𝑖 } 𝑁 𝑖 = 1 . These pages collectively contain a sequence of content blocks B = { 𝑏 𝑗 } 𝑀 𝑗 = 1 , where each block 𝑏 𝑗 represents a distinct element (e.g., text segment, section header, table, or image) organized within a logical chapter hierarchy. Given a user query 𝑞 , the goal is to generate an accurate answer 𝐴 , ideally grounded in a specific set of evidence blocks 𝐸 ⊂ B . The task is formulated as developing a method S that maps the structured document and the query to the final answer:

<!-- formula-not-decoded -->

where S should navigate both the sequential page content and the logical hierarchy of 𝐷 to synthesize the response.

## 3.2 Information Foraging Theory

Information Foraging Theory (IFT) [42] provides a framework for understanding information access as a process analogous to animal foraging. It suggests that users follow cues, known as information scent (e.g., keywords or icons), to navigate between clusters of content, known as information patches (e.g., sections in handbooks). The goal is to maximize the rate of valuable information gain while minimizing effort, guiding the decision to either stay within a patch or seek a new one.

Consider experts seeking a solution to a specific problem within a large technical handbook. They first extract key terms related to the problem, which act as information scent. This scent guides them to navigate towards one or more promising sections (the information patches). Within these patches, they analyze the diverse content to extract the precise knowledge required to formulate a final answer

## 3.3 RAG workflow

Retrieval-Augmented Generation (RAG) systems typically operate in a two-phase framework [6, 16, 41]. In the Offline Indexing phase, unstructured corpus data is organized into a structured index, which can take various forms such as vector databases or KG [66]. Subsequently, in the Online Retrieval phase, the system retrieves relevant components (e.g., text chunks or subgraphs) based on the user query 𝑞 to inform the LLM's generation. However, these general workflows often treat the index as a structure derived purely from content, potentially detaching it from the document's original logical hierarchy. In contrast, our approach seeks to deeply integrate these retrieval structures with the document's native tree topology.

## 4 BookIndex

This section introduces our proposed BookIndex , a hierarchical structure-aware index designed to capture both the explicit logical hierarchy and the intricate entity relations within complex documents. We first formally define the structure of the BookIndex ( 𝐵 ). Subsequently, we elaborate on the sequential, two-stage construction process: (1) Tree Construction , which parses the document's layout to establish a hierarchical nodes, each categorized by type; and (2) Graph Construction , which extracts fine-grained entity knowledge from the tree nodes and refines it through a novel gradient-based entity resolution method.

## 4.1 Overview of BookIndex

We formally define our BookIndex as a triplet 𝐵 = ( 𝑇,𝐺, 𝑀 ) . Here, 𝑇 = ( 𝑁, 𝐸 𝑇 ) represents a Tree structure where 𝑁 is the set of nodes derived from the document's explicit logical hierarchy (e.g., titles, sections, tables), and 𝐸 𝑇 denotes their nesting relationships. 𝐺 = ( 𝑉, 𝐸 𝐺 ) is a Knowledge Graph that captures fine-grained entities ( 𝑉 ) and their relations ( 𝐸 𝐺 ) scattered throughout the document. Finally, 𝑀 : 𝑉 →P( 𝑁 ) is the Graph-Tree Link (GT-Link) , which links each entity in 𝑉 to the set of specific tree nodes in 𝑁 from which it was extracted. These links are crucial for capturing the intricate, cross-sectional relations within the document. The hierarchical tree nodes in 𝑇 serve as the document's native information patches , providing structured contexts for information seeking. Meanwhile, the entities and relations in 𝐺 , connected via 𝑀 , act as the rich information scent that guides navigation between and within these patches.

Figure 2: The BookIndex Construction process. This phase includes Tree Construction, derived from Layout Parsing and Section Filtering, and Graph Construction, which involves KG Construction and Gradient-based Entity Resolution.

<!-- image -->

Figure 2 provides an example of our BookIndex. The Tree component, positioned at the top, organizes the document into a hierarchical structure, where content blocks such as text, tables, and images serve as leaf nodes nested within section nodes. The Graph component is composed of entities and relations extracted from these nodes. The GT-Link, illustrated by the blue dotted lines, explicitly connects these entities back to their corresponding tree nodes, thereby grounding the semantic entities within the document's logical hierarchy.

## 4.2 Tree Construction

The first stage transforms the raw document into a structured hierarchical tree 𝑇 . This involves two key steps: robust layout parsing and intelligent section filtering.

- 4.2.1 Layout Parsing. The Layout Parsing phase processes the input document 𝐷 (a collection of pages) using layout analysis and recognition models. This step identifies, extracts, and organizes diverse blocks (e.g., text, tables, images) from the document pages. The output is a sequence of primitive blocks, B = { 𝑏 1 , 𝑏 2 , · · · , 𝑏 𝑘 } , where each block 𝑏 𝑖 = ( 𝑐 𝑖 , 𝜏 𝑖 , 𝑓 𝑖 ) is defined as a triplet. Here, 𝑐 𝑖 is the raw content (e.g., text, image data), 𝜏 𝑖 is the initial layout-based type (e.g., Title, Text, Table, Image ), and 𝑓 𝑖 is a vector of associated layout features (e.g., 'FontSize', bounding box).
- 4.2.2 Section Filtering. Next, the Section Filtering phase processes this initial sequence to identify the document's logically hierarchical structure. Layout Parsing identifies blocks as Title but does not assign their hierarchical level. Therefore, we select the candidate subset B title ⊂ B (where 𝜏 𝑖 = Title ) for an LLM-based analysis. To handle extremely long documents, this analysis is performed in batches, where each batch retains a contextual window of high-level

section information (with 𝑙 = 1 as the root). The LLM analyzes the content 𝑐 𝑖 and layout features 𝑓 𝑖 of the candidates to determine two key properties: their actual hierarchical level 𝑙 𝑖 ∈ { 1 , 2 , ... } and final node type 𝜏 ′ 𝑖 (e.g., re-classifying an erroneous Title as Text if its level is 'None'). This step is crucial for preserving the document's logical hierarchy by correcting blocks erroneously parsed as Title , such as descriptive text within images or borderless table headers.

Finally, the definitive tree 𝑇 = ( 𝑁, 𝐸 𝑇 ) is constructed. The node set 𝑁 is composed of all blocks from the filtering and re-classification process, where each node 𝑛 ∈ 𝑁 retains its content ( 𝑐 𝑖 ) and its final node type ( 𝜏 ′ 𝑖 ) (e.g., Text , Section , Table , and Image ). The edge set 𝐸 𝑇 , representing the parent-child nesting relationships, is then established. Parent-child relationships are inferred by sequentially traversing the nodes, using both the determined hierarchical levels ( 𝑙 𝑖 ) of Section nodes and the overall document order to assemble the complete tree structure.

As an example shown in Figure 2, the Layout Parsing phase identifies diverse blocks, typing them as Title , Text , Table , and Image . During the Section Filtering phase, the Title candidates (e.g., "Method", "Experiment", and "MOE Layer") are analyzed by the LLM. The blocks 'Method' and 'Experiment' (both with 'FontSize: 14') are correctly identified as Section nodes at 'Level: 2'. Conversely, the 'MOE Layer' block ('FontSize: 20'), which was erroneously tagged as Title by the parser, is re-classified by the LLM as a Text node with 'Level: None'. This correction is crucial for preserving the document's logical hierarchy. Following this process, all filtered and classified nodes are assembled into the final tree structure based on their determined levels and document order.

## 4.3 Graph Construction

Once the tree 𝑇 is established, we proceed to populate the Knowledge Graph 𝐺 by extracting and refining entities from the tree nodes.

```
Input: KG 𝐺 , New entity 𝑣 𝑛 , Rerank model R , Entity vector database 𝐷𝐵 , Vector search number 𝑡𝑜𝑝 _ 𝑘 , threshold of gradient 𝑔 // Vector Search 𝑡𝑜𝑝 _ 𝑘 relevant entities in 𝐷𝐵 . 1 𝐸 𝑐 ← Search( 𝐷𝐵, 𝑣 𝑛 , 𝑡𝑜𝑝 _ 𝑘 ); 2 S ← R( 𝐸 𝑐 , 𝑣 𝑛 ) ; // Sort all candidate entities by rerank scores. 3 Sort( 𝐸 𝑐 , S ); 4 𝑠𝑐𝑜𝑟𝑒 ← S[ 0 ] , 𝑆𝑒𝑙 ← 𝐸 𝑐 [ 0 ] ; // Gradient select similar entities. 5 for each remain entity 𝑣 𝑐 ∈ 𝐸 𝑐 \ { 𝐸 𝑐 [ 0 ] } do 6 if S[ 𝑣 𝑐 ] > 𝑠𝑐𝑜𝑟𝑒 / 𝑔 then 7 𝑆𝑒𝑙 ← 𝑆𝑒𝑙 ∪ { 𝑣 𝑐 } , 𝑠𝑐𝑜𝑟𝑒 ← S[ 𝑣 𝑐 ] ; 8 else break; // Merge entity or add new entity. 9 if length( 𝑆𝑒𝑙 ) = length( 𝐸 𝑐 ) then 10 𝐺 ← AddNewEntity( 𝐺, 𝑣 𝑛 ), 𝐷𝐵 ← AddNew( 𝐷𝐵, 𝑣 𝑛 ); 11 else 12 if length( 𝑆𝑒𝑙 ) = 1 then 𝑣 𝑠𝑒𝑙 ← 𝑆𝑒𝑙 [ 0 ] ; 13 else 𝑣 𝑠𝑒𝑙 ← LLMSelect( 𝑆𝑒𝑙 ); 14 𝐺 ← MergeEntity( 𝐺, 𝑣 𝑛 , 𝑣 𝑠𝑒𝑙 ), 𝐷𝐵 ← Update( 𝐷𝐵, 𝑣 𝑠𝑒𝑙 , 𝑣 𝑛 ); 15 return 𝐺,𝐷𝐵 ;
```

Algorithm 1: Gradient-based entity resolution

4.3.1 KG Construction. We iterate each node 𝑛 𝑖 ∈ 𝑁 from the previously constructed tree 𝑇 . For each node 𝑛 𝑖 , we extract a subgraph 𝑔 𝑖 = ( 𝑉 𝑖 , 𝐸 𝑅𝑖 ) based on its content 𝑐 𝑖 and final node type 𝜏 ′ 𝑖 . This extraction is modality-dependent: if the node is text-only, an LLM is prompted to extract entities and relations, while for nodes containing visual elements (e.g., 𝜏 ′ 𝑖 = Image ), a Vision Language Model (VLM) is employed to extract visual knowledge. Crucially, for every entity 𝑣 ∈ 𝑉 𝑖 extracted, its origin tree node 𝑛 𝑖 is recorded, which is vital for constructing the final mapping 𝑀 .

Furthermore, to preserve structural semantics for specific logical types (e.g., Table , Formula ), our process first creates a distinct, typed entity (e.g., 𝑣 table representing the table itself). The other extracted entities from the specific node's content are linked to this primary vertex. For Table nodes specifically, row and column headers are also explicitly extracted as distinct entities and linked to 𝑣 table via a 'ContainedIn' relationship.

4.3.2 Gradient-based Entity Resolution. As shown in the literature [62, 66], a well-constructed KG is essential for document question answering. A common challenge in the extraction process is that the same conceptual entity is often fragmented into multiple distinct entities due to abbreviations, co-references, or its varied occurrences across different document sections. This necessitates a robust Entity Resolution (ER) process, which identifies and merges these fragmented entities to refine the raw KG.

However, conventional ER methods are computationally expensive. They are often designed for batch processing across multiple data sources (commonly referred to as dirty ER), aiming to ensure accurate entity resolution by finding all possible matching pairs [12]. This process typically requires finding the transitive closure of all detected matches. That is, to definitively merge multiple entities (e.g., A, B, and C) as the same concept, the system must ideally compare all possible pairs ('A-B', 'A-C', and 'B-C') to confirm their equivalence. This can lead to a quadratic ( 𝑂 ( 𝑛 2 ) )

number of pairwise comparisons, a process that becomes prohibitively slow and computationally expensive when relying on LLMs for high-accuracy judgments.

To address this, we employ a gradient-based ER method, operating on a single document (simplified as the clean ER), which performs ER incrementally as each new entity 𝑣 𝑛 is extracted. This transforms the quadratic batch problem into a simpler, repeated lookup task: determining where the single new entity 𝑣 𝑛 fits among the already-processed entities in the database. This incremental process yields two distinct, observable scoring patterns when 𝑣 𝑛 is reranked against its 𝑡𝑜𝑝 \_ 𝑘 most relevant candidates:

- Case A: New Entity. If 𝑣 𝑛 is a new conceptual entity, its relevance scores against all existing entities will be uniformly low, showing no significant gradient or discriminative pattern.
- Case B: Existing Entity. If 𝑣 𝑛 is an alias of an existing entity, its scores will show a high relevance to the true match (or a small set of equivalent aliases). Due to the reranker's inherent discriminative limitations, this initial high-relevance set might occasionally contain multiple similar entities. This high-relevance set is then typically followed by a sharp decline (a large 'gradient') before transitioning to a gradual slope of irrelevant entities.

Our Gradient-based ER algorithm is designed precisely to detect this sharp decline (characteristic of Case B), allowing us to efficiently isolate the high-relevance set. Subsequently, an LLM is utilized for finer-grained distinction when multiple similar entities are identified within this set, differentiating it from the 'no gradient' scenario (Case A) without quadratic comparisons.

Algorithm 1 shows the above entity resolution process. For a new entity 𝑣 𝑛 , we first retrieve its 𝑡𝑜𝑝 \_ 𝑘 candidates 𝐸 𝑐 from the vector database 𝐷𝐵 , which are then reranked by R against 𝑣 𝑛 and sorted based on their scores S (Lines 1-3). We initialize the selection set 𝑆𝑒𝑙 with the top-scoring candidate 𝐸 𝑐 [ 0 ] and set the initial score to S[ 0 ] (Line 4). We then iterate through the remaining sorted candidates (Lines 5-8). The core logic checks if the current score S[ 𝑣 𝑐 ] is still within the gradient threshold 𝑔 of the previous score (i.e., S[ 𝑣 𝑐 ] &gt; score / 𝑔 ). If the score drop is gentle (passes the check), the candidate 𝑣 𝑐 is added to 𝑆𝑒𝑙 , and score is updated (Lines 7-8); otherwise, the loop breaks (Line 8) as soon as a sharp score drop is detected. Finally, the algorithm makes its decision (Lines 9-14). If the selection set 𝑆𝑒𝑙 is identical to 𝐸 𝑐 , this indicates that all candidates passed the gradient check. This corresponds to Case A , where the scores lacked discriminative power (i.e., 𝑣 𝑛 is equally dissimilar to all candidates), so 𝑣 𝑛 is added as a new entity (Line 9-10). Conversely, if a gradient was found (i.e., 𝑙𝑒𝑛𝑔𝑡ℎ ( 𝑆𝑒𝑙 ) &lt; 𝑙𝑒𝑛𝑔𝑡ℎ ( 𝐸 𝑐 ) ), this signals Case B . We then select the canonical entity 𝑣 𝑠𝑒𝑙 from 𝑆𝑒𝑙 , using an LLM (Line 13) if the reranker identifies multiple aliases, and merge 𝑣 𝑛 with it (Lines 12-14). The updated 𝐺 and 𝐷𝐵 are then returned (Line 15).

For instance, considering the example in Figure 2, when the new entity 𝑒 9 is processed, it is first compared with existing entities in the KG. As depicted in the similarity curve (orange line), 𝑒 9 shows high similarity with 𝑒 7, followed by a sharp decline in similarity with other entities like 𝑒 6, 𝑒 8, and 𝑒 5. Our gradient-based selection process identifies 𝑒 7 as the unique, high-confidence match for 𝑒 9. Consequently, 𝑒 9 is merged with 𝑒 7, enriching the KG with consolidated information as shown in the final merged entity 𝑒 ′ 7 .

Graph-Tree Link (GT-Link). The GT-Link 𝑀 is formalized to complete the BookIndex 𝐵 = ( 𝑇,𝐺, 𝑀 ) . As described in the KG Construction phase, the origin tree node 𝑛 𝑖 is recorded for every newly extracted entity 𝑣 𝑖 . GT-Link is then refined during entity resolution: when an entity 𝑣 𝑛 is merged into a canonical entity 𝑣 𝑠𝑒𝑙 , the origin node set of 𝑣 𝑠𝑒𝑙 is updated to include all origin nodes previously associated with 𝑣 𝑛 . This aggregation process creates the final mapping 𝑀 : 𝑉 → P( 𝑁 ) , which bi-directionally links the entities in 𝐺 to the set of their structural locations (nodes) in 𝑇 .

## 5 Agent-based Retrieval

Real-world document queries are often complex, necessitating operations like modal type filtering, semantic selection, and multi-hop reasoning. To address this, we propose an agent-based approach in BookRAG, which intelligently plans and executes operations on the BookIndex. We first introduce the overall workflow and present two core mechanisms: Agent-based Planning , which formulates the strategy, and the Structured Execution , which includes the retrieval process under the principles of IFT and generation.

## 5.1 Overall Workflow

The overall workflow of agent-based retrieval, illustrated in Figure 3, follows a three-stage pipeline designed to address users' queries systematically.

1. Agent-based Planning. BookRAG first performs Classification &amp; Plan . This stage aims to distinguish simple keyword-based queries from reasoning questions that require decomposition and analysis. For instance, a query like 'How does Transformer differ from RNNs in handling long-range dependencies?' cannot be solved by retrieving from a single keyword. Therefore, the planning stage first performs query classification . Based on this classification and a predefined set of operators designed for the BookIndex, it generates a specific operators plan that effectively guides the retrieval and generation strategies.
2. Retrieval Process. Guided by the operator plan, the retrieval process executes Scent/Filter-based Retrieval . This stage navigates the BookIndex 𝐵 = ( 𝑇,𝐺, 𝑀 ) , either utilizing a scent-based retrieval principle (e.g., following relevant entities in 𝐺 ) to find information, or employing various filters (e.g., modal type) to refine the selection. After reasoning, BookRAG gets the retrieval set of highly relevant information blocks from the BookIndex.
3. Generation Process. Finally, all retrieved information enters the generation stage for Analysis &amp; Merging . This stage synthesizes these (often fragmented) pieces of evidence, performs final analysis, and formulates a coherent response.

Figure 3: The general workflow of agent-based retrieval in BookRAG, which contains agent-based planning, retrieval, and generation processes.

<!-- image -->

## 5.2 Agent-based Planning

The planning stage is the core of BookRAG, designed to intelligently navigate our BookIndex 𝐵 = ( 𝑇,𝐺, 𝑀 ) . To support flexible retrieval, we define four types of operators: Formulator, Selector, Reasoner, and Synthesizer. These operators can be arbitrarily combined to form tailored execution pipelines, each with adjustable parameters. BookRAG dynamically configures and assembles these operators to adapt to the specific requirements of different query categories. This process involves two sequential steps: first, the agent performs Query Classification to determine the appropriate solution strategy, then generates a specific Operator Plan .

- Query Classification . To enable agent strategy selection, we focus on three representative query categories defined by their intrinsic complexity and operational demands (Table 2): Single-hop , Multi-hop , and Global Aggregation . This classification is crucial because each category requires a different solution strategy. For instance, a Single-hop query typically requires a single piece of information retrieved via a Scent-based Retrieval operation. In contrast, a Global Aggregation query often necessitates analyzing content under multiple filtering conditions, usually involving a sequence

Table 2: Three common query categories addressed in BookRAG.

| Query Category     | Description                                                                                                 | Core Task                                                                                                     | Example Query                                                              |
|--------------------|-------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| Single-hop         | Queries with a single, distinct information target.                                                         | Scent-based Retrieval : Retrieve content related to a specific entity or section.                             | What is the definition of Information Scent?                               |
| Multi-hop          | Queries that require synthesizing information from multiple blocks, often by decomposing into sub-problems. | Decomposing & Merging : Decompose into sub-problems, retrieve for each, and synthesize the final answer.      | How does Transformer differ from RNNs in handling long-range dependencies? |
| Global Aggregation | Queries that require filtering across the entire document and performing calculations.                      | Filter & Aggregation : Apply filters across the document & perform aggregation operations (e.g., Count, Sum). | How many figures related to IFT are in Section 4?                          |

Figure 4: The BookRAG Operator Library and an Execution Example from MMLongBench dataset: (a) a visual depiction of the four operator types (Formulator, Selector, Reasoner, and Synthesizer) and (b) an execution trace for a 'Single-hop' query, demonstrating the agent-based planning and step-by-step operator execution.

<!-- image -->

of Filter &amp; Aggregation operations across various parts of the document. Furthermore, BookRAG is designed to be extensible, allowing for the resolution of a broader range of query types by integrating additional operators.

- BookIndex Operators . To execute the strategies identified by classification, we designed a set of operators ( O ) tailored for the BookIndex 𝐵 = ( 𝑇,𝐺, 𝑀 ) . These operators, visually depicted in Figure 4(a) and detailed in Table 3, define the set of operations the agent can employ for diverse query categories. We group them into four types, which we describe in sequence:
- ❶ Formulator. These are LLM-based operators that prepare the query for execution. This category includes Decompose , which breaks a Complex query into a set of simpler, actionable sub-queries 𝑄 𝑠 . It also includes Extract , which employs an LLM to identify key entities 𝐸 𝑞 from the query text and link them to corresponding entities in the KG, 𝐺 :

<!-- formula-not-decoded -->

<!-- formula-not-decoded -->

Here, 𝑞 is the original user query, while 𝑃 𝐷𝑒𝑐 and 𝑃 𝐸𝑥𝑡 represent the prompts used to guide the LLM for the decomposition and extraction tasks, respectively.

- ❷ Selector. These operators filter or select specific content ranges from the BookIndex. Filter\_Modal and Filter\_Range directly apply the explicit constraints 𝐶 (e.g., modal types, page ranges) generated during the plan. Operating on the Tree 𝑇 = ( 𝑁, 𝐸 𝑇 ) , these operators produce a filtered subset 𝑁 𝑓 where the predicate 𝐶 ( 𝑛 ) holds true for each node:

<!-- formula-not-decoded -->

In contrast, Select\_by\_Entity and Select\_by\_Section target contiguous document segments by retrieving subtrees rooted at specific section nodes. This process first identifies a set of target section nodes 𝑆 target ⊂ 𝑁 at a specified depth, where 𝑆 target consists of sections either linked to entities 𝐸 𝑞 via the GT-Link 𝑀 or selected by the LLM. It then retrieves all descendants of these targets to form the selected node set 𝑁 𝑠 :

<!-- formula-not-decoded -->

- ❸ Reasoner. These operators analyze and refine selected tree nodes. Graph\_Reasoning performs multi-hop inference on a subgraph 𝐺 ′ ( 𝑉 ′ , 𝐸 ′ ) (extracted from selected nodes 𝑁 𝑠 ) starting from entity 𝑒 . Starting from the retrieved entities, it computes an entity importance vector 𝐼 𝐺 ∈ R | 𝑉 ′ | over the subgraph 𝐺 ′ using the PageRank algorithm [20]. These entity scores are then mapped to the tree nodes via the GT-Link matrix 𝑀 to derive the final tree node importance scores vector 𝑆 𝐺 ∈ R | 𝑁 𝑠 | :

<!-- formula-not-decoded -->

<!-- formula-not-decoded -->

Text\_Ranker evaluates the semantic relevance of the tree node's content to the query 𝑞 , assigning a relevance score 𝑆 𝑇 to each node. Skyline\_Ranker employs the Skyline operator to filter nodes based on these multiple criteria (e.g., 𝑆 𝐺 and 𝑆 𝑇 ), retaining only those nodes that are not dominated by any others in terms of the specified scoring dimensions.

- ❹ Synthesizer. These operators are responsible for content generation. Map performs analysis on specific retrieved information segments to generate partial responses. Reduce synthesizes a final

coherent answer by aggregating information from multiple sources, such as partial answers or a collection of retrieved evidence.

- Operator Plan . After classifying the query ( 𝑞 ) into its category ( 𝑐 ), the agent's final task is to generate an executable plan 𝑃 . This plan is a specific sequence of operators ⟨ 𝑜 1 , . . . , 𝑜 𝑛 ⟩ selected from our library O with parameters dynamically instantiated based on 𝑞 . This process is formulated as:

<!-- formula-not-decoded -->

The plan follows a structured workflow tailored to each category:

- Single-hop : The agent first attempts to Extract an entity. If successful, it executes a 'scent-based' selection; otherwise, it falls back to a section-based strategy. Both paths then proceed to standard reasoning and generation, denoted as 𝑃 std .

<!-- formula-not-decoded -->

<!-- formula-not-decoded -->

- Complex : The agent first decomposes the problem, applies the Single-hop workflow 𝑃 s to each sub-problem, and finally synthesizes the results.

<!-- formula-not-decoded -->

- Global Aggregation : The workflow involves applying a sequence of filters followed by synthesis.

<!-- formula-not-decoded -->

Here, the symbol ˛ denotes the nested composition of filters, applying either a modal or range filter at each step.

## 5.3 Structured Execution

Following the planning stage, BookRAG executes the generated workflow 𝑃 . This execution phase embodies the cognitive principles of Information Foraging Theory (IFT), effectively translating abstract textual queries into concrete operations. Specifically, the Selector operators mirror the act of 'navigating to information patches,' narrowing the vast document space down to relevant scopes. Subsequently, the Reasoner operators perform 'sensemaking within patches,' where they analyze and refine the information within these focused scopes. Finally, the Synthesizer generates the answer based on the processed evidence. This design minimizes the cost of attention by ensuring computational resources are focused solely on high-value data patches.

Scent/Filter-based Retrieval. The execution begins by narrowing the scope. Aligning with IFT, Selector operators identify relevant 'patches' by following 'information scents' (e.g., key entities in question) or applying explicit filter constraints. This process reduces the full node set 𝑁 to a focused node subset 𝑁 𝑠 :

<!-- formula-not-decoded -->

This pre-selection minimizes noise and ensures that subsequent reasoning is applied only to highly relevant contexts, optimizing the foraging cost. Subsequently, within this focused scope, Reasoner operators evaluate nodes using multiple dimensions, such as graph topology and semantic relevance. We then employ the Skyline\_Ranker to get the final retrieval set. Unlike fixed top𝑘 retrieval, the Skyline operator retains the Pareto frontier of nodes, retaining nodes that are valuable in at least one dimension while discarding dominated ones:

<!-- formula-not-decoded -->

Analysis &amp; Merging Generation. In the final stage, the Synthesizer operator generates the coherent answer by aggregating the refined evidence:

<!-- formula-not-decoded -->

The Map operator performs fine-grained analysis on individual evidence blocks or sub-problems (from Decompose ) to generate intermediate insights. The Reduce operator then aggregates these partial results, such as answers to decomposed sub-queries or statistical counts from a global filter, to construct the final response.

Table 3: Operators utilized in our BookRAG, categorized by their function.

| Operator                                                     | Type                                | Description                                                                                                                                                                                                                                                                                      | Parameters                                                                           |
|--------------------------------------------------------------|-------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Decompose Extract                                            | Formulator Formulator               | Decompose a complex query into simpler, actionable sub-queries. Identify and extract key entities from the query (links to 𝐺 ).                                                                                                                                                                  | (Self-contained) (Self-contained)                                                    |
| Filter_Modal Filter_Range Select_by_Entity Select_by_Section | Selector Selector Selector Selector | Filter retrieved nodes by their modal type (e.g., Table, Figure). Filter nodes based on a specified range (e.g., pages, section). Selects all tree nodes ( 𝑁 ) in sections linked to a given entity ( 𝑉 ). Uses an LLM to select relevant sections and selects all tree nodes ( 𝑁 ) within them. | modal_type: str range: (start, end) entity_name: str query: str, sections: List[str] |
| Graph_Reasoning Text_Reasoning Skyline_Ranker                | Reasoner Reasoner Reasoner          | Performs multi-hop reasoning on subgraph ( 𝐺 ′ ) and score tree nodes ( 𝑁 ) using graph importance and GT-links. Rerank retrieved tree nodes ( 𝑁 ) based on the relevance. Rerank nodes based on multiple criteria.                                                                              | start_entity: str, subgraph: 𝐺 ′ query: str criteria: List[str]                      |
| Map Reduce                                                   | Synthesizer Synthesizer             | Uses partially retrieved information to generate a partial answer. Synthesizes the final answer from partial information or all sub-problem answers.                                                                                                                                             | (Input: List[str]) (Input: List[str])                                                |

This separation ensures that the system can handle both detailed content extraction and high-level reasoning synthesis effectively.

To illustrate this end-to-end process, Figure 4(b) presents an execution trace for a 'Single-hop' query: 'What is the type of car in the Ranking Prompt example?'. In the planning phase, the agent classifies the query and generates a specific workflow. Subsequently, it identifies key entities (e.g., 'car') via Extract , retrieves relevant nodes via Select\_by\_Entity , refines them through reasoning and Skyline filtering, and finally synthesizes the answer using Reduce .

## 6 Experiments

In our experiments, we evaluate BookRAG against several strong baseline methods, with an in-depth comparison of their efficiency and accuracy on document QA tasks.

## 6.1 Setup

Table 4: Datasets used in our experiments. EM and F1 denote Exact Match and F1-score, respectively.

| Dataset     | MMLongBench   | M3DocVQA   | Qasper       |
|-------------|---------------|------------|--------------|
| Questions   | 669           | 633        | 640          |
| Documents   | 85            | 500        | 192          |
| Avg. Pages  | 42.16         | 8.52       | 10.95        |
| Avg. Images | 25.92         | 3.51       | 3.43         |
| Tokens      | 2,816,155     | 3,553,774  | 2,265,349    |
| Metrics     | EM, F1        | EM, F1     | Accuracy, F1 |

Datasets &amp; Question Synthesis. We use three widely adopted benchmarking datasets for complex document QA tasks: MMLongBench [33], M3DocVQA [11], and Qasper [14]. MMLongBench is a comprehensive benchmark designed to evaluate QA capabilities on long-form documents, covering diverse categories such as guidebooks, financial reports, and industry files. M3DocVQA is an open-domain benchmark designed to test RAG systems on a diverse collection of HTML-type documents sourced from Wikipedia pages 1 . Qasper is a QA dataset focused on scientific papers, where questions require retrieving evidence from the entire document. We filtered the datasets to remove documents with low clarity or incoherent structures. To address the scarcity of global-level questions in the original benchmarks, we synthesize additional QA pairs by having an LLM generate global questions from selected document elements (e.g., tables or figures). These questions are then answered and meticulously refined by human annotators via an outsourcing process, with this additional QA pairs constituting less than 20% of our final QA pairs. The statistics of these datasets are presented in Table 4.

Metrics. Weadheretotheofficial metrics specified by each dataset for QA. Our primary evaluation relies on Exact Match (EM), accuracy, and token-based F1-score. To assess efficiency, we also measure time cost and token usage during the response phase. Additionally, for methods including PDF parsing, we also evaluate retrieval recall. To establish the ground truth for this, we manually label the specific PDF blocks (e.g., texts, titles, tables, images, and formulas) required to answer each question. This labeling process is guided by the metadata of ground-truth evidence provided in each dataset; we filter candidate blocks using the given modality (all datasets), page numbers (MMLongBench), and evidence statements (Qasper). Any blocks that remained non-unique after this filtering process are manually annotated. In cases where a PDF parsing error made the ground-truth item unavailable, the retrieval recall for that query is recorded as 0.

1 https://www.wikipedia.org/

Baselines. Our experiments consider three model configurations:

- Conventional RAG: These methods are the most common pipeline for document analysis, where the raw text is first extracted and then chunked into segments of a specified size. We select strong and widely used retrieval models: BM25 [44] and Vanilla RAG. We also implement Layout+Vanilla, a variant that uses document layout analysis for semantic chunking.
- Graph-based RAG: These methods first extract textual content from documents and then leverage graph data during retrieval. We select RAPTOR [45] and GraphRAG [16]. Specifically, GraphRAG has two versions: GraphRAG-Global and GraphRAG-Local, which employ global and local search methods, respectively.
- LayoutsegmentedRAG: This category encompasses methods that utilize layout analysis to segment document content into discrete structural units. We include: MM-Vanilla, which utilizes multi-modal embeddings for visual and textual content; a tree-based method inspired by PageIndex [39], denoted as TreeTraverse, where an LLM navigates the document's tree structure; DocETL [47], a declarative system for complex document processing; and GraphRanker, a graphbased method extended from HippoRAG [19] that applies Personalized PageRank [20] to rank the relevant nodes.

Implementation details. For a fair comparison, both BookRAG and all baseline methods are powered by a unified set of state-of-theart (SOTA) and widely adopted backbone models from the Qwen family [4, 60, 63, 64]. We employ MinerU [52] for robust document layout parsing. We set the threshold of gradient 𝑔 as 0 . 6, and more details are provided in the appendix of our technical report [57]. Our source code, prompts, and detailed configurations are available at github.com/sam234990/BookRAG.

## 6.2 Overall results

In this section, we present a comprehensive evaluation of BookRAG, analyzing its complex QA performance, retrieval effectiveness, and query efficiency compared to state-of-the-art baselines.

- QA Performance of BookRAG . We compare the QA performance of BookRAG against three categories of baselines, as shown in Table 5. The results indicate that BookRAG achieves state-of-the-art performance across all datasets, substantially outperforming the top-performing baseline by 18.0% in Exact Match on M3DocVQA. Layout + Vanilla consistently outperforms Vanilla RAG, confirming that layout parsing preserves essential structural information for better retrieval. Besides, the suboptimal results of Tree-Traverse and GraphRanker highlight the limitations of relying solely on hierarchical navigation or graph-based reasoning, which

Table 5: Performance comparison of different methods across various datasets for solving complex document QA tasks. The best and second-best results are marked in bold and underlined, respectively.

| Baseline Type        | Method           | MMLongBench   | MMLongBench   | M3DocVQA      | M3DocVQA   | Qasper     | Qasper     |
|----------------------|------------------|---------------|---------------|---------------|------------|------------|------------|
| Baseline Type        | Method           | (Exact Match) | (F1-score)    | (Exact Match) | (F1-score) | (Accuracy) | (F1-score) |
| Conventional RAG     | BM25             | 18.3          | 20.2          | 34.6          | 37.8       | 38.1       | 42.5       |
| Conventional RAG     | Vanilla RAG      | 16.5          | 18.0          | 36.5          | 40.2       | 40.6       | 44.4       |
| Conventional RAG     | Layout + Vanilla | 18.1          | 19.8          | 36.9          | 40.2       | 40.7       | 44.6       |
| Graph-based RAG      | RAPTOR           | 21.3          | 21.8          | 34.3          | 37.3       | 39.4       | 44.1       |
| Graph-based RAG      | GraphRAG-Local   | 7.7           | 8.5           | 23.7          | 25.6       | 35.9       | 39.2       |
| Graph-based RAG      | GraphRAG-Global  | 5.3           | 5.6           | 20.2          | 22.0       | 24.0       | 24.1       |
| Layout segmented RAG | MM-Vanilla       | 6.8           | 8.4           | 25.1          | 27.7       | 27.9       | 29.3       |
| Layout segmented RAG | Tree-Traverse    | 12.7          | 14.4          | 33.3          | 36.2       | 27.3       | 32.1       |
| Layout segmented RAG | GraphRanker      | 21.2          | 22.7          | 43.0          | 47.8       | 32.9       | 37.6       |
| Layout segmented RAG | DocETL           | 27.5          | 28.6          | 40.9          | 43.3       | 42.3       | 50.4       |
| Our proposed         | BookRAG          | 43.8          | 44.9          | 61.0          | 66.2       | 55.2       | 61.1       |

often miss cross-sectional context or drift into irrelevant scopes. In contrast, BookRAG's superiority stems from the synergy of its unified Tree-Graph BookIndex and Agent-based Planning. By effectively classifying queries and configuring optimal workflows, our BookRAG overcomes limitations of context fragmentation and static query workflow within existing baselines, ensuring precise evidence retrieval and accurate generation.

Table 6: Retrieval recall comparison among layout-based methods. The best and second-best results are marked in bold and underlined, respectively.

| Method           |   MMLongBench |   M3DocVQA |   Qasper |
|------------------|---------------|------------|----------|
| Layout + Vanilla |          26.3 |       33.8 |     33.5 |
| MM-Vanilla       |           7.5 |       19.7 |     14.9 |
| Tree-Traverse    |          11.2 |       19.5 |     14.5 |
| GraphRanker      |          26.4 |       44.5 |     28.6 |
| BookRAG          |          57.6 |       71.2 |     63.5 |

- Retrieval performance of BookRAG. To validate our retrieval design, we evaluate the retrieval recall of BookRAG against other layout-based baselines on the ground-truth layout blocks. The experimental results demonstrate that BookRAG achieves the highest recall across all datasets, notably reaching 71.2% on M3DocVQA and significantly outperforming the next best baseline (GraphRanker, max44.5%). This performance advantage stems from our IFT-inspired Selector → Reasoner workflow: the Agent-based Planning first classifies the query, enabling the Selector to narrow the search to a precise information patch , followed by the Reasoner's analysis. Crucially, after the Skyline\_Ranker process, the average number of retained nodes is 9.87, 6.86, and 8.6 across the three datasets, which is comparable to the standard top𝑘 ( 𝑘 = 10) setting, ensuring high-quality retrieval without inflating the candidate size.
- Efficiency of BookRAG. Wefurther evaluate the efficiency in terms of query time and token consumption, as illustrated in Figure 5. Overall, BookRAG maintains time and token costs comparable to existing Graph-based RAG methods. While purely text-based

Figure 5: Comparison of query efficiency.

<!-- image -->

RAG approaches generally exhibit lower latency and token usage due to the absence of VLM processing for images, BookRAG maintains a balanced efficiency among multi-modal methods. In terms of token usage, BookRAG reduces consumption by an order of magnitude compared to the strongest baseline, DocETL. Notably, on the MMLongBench dataset, DocETL consumes over 53 million tokens, whereas BookRAG requires less than 5 million. Regarding the query latency, our method also achieves a speedup of up to 2 × compared to DocETL.

## 6.3 Detailed Analysis

In this section, we provide a more in-depth examination of our BookRAG. We first conduct an ablation study to validate the contribution of each component, followed by an experiment on the impact of gradient-based ER and QA performance across different query types. Furthermore, we perform a comprehensive error analysis, compare the effectiveness of our entity resolution method, and present a case study.

- Ablation study. To evaluate the contribution of each core component in BookRAG, we design several variants by removing specific components:
- w/o Gradient ER: Replaces the gradient-based entity resolution with a Basic ER by merging the same-name entities.
- w/o Planning: Removes the Agent-based Planning, defaulting to a static, standard workflow for all queries.
- w/o Selector : Removes the Selector operators, forcing Reasoners to score all candidate nodes.
- w/o Graph\_Reasoning : Removes the Graph\_Reasoning operator. Consequently, the Skyline\_Ranker is also disabled as scoring becomes single-dimensional.
- w/o Text\_Reasoning : Removes the Text\_Reasoning operator. Similarly, the Skyline\_Ranker is disabled, relying solely on graph-based scores.

Table 7: Comparing the QA performance of different variants of BookRAG. EM and F1 denote Exact Match and F1-score, respectively.

| Method variants     | MMLongBench   | MMLongBench   | Qasper   | Qasper   |
|---------------------|---------------|---------------|----------|----------|
|                     | EM            | F1            | Accuracy | F1       |
| BookRAG (Full)      | 43.8          | 44.9          | 55.2     | 61.1     |
| w/o gradient ER     | 40.1          | 42.8          | 48.9     | 57.3     |
| w/o Planning        | 30.8          | 33.2          | 40.9     | 48.5     |
| w/o Selector        | 42.5          | 43.1          | 52.5     | 59.1     |
| w/o Graph_Reasoning | 39.8          | 41.5          | 51.4     | 58.4     |
| w/o Text_Reasoning  | 39.0          | 40.3          | 47.2     | 52.5     |

The first variant evaluates the impact of KG quality on retrieval performance. The second and third variants assess the necessity of our Agent-based Planning and IFT-inspired selection mechanism, respectively. Finally, the last two variants validate the effectiveness of our multi-dimensional reasoning and dynamic Skyline filtering strategy. As shown in Table 7, the performance degradation across all variants confirms the essential role of each module in BookRAG. Specifically, the performance drop in the w/o Gradient ER variant highlights the critical role of a high-quality, connectivity-rich KG in supporting effective reasoning. Removing the Planning mechanism results in the most significant performance loss, confirming that a static workflow is insufficient for handling diverse types of queries. The w/o Selector variant, while maintaining competitive accuracy, incurs a prohibitive computational cost ( &gt; 2 × tokens on Qasper), validating the efficiency of our IFT-inspired "narrow-then-reason" strategy.

- Impact of Gradient-based Entity Resolution. To evaluate the quality of our constructed KG, we compare the graph statistics

Figure 6: Comparison of graph statistics. Values are normalized to the Basic setting (Baseline=1.0). Absolute values for Basic are annotated. Note that density values are abbreviated (e.g., 3.6E-3 denotes 3 . 6 × 10 -3 ).

<!-- image -->

of our Gradient-based ER against a Basic KG construction. The Basic setting employs simple exact name matching for entity merging, which is standard practice in many graph-based methods. Figure 6 presents the comparative results, normalizing the metrics (Entity count, Density, Diameter of the Largest Connected Component, and Number of Connected Components) against the Basic baseline. The results demonstrate that our Gradient-based ER significantly optimizes KG. Specifically, it reduces the number of entities (by 12%) while substantially boosting graph density (by over 20% across datasets). This structural shift indicates that our ER module effectively identifies the same conceptual entities that possess different names. Consequently, the resulting graphs are more compact and cohesive, as evidenced by the reduced diameter and fewer connected components, which mitigates graph fragmentation and facilitates better connectivity for graph reasoning.

Figure 7: QA performance breakdown by different query types (Single-hop, Multi-hop, and Global). The blue bars represent Exact Match (EM) for MMLongBench and Accuracy for Qasper, while the red bars represent the F1-score.

<!-- image -->

- QA performance under different query types. Figure 7 breaks down the performance of BookRAG across Single-hop, Multihop, and Global aggregation query types. We observe that Multihop queries generally present a greater challenge compared to Single-hop ones, resulting in a slight performance decrease. This trend reflects the inherent difficulty of retrieving and reasoning over disjoint pieces of evidence. It further validates our agent-based planning strategy, which handles different query types separately.
- Error Response analysis. To diagnose the performance bottlenecks of BookRAG, we conduct a fine-grained error analysis on 200 sampled queries from each dataset, tracing the error propagation as shown in Figure 9. We categorize failures into four types: PDF Parsing, Plan, Retrieval, and Generation errors. The results

## BookRAG response of different query types

Single-hop Case from Qasper Question: What is the reward model for the reinforcement learning approach? Human-written answer: Reward 1 for successfully completing the task, with a discount by the number of turns, and reward 0 when fail. Evidence: We defined the reward as being 1 for successfully completing the task, and 0 otherwise. A discount of 0 . 95 &lt;/&gt; Agent-based Planning: This is a single-hop query. Here is the Select operator: Extract={"entity\_name": "reinforcement learning (rl)", "entity\_type":"METHOD\_OR\_TECHNIQUE"} Process: The Select\_by\_Entity operator identifies relevant sub-trees (e.g., 'Introduction', 'Related work'), pruning the reasoning space from 134 to 24 nodes. Subsequent Graph\_Reasoning , Text\_Reasoning , and Skyline\_Ranker operate on this focused scope to retrieve 8 nodes for the final response. Output : The reward model for the reinforcement learning approach is based on a binary reward system that evaluates the success or failure of dialog interactions. &lt;/&gt; 1 for successfully completing a task. &lt;/&gt; 0 for failing &lt;/&gt; using a discount factor of 0.95 &lt;/&gt; Multi-hop Case from Qasper Question: What is the difference in performance between the interpretable system (e.g., vectors and cosine distance) and LSTM with ELMo system? Human-written answer: Accuracy of best interpretible system was 0.3945 while accuracy of LSTM-ELMo net was 0.6818. Evidence 1: The experimental results are presented in Table 1. Diacritic swapping showed a remarkably poor performance &lt;/&gt; Evidence 2: Test results for all the methods used. The loss measure is cross-entropy &lt;/&gt; Agent-based Planning: This is a multi-hop query. Here is the Decompose operator: Sub\_question 1: "What is the performance metric of the interpretable system (e.g., vectors and cosine distance)?" Sub\_question 2: "What is the performance metric of the LSTM with ELMo system?" Process: BookRAG applies the single-hop workflow for each sub-question and generates the partial answers as follows: Answer 1: "Summary:\nPerformance Metric: Accuracy (0.3945) and &lt;/&gt;" Answer 2: "The performance metric of the LSTM with ELMo system (LSTM-ELMo net) is as follows:\n Accuracy: 0.6818 &lt;/&gt;" Output : The interpretable system (using vector distance and cosine distance) has an accuracy of 0.3945 , while the LSTM with ELMo system has an accuracy of 0.6818 . The difference in accuracy between the two systems is 0.6818 - 0.3945 = 0.2873. &lt;/&gt; Global Aggregation Case from MMLongBench Question: How many charts are shown in the first 10 pages of the document? Human-written answer: 5 Agent-based Planning: This is a global query. Here are filter operators: 1. Filter\_Range={"filter\_type": page, "filter\_range":"1-10"} 2. Filter\_Modal={"filter\_type": image} Map Reduce synthesizes the final output.

Process: Applying filter operators retrieves images nodes from pages [ 3 , 5 , 6 , 8 , 9 ] . analyzes each image, and Output : Based on my analysis of the document, I found 5 items that answer the question. &lt;/&gt;

Figure 8: Case study of responses across different query types from MMLongBench and Qasper. CYAN TEXT highlights correct content generated by BookRAG. GRAY TEXT describes the internal process, and &lt;/&gt; marks omitted irrelevant parts.

identify Retrieval Error as the dominant failure mode, followed by Generation Error, reflecting the persistent challenge of locating and synthesizing multimodal evidence. Regarding Plan Error, our qualitative analysis reveals a specific failure pattern: the planner tends to over-decompose detailed single-hop queries into unnecessary multi-hop sub-tasks. This fragmentation leads to disjointed retrieval paths, effectively preventing the model from synthesizing a cohesive final answer from the scattered sub-responses.

- Case study. Figure 8 illustrates BookRAG's answering workflow across Single-hop, Multi-hop, and Global queries. The results demonstrate that by leveraging specific operators ( Select , Decompose , and Filter ), BookRAG effectively prunes search spaces. For example, in the Single-hop case, the reasoning space is significantly reduced from 134 to 24 nodes. This capability allows the system to efficiently isolate relevant evidence from noise, ensuring precise answer generation.

Figure 9: Error analysis on 200 sampled queries from MMLongBench and Qasper datasets.

<!-- image -->

## 7 Conclusion

In this paper, we propose BookRAG, a novel method built upon Book Index, a document-native, structured Tree-Graph index specifically designed to capture the intricate relations of structural documents. By employing an agent-based method to dynamically configure