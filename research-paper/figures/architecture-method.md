# Benchmark Construction and Complete-Bundle Statutory Retrieval

Two-panel figure for a legal information retrieval paper on Sri Lankan statutes.

## Panel A: Benchmark construction (left-to-right pipeline)

Funnel stages, drawn as a horizontal pipeline of boxes joined by thin arrows:

1. 667 atomic examination questions (split from Sri Lanka Law College conveyancing papers)
2. 210 keep or enrich candidates
3. 144 clean and confident questions (Tier A)
4. Statute-only authority filtering
5. Independent research agent (searches the frozen statutory corpus, records every provision with a verbatim excerpt)
6. Independent verification agent (has not seen the research; re-reads every cited section; marks verified / partially verified / rejected / unresolved)
7. 50 proposed-gold questions in 40 legal matters
8. Lawyer validation: PENDING (0 approvals). Draw this as a dashed, unfilled box to show it has not happened.

Under stages 5 to 7 (the annotation stages), show a row of the gold fields each question carries:
legal issue; governing Act; indispensable sections; supporting sections; legal-hop count; temporal applicability; claim-level provenance.

Four data states must be visually distinct, with a small legend:

- original facts (plain, from the exam paper)
- labelled enriched facts (synthetic facts added by the researcher, explicitly labelled as such)
- proposed gold (agent-produced, agent-verified, solid outline)
- lawyer-approved gold (dashed outline, empty, marked "pending"; none exists yet)

Do not imply that lawyer validation is complete. The final box must read "proposed gold, pending lawyer validation".

## Panel B: Complete-bundle retrieval (left-to-right pipeline)

Input: scenario background plus legal question (one query box).

Steps, each a box joined by thin arrows:

1. Act-level router (scores Acts by summing the top fused section scores inside each Act)
2. Candidate Acts (a small set of Act nodes)
3. Hybrid section retrieval: BM25F (field-weighted lexical) and dense retrieval (bge-base), fused by reciprocal rank fusion
4. Seed sections
5. Typed-edge expansion over the statute graph
6. Temporal filtering (drop sections not in force at the matter's reference date)
7. Reranking (cross-encoder score averaged with fused score plus graph support)
8. Top-k statutory sections

Statutory corpus: draw it as a small graph beneath steps 2 to 5. Act nodes (larger, dark blue) contain section nodes (smaller circles). Sections are connected by typed directed edges. Show the six edge types with a legend, using distinct thin line styles (solid, dashed, dotted, dash-dot) and small uppercase labels:
DEFINES, EXCEPTS, QUALIFIES, PROCEDURALLY_REQUIRES, CROSS_REFERENCES, AMENDS.
AMENDS edges run from a section of an amending Act to a section of a principal Act.

Evaluation (far right of Panel B): compare the retrieved top-k sections against the complete set of indispensable gold sections from Panel A. Show two mini-examples side by side:

- all indispensable sections retrieved: check mark, "complete"
- one indispensable section missing: cross mark, "incomplete"
Caption text inside the panel: "A question succeeds only when every indispensable section is retrieved (complete-indispensable recall)." Partial credit is not given.

## Style

Clean NeurIPS-style vector diagram. White background. Restrained palette: dark blue (#1F3A5F) for primary boxes and Act nodes, muted gold (#B8963E) only for highlights (indispensable sections, the success check). Thin 1 px lines, rounded rectangles, sans-serif typography at one consistent size, panel labels "A" and "B" in bold at top-left of each panel. Readable at single-column (8.5 cm) or double-column (17 cm) width. No gradients, no shadows, no decorative legal icons, no courthouse or gavel imagery, no 3D effects, no clip art.
