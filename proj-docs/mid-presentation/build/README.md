# Mid-evaluation deck generator

Builds `../Draftly - Mid Evaluation.pptx` (30 slides) from the beige/brown
template in the parent folder. The template supplies the theme and the embedded
Open Sauce fonts; every slide is drawn from scratch, so editing text means
editing Python, not the `.pptx`.

```powershell
python make_deck.py    # rebuild the deck
python qa_text.py      # dump slide text, flag template leftovers
```

## Files

| File | Holds |
| --- | --- |
| `kit.py` | Palette, geometry, text/shape primitives, overflow estimator |
| `deck_part1.py` | Slides 1-14, plus the card / flow / divider helpers |
| `deck_part2.py` | Slides 15-30 |
| `make_deck.py` | Strips the template slides, calls both parts, saves |
| `qa_text.py` | Content QA pass over the built file |

`make_deck.py` prints an overflow warning for any text box whose estimated
bottom passes `kit.BODY_BOTTOM`. The estimator is approximate — render to
images before trusting a layout change:

```powershell
# export via installed PowerPoint, then rasterise
powershell -Command "$pp = New-Object -ComObject PowerPoint.Application; $pres = $pp.Presentations.Open('<abs path>.pptx', $true, $false, $false); $pres.SaveAs('<abs path>.pdf', 32); $pres.Close(); $pp.Quit()"
pdftoppm -jpeg -r 80 deck.pdf slide
```

## Numbers in the deck

Corpus and extraction figures come from the repository `README.md`; platform
figures come from `draftly-platform/backend/contracts/rta-rule-pack.v1.json`
and `backend/docs/services/README.md`. Re-check both before presenting — the
README is the source of truth and its numbers move as pipelines run.
