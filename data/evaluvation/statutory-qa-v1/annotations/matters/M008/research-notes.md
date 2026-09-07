# M008 research notes (status=unverified)

Paper 1, question 6, parts (i) and (ii). Both Tier A, both `enrich`. Reference
date 2026-04. Validator: OK, 0 errors, 0 warnings.

## Queries run

- `acts` (confirmed `21-1998` present, no amending Act listed for it);
  `toc 21-1998`; `show --full` on ss. 11, 12, 13, 14, 20, 26, 29, 31, 32, 33,
  34, 35, 57, 66, 67, 75; `show 22-1871/s3 --full`.
- `search "class of title bonafide possession registration"` to confirm s. 14
  is the only section setting out the classes.
- `edges` on s14, s31, s34, s57; `defs 21-1998` for "Title Register" and
  "Land parcel". `check` run on all 14 excerpts; all returned verbatim.

## Alternatives rejected

- s. 20 (general declaration of eligibility as owner) is displaced by s. 14,
  which names the classes. ss. 32-33 (effect of registration, conclusiveness)
  answer "what does he get", not "which class", so they are out of Q01.
- s. 63 and s. 66 dropped as noise; s. 67(2)(g)-(h) carries the "prescribed
  form / prescribed fee" point for Q02.

## For the verifier, in order of risk

1. Q01 is marked `statute_only`. The weak link: "title of Absolute Ownership"
   is undefined in s. 75, so the step from "possession since 1980, no deed, no
   decree" to "outside s. 14(a)" rests on Prescription Ordinance s. 3 alone. A
   lawyer may hold that judicial authority on when prescriptive title vests is
   indispensable, moving the question to `mixed_statute_and_case`/`reserved`.
   FACT-M008-Q01-002 was written to close that gap; check it is enough.
2. Q01 s. 14(b) is permissive ("may"). The conclusion is framed as eligibility
   on the Commissioner's view, not automatic entitlement. Check the framing.
3. Q02 turns on the split between s. 34(2) (Registrar of Title certifies the
   register extract) and s. 34(3) (Superintendent of Surveys, on behalf of the
   Surveyor-General, certifies the map extract). Confirm the corpus text of
   s. 34(3) is not a transcription artefact.
4. `21-1998` is held as `original_or_unconfirmed_consolidation` with no
   amendment events, so a post-1998 amendment would be invisible here.
   Regulations under s. 67 are absent, so no form or fee is stated.
