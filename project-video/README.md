# Draftly product film

“One property transfer. Follow the evidence.” The active edit is 10 minutes,
with a separate 45-second opening. It uses the approved case-001 source scans,
current Draftly interface recordings, original sound effects and music.
Voiceover and speech captions are off, as requested.

## Preview and render

Open PowerShell and run:

```powershell
cd D:\projects\Draftly-Project\draftly-research\project-video
npm ci
npm run studio
```

Choose **DraftlyOpening** for the opening or **DraftlyDemo** for the complete
edit. Studio also opens at <http://localhost:3000/DraftlyDemo> when port 3000
is available.

```powershell
npm run check
npm run render:opening
npm run render:review
```

The opening is saved to `out/draftly-opening.mp4` at 1080p. The complete
review cut is saved to `out/draftly-review.mp4` at 720p. A review cut can contain
clearly labelled editorial sequences where a recording is still required;
it must not be described as the finished film.

For the final 1080p render, once every recording is supplied:

```powershell
npm run render:final
```

This command checks required recordings before writing `out/draftly-demo.mp4`.
No speech is generated during preview or rendering.

## Change the edit

- `src/film/edit.ts`: chapters, shot lengths, source choices and footage crops.
- `src/film/Opening.tsx`: folder arrival, readable extent crops and viewer handoff.
- `src/film/Scenes.tsx`: document comparisons and editorial sequences.
- `src/film/media.json`: imported recording paths and measured durations.
- `SCRIPT.md`: the visual script; refresh it with `npm run script`.

The current compositions use `src/film/`. Previous sequences are retained
outside the active compositions.

## Recordings still needed

The current edit has 10 imported, checked product recordings. Nine recording
slots remain open, including the working instrument, review record and research
answer journey. The attempted draft recording did not reach the instrument and
is excluded from the edit. A complete final film has not been rendered.

Run `npm run check` for the exact current list. Put recordings in
`public/footage/`. The remaining research recordings must show the current
product, its actual answer and source passages, without claiming an unresolved
question was answered or a research lead was legally verified.

Client originals remain in `draftly-platform/inputs/case-001`. Display copies
and recordings show them without masking under the user's confirmed owner
approval. These local assets are ignored by Git. Do not commit or publish them
as part of routine code work.

After a fresh checkout, prepare the display copies from the approved local
bundle before previewing. With PyMuPDF and Pillow installed in the repository's
Python environment, run these commands from `project-video`:

```powershell
..\.venv\Scripts\python.exe scripts/prepare-evidence.py
..\.venv\Scripts\python.exe scripts/make-sound.py
```

The checked recordings must also be restored locally at the paths listed in
`src/film/media.json`. Their measured durations are recorded there. Missing
local files cause `npm run check` to fail rather than silently substituting
older footage.

## Recording method

The local capture harness uses an isolated database and a copy of the current
frontend. It reads source PDFs unchanged, performs local English OCR, and
supplies prepared structured candidates from the bundle's `expected-fields.json`.
Remote extraction keys are disabled. Review and draft actions use the actual
backend services; approval rules remain enforced. Film labels identify the
prepared extraction and review demonstration. No real-case legal certification
or successful registration is claimed.

See [ASSETS.md](ASSETS.md) for asset provenance and
[src/film/evidence-sources.json](src/film/evidence-sources.json) for original
source checksums.
