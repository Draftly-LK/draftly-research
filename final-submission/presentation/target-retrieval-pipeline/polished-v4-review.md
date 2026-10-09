# Polished target retrieval diagram

The v4 redraw uses deterministic FigureSpec geometry, equal search cards,
numbered stages, and an editable SVG. The original and PaperBanana v3 remain
available for comparison.

## Files

- `Draftly-Target-Hybrid-Retrieval-Polished-v4.png`: 4,800 × 2,700 pixels.
- `Draftly-Target-Hybrid-Retrieval-Polished-v4.svg`: editable vector figure.
- `Draftly-Target-Hybrid-Retrieval-Polished-v4.pdf`: vector PDF.
- `figures/specs/Draftly-Target-Hybrid-Retrieval-Polished-v4.json`: FigureSpec.
- `build_polished_target.py`: regeneration script using the installed
  FigureSpec renderer, CairoSVG, and Pillow.

## Review

- Original and sanitized queries each feed lexical and dense search.
- All four ranked lists enter initial RRF fusion.
- Fused results and typed graph candidates both enter final RRF.
- Retrieved sections feed answer generation and citation/claim checks.
- The second outcome now says **Not enough legal evidence**.
- The search-only rewrite restriction and target/in-progress badge remain.
- Checked the full-color render and a 1,600-pixel grayscale preview; adjusted
  arrow routes and text so connectors do not pass through intermediate cards.
- FigureSpec validation passes without warnings.

A PNG copy is in
`final-submission/figures/research-target-hybrid-retrieval-polished-v4.png`.
