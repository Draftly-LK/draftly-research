# Case Law → Retrieval Engine Roadmap

Tracks the path from LKCA + LKSC parsed case law (7,439 + 2,162 cases) to
those cases being searchable through the retrieval engine. Mark each step
`[x]` when done, and add a one-line note underneath with the date and any
result worth remembering.

## Steps

- [ ] **1. Fix + run the conveyancing filter (LKCA and LKSC)**
  Narrows 7,439 + 2,162 cases down to just the ones actually about
  conveyancing/land law. `scripts/classify_commonlii_conveyancing.py` exists
  but its `SOURCE` path is stale after the multi-database reorg — fix before
  running.

- [ ] **2. Decide + build the "rule" for each in-scope case**
  Clean rule text already exists (`extract_headnote()`'s `holdings` field).
  Still needed: link each case's statute mention to your official
  statute-ID list (`SRCxxx-sN`), not just the raw regex-extracted name.

- [ ] **3. Link cases to statute sections**
  A table saying "this case's rule ↔ this exact statute section," so a
  search for a section can surface the cases about it.

- [ ] **4. Decide how case law joins the existing statute retrieval engine**
  ⚠️ Slow down here. The engine currently *deliberately excludes* case law —
  a guarded rule in `corpus.py` (`ALLOWED_KINDS`, two runtime checks, a
  schema `CHECK`, and the answering prompt all move together per CLAUDE.md).
  Not a quick config flag.

- [ ] **5. Add the case documents to the searchable corpus**
  Same place statutes live (`documents.csv`), following the same pattern.

- [ ] **6. Build the search index over the new documents**
  The lexical (keyword/BM25) index picks up the new case text automatically
  once step 5 is done.

- [ ] **7. Add embeddings for the new case documents**
  What lets "meaning-based" search work, not just exact keyword matches.

- [ ] **8. Add case-law connections to the graph layer**
  Case→statute links (from step 3) and case→case citations, so the
  graph-based ranking channel knows about them too.

- [ ] **9. Add test questions that need case law to answer**
  So the engine can be checked on whether it actually finds and uses cases
  correctly, not just statutes.

- [ ] **10. Rebuild the index and test it**
  Run the engine's build step, then ask real questions and confirm answers
  cite the right cases.
