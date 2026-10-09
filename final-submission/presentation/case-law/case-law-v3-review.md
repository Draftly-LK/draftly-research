# Case-law retrieval figure v3

Recreated `image.png` using the local PaperBanana planner, stylist, and
visualizer. The prompt is `paperbanana-case-law-v3-prompt.txt`.

## Content review

Checked against `src/draftly/case_retrieval/search.py`,
`scripts/similar-case-retrieval/RESULTS.md`, and the presentation evidence map.

- Preserves the 5,121 conveyancing-flagged / 9,177 collected corpus counts.
- Shows lexical and case-graph retrieval as active parallel paths.
- Shows dense embeddings as a regular architectural branch. The bottom
  pilot-results note retains the recorded dense-inactive evaluation status.
- Separates RRF fusion from lexical/graph corroboration.
- Shows cited similar cases and no-similar-case outcomes separately.
- Retains 14/20 and 10/20 as LLM proxy results on different corpus snapshots.
- Does not depict a statutory answer generator or legal-holding verification.

## Visual review

- Reviewed the full-color figure and a 1,440-pixel grayscale preview.
- Labels fit their cards; corroboration is readable and spelled correctly.
- All three paths enter fusion, and both outputs leave the gate.
- Dense-channel borders and arrows are solid and match the other channels.
- No connector crosses a card or label; pilot cards have no comparison arrow.
- Accepted at 9/10: the two output cards share the same fill, but their labels
  clearly distinguish the outcomes.

## Outputs

- `Draftly-Case-Law-Retrieval-PaperBanana-v3.png`: 5,504 × 3,072 pixels.
- `case-law-v3-grayscale-preview.png`: reduced review copy.
- `final-submission/figures/research-case-law-retrieval-v3.png`: library copy.

The original `image.png` remains available.

## Dense-channel correction

At the user's request, removed the optional label, dashed border and arrows,
and optional-channel legend. The dense card now says **Semantic similarity**.
`fix_dense_channel.py` applies this precise raster edit to the retained
`Draftly-Case-Law-Retrieval-PaperBanana-v3-before-dense-fix.png`.
The color, grayscale-preview, and figure-library copies were all updated.
