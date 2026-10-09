# Film asset record

## Evidence

The user supplied `draftly-platform/inputs/case-001` and confirmed the owner's
approval for use in this film, including unmasked display. The supplied PDFs
remain unchanged. `scripts/prepare-evidence.py` makes local display copies and
readable crops; `src/film/evidence-sources.json` records SHA-256 checksums and
page numbers. Source contents are not repeated in this document.

The recurring extent is taken directly from the certificate and supplied
instrument. The survey extract shows a different extent. This is presented
as a question about the records, without a legal conclusion or invented alert.

## Product recordings

`capture/record-case.cjs` records the current Draftly frontend against a fresh,
local PostgreSQL database. `capture/serve-case.py` connects the actual backend
services to local OCR and prepared structured candidates. It reads the bundle's
expected values; it does not call a remote extraction provider.

The isolated frontend copy changes local authentication and the document
upload hint to describe the owner-approved file. Its CSS is compiled from the
product's own Tailwind configuration. Product review controls, draft templates
and backend approval rules are retained. The template remains visibly unvalidated.
Recorded clicks are a review demonstration, not evidence of a lawyer validating
this transaction.

Recordings enter the active film through a measured media manifest. Earlier
case recordings cannot be used as an automatic fallback. The Legal sources
recording shows 57 statutes and 18 amendments in the actual interface.

## Brand and fonts

- Logo marks: `draftly-platform/frontend/public`, current product assets.
- Palette: `draftly-platform/frontend/src/styles/globals.css`.
- IBM Plex Sans: the project's existing font asset; its licence is in
  `public/brand/FONT-LICENSE.txt`.
- Display serif: locally available Georgia; no font download during rendering.
- Existing interface background: retained within the recorded product UI;
  no additional stock image was downloaded.

## Sound

`scripts/make-sound.py` generates the folder, page, pen and interface effects,
and the restrained instrumental motif. These are original procedural sounds,
not recordings of a physical desk session. The score and effects require no
third-party stock licence. The film uses cached WAV files and deterministic
frame-driven volume changes.

Voiceover and speech captions are disabled at the user's request. No generated
voice test is connected to either composition.
