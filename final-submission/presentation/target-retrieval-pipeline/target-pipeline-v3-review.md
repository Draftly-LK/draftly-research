# Target hybrid retrieval figure review

## Pass 1: content and connections

Checked the supplied reviewed PNG against
`figures/target-hybrid-retrieval-pipeline.md`, the target implementation
specification in `docs/retrieval/HYBRID_QUERY_REWRITE_IMPLEMENTATION.md`, and
the citation and claim-checking path in `src/draftly/retrieval/answering.py`.

- Retain the original query alongside a sanitized rewrite. The rewrite adds
  search terms and does not become an authority or legal answer.
- Preserve four core channels: original BM25 and dense, rewritten BM25 and
  dense. The fuller design also has direct and source-hinted channels, so
  label this illustration as a view of the core query channels.
- Fuse the four lists before expanding fused statutory-section seeds.
- Preserve the direct fused list alongside graph candidates in Final RRF.
- Add the answer gate missing from the PNG. Retrieved source-linked sections
  feed answer generation and citation/claim checks before the outcome fork.
- Retain the target/in-progress status. This exact combination is not a
  measured result from the paper and is not represented as deployed.

## Pass 2: layout and readability

- Replace the large, mostly empty vertical panels with compact named cards.
- Keep parallel search cards equal in size and the query paths distinct.
- Give the direct and expanded candidate paths clear labels and arrowheads.
- Keep the rewrite restriction next to the sanitized query as plain text.
- Use the navy, pale blue, and cream style of the two reviewed research
  figures. Avoid a title banner because the presentation supplies its title.
- Check the final image in color and at reduced grayscale size before use.

## Regeneration

- Brief: `paperbanana-target-retrieval-v3-prompt.txt`.
- Renderer: the project's local official PaperBanana launcher, using its
  default Gemini image model and a 4K size request.
- Original: `Draftly-Target-Hybrid-Retrieval-PaperBanana-reviewed.png`.
- Output: `Draftly-Target-Hybrid-Retrieval-PaperBanana-v3.png`.

## Final two-pass review

### Content

- Both query paths remain separate and each feeds BM25 and dense search.
- All four search lists converge at the initial RRF stage.
- Direct fused results and graph-expanded candidates both enter Final RRF.
- Retrieved source-linked sections feed answer generation and the explicit
  citation/claim gate before either outcome.
- The search-only rewrite restriction and in-progress status are intact.
- No metric, deployed-status claim, or new legal citation was introduced.
- Accepted: 9/10. The omitted `ranked lists` connector label is a minor
  presentation variation; the four-list convergence remains explicit.

### Presentation

- Reviewed the complete color render and a reduced grayscale preview at
  1,440 pixels wide. All labels and branches remain readable, with no cropped
  text, overlapping cards, or ambiguous joins.
- Added one navy arrowhead at the graph-input connection using a precise
  raster edit. The pre-edit generated image is retained in ignored `tmp/`.
- Final dimensions: 5,504 × 3,072 pixels. The original reviewed PNG is retained.
- A copy is in `final-submission/figures/research-target-hybrid-retrieval-v3.png`.
