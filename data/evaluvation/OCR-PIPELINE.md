# Law College past-paper OCR

We deskewed the scan first, then ran OCRmyPDF over the straightened images.
That order is the point of this directory. The source PDF is a 67-page scan of
a Sri Lanka Law College Attorneys-at-Law final examination paper with no text
layer, so every page has to be recognised from pixels, and how straight and
which way up those pixels are turned out to matter more than any OCR setting.

Deskewing first beat letting OCRmyPDF do its own rotate and deskew pass: 122,524
characters against 119,590, and 3.8 seconds per page against 4.8.

Everything here is `status=unverified`. There is no ground truth for this
document in `ocr-benchmark/labels/`, so the character counts below measure how
much text came out, not how much of it is correct.

## The two stages

### 1. Deskew

`scripts/deskew_pages.py` renders each PDF page at roughly the source scan
resolution, corrects orientation, deskews, and writes a JPEG plus an auditable
row in `manifest.csv`. Output is in `0-deskew-outputs/` (67 images, 92 MB).

The automatic pass found very little to fix. Only 4 of 67 pages had measurable
skew, all under 0.6 degrees, because the scan was captured with CamScanner,
which already straightens on capture.

Orientation was the real problem. 30 pages were upside down. The script splits
that decision in two because the halves are not equally trustworthy:

- The portrait/landscape axis comes from projection-profile sharpness and is
  reliable, scoring 0.85 to 0.99 confidence on these pages.
- The 180-degree flip is not reliably detectable this way. A projection profile
  is identical for 0 and 180 degrees, so the flip needs a text-direction signal,
  and the baseline-sharpness heuristic used here scored 5 of 9 on a spot check.

Because of that measured weakness, flip correction is off by default. The script
recorded its guess in `rotation_detected` and flagged nothing, and the 30 pages
were rotated by hand. The heuristic turned out to be right on all 30, so the
5-of-9 estimate was too pessimistic. Passing
`--detect-flip --rotation-threshold 0.3` reproduces the same 30 corrections
automatically.

Do not re-run `deskew_pages.py --overwrite` against `0-deskew-outputs/`. It
regenerates all 67 images from the source PDF and would discard the manual
rotations.

### 2. OCR

`ocrmypdf-script.py` runs OCRmyPDF over the pages and records text yield and
wall-clock cost. It reads `0-deskew-outputs/` and writes only to
`1-ocrmypdf-outputs/`, so it cannot touch the deskewed images.

It runs two arrangements over the same 67 pages:

- `raw`: the original PDF, with OCRmyPDF doing its own rotate and deskew.
- `deskewed`: the images from `0-deskew-outputs/` repacked into a PDF at 300
  dpi, with OCRmyPDF's preprocessing switched off.

Neither variant does noise removal. `--clean` needs `unpaper`, which is not
installed.

Tools: OCRmyPDF 16.13.0, Tesseract 5.4.0.20240606, Ghostscript 10.07.1,
language `eng`.

## Results

| variant | pages | chars | words | empty | sec | s/page |
| --- | --- | --- | --- | --- | --- | --- |
| raw | 67 | 119,590 | 21,672 | 0 | 322.9 | 4.8 |
| deskewed | 67 | 122,524 | 21,746 | 0 | 257.9 | 3.8 |

The deskewed variant yielded more text on 49 of 67 pages and ran about 20%
faster, since OCRmyPDF skips its own preprocessing.

Splitting those pages by whether they were among the 30 hand-rotated ones shows
where the gain came from:

| pages | raw | deskewed | delta | deskewed wins |
| --- | --- | --- | --- | --- |
| the 30 rotated by hand | 51,331 | 54,408 | +3,077 (+6.0%) | 30/30 |
| the other 37 | 68,259 | 68,116 | -143 (-0.2%) | 19/37 |

The whole improvement is the rotation. Every one of the 30 fixed pages
improved, and the remaining 37 are a wash, which fits the finding that only 4 of
them had any skew worth correcting. Deskewing bought almost nothing here.
Getting pages the right way up bought 6%.

Two pages got worse and are not in the rotated set: page 64 dropped from 292
characters to 133, and page 18 from 1,160 to 838. Pages 64, 65 and 66 all yield
under 400 characters with alpha ratios near 0.6, which usually means sparse or
handwritten content rather than a rotation problem. Check them by eye before
trusting them.

## Layout

```text
Past Paper Question from Law College.pdf   source scan, 67 pages, no text layer
0-deskew-outputs/                          deskewed images + manifest.csv
1-ocrmypdf-outputs/
  manifest.csv                             per-page chars/words/lines/alpha
  run.json                                 tool versions, args, per-variant totals
  run.log                                  progress log
  raw/, deskewed/                          ocr.pdf, sidecar.txt, pages/*.txt
```

## Reproducing

The deskew step is destructive to the manual rotations, so it is listed for
reference rather than as a step to re-run:

```bash
# stage 1, only on a fresh output directory
uv run python scripts/deskew_pages.py --format jpg --detect-flip --rotation-threshold 0.3

# stage 2
uv run python data/evaluvation/ocrmypdf-script.py --variant both
uv run python data/evaluvation/ocrmypdf-script.py --variant deskewed --overwrite
```

A variant whose output already exists is skipped unless `--overwrite`, and its
numbers are rebuilt from the sidecar text, so an interrupted run resumes at
variant granularity. Running a single variant rewrites `manifest.csv` and
`run.json` with only that variant's rows; re-run with `--variant both` and no
`--overwrite` to fold both back in without redoing any OCR.

A full 67-page run takes about 5 minutes per variant. Progress goes to stdout
and to `1-ocrmypdf-outputs/run.log`.

## Caveats

Character counts are yield, not accuracy. A page that recognises 2,000
characters of scanner speckle scores higher here than one that recognises 1,500
correct ones. The `alpha_ratio` column in `manifest.csv` is a rough guard: a low
letter share flags pages where OCR found marks rather than words. Scoring
against labels is what `ocr-benchmark/score.py` does, and this directory does
not imitate it.

The source PDF declares a 2192x3152 point page box, so OCRmyPDF reports 72 dpi
and warns on every page. A 2192 pt page rasterised at 72 dpi is still 2192 px,
so Tesseract sees the scan's real pixels and only the dpi hint is wrong.
`--oversample` is wired up in case that hint matters on another document.
