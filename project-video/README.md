# Draftly product film

The active composition is **DraftlyFullFilm**: 10 minutes at 1920 x 1080,
30 fps. It follows the eleven chapter boundaries in `SCRIPT.md`, preserves
its existing opening, and continues with the same owner-approved case.
The user's later directions take precedence over the script's older production
notes: real case documents, no masking, no voiceover, and no on-screen label
suggesting invented client records. Music and purposeful sound effects remain.

## Preview and render

Run in PowerShell from this folder. Dependencies are already installed.

```powershell
cd D:\projects\Draftly-Project\draftly-research\project-video
npm run studio -- --port=3010
```

Choose **DraftlyFullFilm**, or open
<http://localhost:3010/DraftlyFullFilm>.

```powershell
npm run check:full
npm run render:full
```

The MP4 is written to `out/draftly-full-film.mp4`. The fast exporter reuses
this workstation's owned capture Chrome at `127.0.0.1:9223`, the existing
`out/draftly-opening.mp4`, and installed FFmpeg. It renders authored Remotion
motion, places the original recordings at natural speed, and caches completed
shots in `out/long-film/`. It does not attach to a personal Chrome profile.
Keep the owned capture browser open while using this command.

For a normal Remotion render without that capture browser, use:

```powershell
npm run render:full:standalone
```

This renders all 18,000 frames directly and takes longer. The same composition
and assets are used. `npm run render:opening` regenerates the 45-second opening.
The full-film exporter also includes the corrected alignment in its first shot.

## What is shown

- The source bundle and its actual extent discrepancy, which stays unresolved.
- The supplied four practitioner portraits and titles from `lawyers.png`, with
  five lawyer discussions, one workflow contribution, and Legal IR/NLP guidance.
- Actual matter setup, document processing results, source review and **Approve**
  fact controls. Prepared extraction results are explicitly labelled.
- Form 8 working-draft generation from accepted facts, followed by **Confirm**
  field actions. Twenty populated fields were checked against their fact values,
  versions and source references. Field confirmation and final approval differ.
- Actual unresolved particulars, preflight blockers and an internal working-draft
  manifest. No executable instrument, approval or registration is claimed.
- The separate Research workspace, source-scope controls, and the Legal sources
  catalogue. Visible counts are 57 statutes and 18 amendments.
- The recorded research availability gap, an official Title Act source lead,
  the supplied research-paper title and the retrieval contribution graphic.

The date-sensitive source-inspection sequence is visibly **Planned**. The local
matter assistant and grounded-answer composer are unavailable in these captures;
no answer or supporting passage is fabricated. This local availability result
is not a conclusion about which law exists in the corpus. No benchmark result
is asserted. The research paper is shown without its numerical result paragraph.

## Editing and assets

- `src/long-film/edit.json`: editable shots, timings, crops and on-screen wording.
- `src/long-film/FullFilm.tsx`: the complete composition and audio timeline.
- `src/long-film/Editorial.tsx`: documents, practitioners and closing.
- `src/long-film/ResearchEditorial.tsx`: research graphics and planned inspection.
- `src/long-film/media.json`: measured recording durations and dimensions.
- `src/film/Opening.tsx`: existing intro, with its paper alignment corrected.
- `src/continuation/portraits.json`: original portraits and supplied role wording.

`public/evidence/identity.png` is now upright: its display copy is rotated
90 degrees counterclockwise. `scripts/prepare-evidence.py` preserves this on
regeneration and records the display rotation. Source PDFs remain unchanged.

Owner-approved client media, portraits and rendered MP4s stay local and ignored
by Git. Recordings belong in `public/footage/`, portraits in `public/people/`,
and document display copies in `public/evidence/`. The supplied paper and lawyer
reference images are preserved separately, so replacing `image.png` cannot
replace the film's research image. See [ASSETS.md](ASSETS.md) for provenance.

## Optional replacement recordings

No narration files are needed. All assets for the current ten-minute edit are
present. These two recordings would allow replacing its truthful availability
states when the corresponding services are available:

- `public/footage/matter-conversation.mp4`: Overview conversation followed by
  the same saved conversation in the full matter Assistant.
- `public/footage/research-answer-current.mp4`: the same matter-related question,
  a currently approved answer, and its opened supporting passage.

After importing them, update the relevant shots in `src/long-film/edit.json`;
there is no automatic fallback to old research answers.

## Capture boundaries and earlier edits

Chrome DevTools could not attach to the existing Chrome profile. A fresh hosted
session required sign-in. Captures therefore use the actual application in an
isolated local database; existing production records were preserved. The local
harness supplies prepared candidates from the approved bundle. Fact approval,
draft generation, field confirmation and the manifest use the actual backend
and its existing gates. Recorded clicks demonstrate the workflow; they do not
constitute professional validation of the transaction.

The earlier **DraftlyWorkflowFilm** remains as a separate 105-second composition
and `out/draftly-workflow-film.mp4`. Its six-group living checklist and agent
suggestion are explicitly labelled workflow concepts. The older **DraftlyDemo**
is a different unfinished composition; its `render:final` command is not the
full-film delivery command above.

## Verified export

`out/draftly-full-film.mp4` is 600.000 seconds, 18,000 frames and 34,332,185
bytes, with H.264 video at 1920 x 1080/30 fps and 48 kHz AAC audio. The complete
file decoded without errors. Audio peak is -10.5 dBFS, with no clipping.
Representative evidence, fact-approval, draft-confirmation, research, closing
and chapter-boundary frames were inspected. TypeScript, the 47-asset check and
Markdown lint passed. Verification metadata, logs and images are saved under
`out/long-film/`.

`out/draftly-opening-aligned.mp4` is the corrected 45-second opening with sound.
The certificate and instrument pages fit their full height, including the lower
stamps and signatures. The latest correction preserves all timings and the
original audio. After future edits to `Opening.tsx`, regenerate the opening
with `npm run render:opening` before using the fast full-film exporter.
