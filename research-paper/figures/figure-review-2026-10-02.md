# Corpus and retrieval figure review

Reviewed the two original PaperBanana PNGs in two passes before regeneration.
The source of truth is `../neurips_2026.tex`, its retrieval-method section,
and `../paper-numbers.tex`. The originals are retained; regenerated images
use versioned filenames.

## Pass 1: factual content and connections

### Syllabus-guided corpus

- The five counts match the paper: 52 principal enactments, 60 amending Acts,
  4,557 sections, 17,854 provisions, and 6,346 typed edges.
- Course tables guide principal-enactment selection. Examination questions
  belong to the separate benchmark construction process.
- Amending Acts remain separate documents. Make this explicit in the redraw.
- The section index and typed graph are outputs of the corpus build. The
  original routes a graph-output connection through the count box, which
  obscures the distinction between a summary and a processing stage.
- Structural checks and heuristic relation typing do not establish legal
  indispensability.

### Retrieval and evaluation

- S1–S5, S6, and S7 are independently evaluated systems. The original connects
  the flat-baseline card to S7 and omits their independent output routes.
- The graph must feed only S7 edge expansion. The original also connects it
  to S6 and visually mixes it with the S6 output.
- Correct S7 order: hybrid ranking, Act routing, scoped search and seed
  selection, typed-edge expansion, date filtering and reranking. The original
  places hybrid seeds before routing.
- Each system produces its own ranking. The retrieval output and proposed
  indispensable bundle are separate inputs to C@k; retrieved sections do not
  produce the reference labels.
- Reference labels remain provisional, with attorney validation pending.

## Pass 2: layout and readability

- Keep the pale blue, cream, navy, white background, and restrained rounded
  cards. Remove redundant stage numbering and the literal `Footer:` label.
- Use a common-input bus and separate-output bus for the method families.
  Route the graph arrow in its own gutter to prevent ambiguous intersections.
- Place both metric inputs directly into the metric card. Avoid the original
  long right-edge loop that ends in the reference-bundle card.
- Keep labels short and readable at full paper width. Preserve all seven
  method names, five S7 stages, six graph relation types, and verified counts.
- Keep the corpus and retrieval diagrams separate, with consistent styling.

## Regeneration specifications

- Corpus: `paperbanana-corpus-v2-brief.txt`.
- Retrieval: `paperbanana-retrieval-v2-brief.txt`.
- Renderer: local official PaperBanana planner and stylist pipeline, using
  the model defaults recorded in `../../scripts/paperbanana_local.py`.
- Each generated output is reviewed for content and visual presentation
  before being accepted.

## First regeneration review

- Corpus v2: counts, relation labels, amendment status, and output fork are
  correct. The selection subtitle was turned into a disconnected card;
  refine it into plain text beneath the course-table sheets. Score: 8/10.
- Retrieval v2: rejected. S3 appears twice; Act routing is missing from S7;
  a retrieved-output arrow enters the proposed bundle; and the footer contains
  duplicated wording. These failures affect content and connectivity.
  Score: 5/10.
- The next render uses shorter specifications, a vertical five-stage S7
  chain, and a metric card between output and reference so the two inputs
  cannot be confused. The renderer receives the corrected brief directly.
- Revised briefs: `paperbanana-corpus-v3-brief.txt` and
  `paperbanana-retrieval-v3-brief.txt`. Requested resolution: 4K.

## Final review: v3

### Content pass

- Corpus: all five counts and all six edge labels match the paper. The
  amendment documents remain separate, the summary stays within the corpus,
  and the corpus forks to the two retrieval representations. Accepted: 9/10.
- Retrieval: five unique baseline rows, S6, and all five correctly ordered
  S7 stages are present. The graph feeds only expansion. Each method family
  has an independent output route. Rankings and the provisional reference
  bundle feed the metric separately. Accepted: 9/10.

### Presentation pass

- Viewed both complete images and reduced grayscale previews at 1,100 pixels
  wide. Labels, numbers, stage arrows, graph arrows, and both scoring inputs
  remain legible. No cropped text or overlapping cards were found.
- The retrieval render has an extra descriptive title. It does not alter
  the method and remains readable; a paper caption can make it redundant.
- The input bus enters the S7 group boundary. It denotes an input to the
  whole method; the internal chain establishes the processing order.
- Final outputs are `syllabus-guided-corpus-paperbanana-v3.png` and
  `retrieval-evaluation-paperbanana-v3.png`, each 5,504 × 3,072 pixels.
- The original PNGs are retained. Rejected v2 candidates are kept locally for
  comparison and are not recommended for publication.
