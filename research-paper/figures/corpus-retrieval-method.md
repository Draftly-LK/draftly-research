# Structured Statutory Corpus and Complete-Bundle Retrieval Benchmark

One landscape figure with two clearly separated panels arranged left to right, each with a subtle dashed border and a bold circled panel letter at the upper-left corner, followed by the panel title in bold text:

- "A. Structured Statutory Corpus"
- "B. Complete-Bundle Retrieval Benchmark"

Clean NeurIPS/ACL research-paper style. Must remain readable when printed at approximately 14 cm width.

## Panel A: Structured Statutory Corpus

At the left, a small stack of source statute documents labelled "Sri Lankan Statutes", with the short subtitle "Principal and amending enactments" under it.

An arrow connects the source documents to a large central dark-navy corpus card labelled "Canonical Statutory Corpus". Inside this card, four lines: "52 principal enactments", "60 amending Acts", "4,557 sections", "17,854 provisions".

From the canonical corpus, two branches.

First branch: a card labelled "Section Index". Under it, three small field chips: "Act title", "Section heading", "Section text".

Second branch: a card labelled "Typed Statutory Graph". Show several small circular section nodes connected with directional arrows. Node labels: "§2", "§5", "§9", "§14". Below the graph, a compact edge legend containing exactly these six relationship types: "DEFINES", "EXCEPTS", "QUALIFIES", "PROCEDURALLY_REQUIRES", "CROSS_REFERENCES", "AMENDS". Solid navy arrows for general statutory relationships; muted-gold arrows for amendment relationships. Add the small note: "Heuristically typed and deterministically validated".

## Panel B: Complete-Bundle Retrieval Benchmark

At the top-left of Panel B, a document-shaped query card labelled "Scenario Question" with two short lines inside: "Factual background", "Legal question".

The Scenario Question feeds BOTH retrieval tracks with explicit arrows: one arrow into the "Retrieval Baselines" card and one arrow into the FIRST stage of the proposed method, "Initial Hybrid Retrieval".

Upper track, baselines: one grouped pale-blue card labelled "Retrieval Baselines" listing exactly: "BM25", "Field-weighted BM25", "Dense retrieval", "Hybrid RRF", "Hybrid + cross-encoder".

Lower track, proposed method: a visually emphasized dark-navy pipeline labelled "Structure-Aware Retriever" with exactly seven connected stages in this order:

"Initial Hybrid Retrieval" -> "Act-Score Aggregation" -> "Candidate Acts" -> "Scoped Section Retrieval" -> "Typed-Edge Expansion" -> "Temporal Filtering" -> "Reranking"

Small subtitle below "Temporal Filtering": "Reference-date constraints".

Corpus connections (draw exactly these, no others):

- "Section Index" (Panel A) -> "Retrieval Baselines" card.
- "Section Index" (Panel A) -> "Initial Hybrid Retrieval" stage.
- "Typed Statutory Graph" (Panel A) -> "Typed-Edge Expansion" stage.

Do NOT draw any line from the graph into hybrid retrieval, and do not draw the Section Index into any stage other than "Initial Hybrid Retrieval".

Both tracks lead to a common output card labelled "Top-k Statutory Sections", drawn as a ranked stack of section cards: "1  Act A §5", "2  Act B §9", "3  Act A §14".

Evaluation area, bottom-right: a gold-coloured reference card titled "Proposed Gold Indispensable Bundle" with the small line "Lawyer validation pending" under the title, and three gold section chips: "Act A §5", "Act B §9", "Act A §14". Both the retrieved top-k sections and the gold bundle connect to a final evaluation card labelled "Retrieval Evaluation" listing exactly: "Indispensable Recall@5/10/20", "MRR", "nDCG@10", "Act Identification Accuracy", "Complete-Bundle Recall@k". Emphasize "Complete-Bundle Recall@k" with a muted-gold border or banner. Beside it, a very small two-row illustration: first row, all three required sections retrieved, a gold check mark, label "Complete = 1"; second row, one required section missing, a grey cross, label "Complete = 0". Below the evaluation card: "A question succeeds only when every indispensable section appears in the top-k results."

## Visual style

White background; dark navy #1F3A5F; muted gold #B8963E; pale blue #EAF0F7; pale gold #FFF8E7; light grey #F4F5F7; charcoal text #263238; thin 1 to 1.5 px lines; rounded rectangular cards; consistent spacing; one professional sans-serif typeface; clear visual hierarchy; flat vector graphics. Dark navy for the corpus and the proposed retrieval method. Pale blue for inputs and baseline components. Muted gold only for gold labels, amendment edges, highlighted metrics and important evaluation elements.

Do not use gradients, drop shadows, 3D elements, photographs, robots, human faces, gavels, scales of justice, courthouse icons, case-law databases, answer-generation components, lawyer-validation components, benchmark-construction agents, or invented performance results.

Every label must be spelled exactly as specified. Do not abbreviate, paraphrase, duplicate or omit any pipeline stage. Do not invent evaluation scores. Keep the layout uncluttered.
