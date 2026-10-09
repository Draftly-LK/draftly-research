# Draftly demo video

A 9-minute product demo, built with Remotion around real recordings of the
Draftly app. This folder sits outside the product repositories on purpose:
it holds rendered footage and team media, not product code.

## What is here

| Path | What it is |
| --- | --- |
| `src/script.ts` | The narration, section by section (source of truth) |
| `SCRIPT.md` | The narration sheet each member reads from (generated) |
| `src/media.ts` | Where you list your audio, camera clips and the case-law clip |
| `src/Demo.tsx` | The edit: which footage goes in which section |
| `public/footage/` | App recordings, made by `capture/record.cjs` |
| `capture/` | The recording scripts and the synthetic documents they upload |
| `out/` | Rendered video and stills |

## Finish the video

1. **Record narration.** Each member reads their sections from `SCRIPT.md`
   and saves one file per section into `public/audio/`, named as the sheet
   shows. Then set each `audio` entry in `src/media.ts`.
2. **Record a camera clip** of each member (5 to 8 seconds, looking at the
   camera, square or 16:9). Save as `public/camera/<name>.mp4` and set
   `CAMERA` in `src/media.ts`. They appear picture-in-picture at the start of
   each member's part and in the closing credits.
3. **Record the case-law clip** on the hosted site with OBS (about 12 s):
   Legal sources, Case law, "Find similar cases", show the results and the
   "unverified" mark. Save as `public/footage/case-law-live.mp4` and set
   `CASE_LAW_CLIP`.
4. If a narration runs longer than its section, raise that section's
   `seconds` in `src/script.ts`; the footage refits automatically.
5. Preview with `npm run studio`, then render with `npm run render`.

## Re-recording the app footage

The servers must be running locally with the demo settings
(`ENVIRONMENT=local`, `USE_STUB_IDENTITY=true`, `EXTRACTION_PROVIDER=vision-stub`,
`DEMO_RELAXED_GATES=true` in `backend/.env`; `AUTH_BYPASS=true` and
`NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000` in `frontend/.env.local`).

```powershell
cd capture
python make_docs.py                     # the four synthetic documents
$env:MATTER_REF = "RTA-2026-DEMO-SALE-04"; node record.cjs   # a new reference each run
cd ..; node scripts/probe-footage.cjs   # refresh clip lengths
```

Every run creates a new matter, so use a new reference each time.

## Honesty rules for this video

- Every document and value is synthetic. Never record real client files.
- The extraction in this footage is the demonstration reader, not live OCR;
  the video says so on screen.
- The form template is a transcription that the legal team has not
  validated; the video says so. Do not describe exports as filed documents.
- Two matter-wide approval rules are relaxed for the demo; the video says so.
