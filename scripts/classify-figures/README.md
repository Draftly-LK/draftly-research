# Classification EDA figures

Figures for the two classification problems in the CommonLII judgment corpus
(9,601 parsed judgments, LKCA + LKSC, reported 1878–2010):

- **layout class** — `category` on the parsed judgments (`dense_br_nlr`,
  `paragraph_nlr`, `structured_slr`, `late_slr_font`). Decides which parser
  branch runs.
- **conveyancing gate verdict** — `verdict` in
  `evaluation/runs/conveyancing-gate-v2/conveyancing_labels.csv`
  (`required` / `review` / `not-required`). Decides what stays in scope.

Every label plotted here is `status=unverified`. The gate is a deterministic
scorer, not a lawyer sign-off.

## Regenerating

```powershell
uv run python scripts/classify-figures/make_classify_figures.py
uv run python scripts/classify-figures/make_classify_figures.py --out /tmp/figs
```

Read-only: it touches `data/commonlii/parsed/{LKCA,LKSC}/judgments.csv` and the
gate labels, writes PNGs here and the numbers behind each figure to `tables/`.
No model calls, no spend. Figures 07–10 are skipped if the gate labels are
missing.

## What each figure shows

| Figure | Reading |
| --- | --- |
| `01-layout-class-balance` | 58% of the corpus is `dense_br_nlr`; `late_slr_font` is 320 cases. Any accuracy number needs a per-class breakdown. |
| `02-layout-class-over-time` | Layout class is almost a function of reporting decade. A year or citation-year feature would leak the label; split train/test by era, not at random. |
| `03-layout-confidence` | Confidence is near-degenerate (median 0.919) except in `paragraph_nlr`, where 41% sits below 0.90 — that class is where a review threshold would actually bite. |
| `04-field-completeness` | Which extracted fields exist as features, per class. `hearing_dates` is 20% in `paragraph_nlr` vs 82% in `late_slr_font`; `bench` and `case_numbers` swing the other way. Missingness itself carries class signal. |
| `05-document-length` | SLR classes run ~1.6× longer at the median, but the IQRs overlap — length is a weak feature on its own. |
| `06-parser-damage` | Encoding/malformed-tag rates by class and decade. `structured_slr` is the most damaged (36% / 24%). This is the label-noise floor for anything read off body text. |
| `07-gate-verdicts` | 28% required / 14% review / 58% not-required, plus what actually decided each verdict. Half the corpus is not-required with no rule firing at all. |
| `08-gate-score-distribution` | The score is zero for most of the corpus; the informative cases are a long right tail. Band edges are visible as colour changes. |
| `09-gate-feature-separability` | `proceeding_type` is a strong prior (testamentary 60% required, election petition ~0%), and damaged text roughly doubles the review rate. |
| `10-gate-verdicts-over-time` | Required cases appear in every decade, so a corpus sample should be stratified by decade rather than taken from the recent end. |

## Notes on the plots

- Colours are the four categorical slots of the shared palette, in fixed order,
  validated for colour-vision deficiency; a class keeps the same colour in every
  figure. Two slots fall below 3:1 contrast on the surface, so every bar carries
  a value label and every figure ships its numbers in `tables/`.
- Decades with fewer than 25 judgments (the 1870s and the 2010s stub) are
  dropped from the time panels and reported on stdout — a percentage over seven
  cases is noise, and the stub bars only stretched the axis into empty margins.
  There is no 1880s data in the corpus, so that tick sits empty in figure 10.
- Figure 03 folds the handful of cases below 0.84 confidence into the leftmost
  bin and states the count in the panel.
