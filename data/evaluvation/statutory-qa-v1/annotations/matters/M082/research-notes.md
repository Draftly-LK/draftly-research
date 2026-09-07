# M082 research notes (statutory-qa-v1, unverified)

One Tier A question, M082-Q01, paper 13 q4(iii), 3 marks, reference date 2019-10.

## Queries tried

- `acts` to see the closed statute list; the Registration of Documents
  Ordinance No. 23 of 1927 was the obvious home for a notice-of-presentation
  device.
- `grep "[Cc]aveat"` across the whole corpus. It returned s.32, s.33, s.34 and
  s.43 of the 1927 Ordinance, the fee item in Act No. 21 of 2013 s.5, the 2022
  rewrite in Act No. 32 of 2022 ss.2, 3 and 5, and Civil Procedure Code s.536
  (a testamentary caveat, not this one).
- `toc 23-1927`, then `show --full` on ss.2, 3, 6, 8, 12, 14, 26, 27, 29, 32,
  33, 34, 43, 49, 50.
- `edges 23-1927/s32` and `defs 23-1927` both returned nothing, so the links to
  s.8, s.14 and s.2 were made by reading, not by the graph.

## Alternatives rejected

- Civil Procedure Code s.536 caveat: testamentary intervention, unrelated to
  land registration.
- Registration of Title Act No. 21 of 1998: a different register, and nothing
  in the facts says this land is on the title register.
- Priority notice (s.30) and lis pendens (s.11): both give priority or notice
  to the world, but neither produces service of notice on the applicant, which
  is what the question asks for.
- s.26 (who may present an instrument) and s.27 (day book): true but not
  needed once s.32(1) and s.32(2) are read together, so they were left out.

## Corpus gaps

The Second Schedule of forms, the First Schedule of fees and any s.49
regulations are absent, so "the prescribed form" cannot be named or numbered
from the corpus and the fee is reachable only through the 2013 amending text.
The principal Act is a consolidated 1990 edition, so post-1990 amendments not
separately in the corpus cannot be checked.

## For the verifier first

1. The temporal line. Act No. 32 of 2022 rewrote s.32 (interest requirement,
   affidavit and attorney certificate, two-year cap, sixty days instead of
   thirty). The answer is written on the pre-2022 text, and PROV-M082-015 is
   carried as background with `applicable_to_matter_date: false` only to record
   that the change was checked and excluded. Confirm nothing between 1990 and
   2019 also changed s.32.
2. Whether s.32(6), s.33, s.34 and s.43(2) belong in a 3-mark answer at all.
   They are all `supporting`, so dropping them costs nothing structurally, but
   a marker may consider them padding.
3. The s.34 claim CL-M082-Q01-016 is marked `inferential`: "reasonable cause"
   is not defined in the corpus and the conclusion that this caveator has it is
   a judgement on the added facts, not a statutory deduction.
4. PROV-M082-011 quotes "Us pendens" verbatim; that is an OCR error in the
   corpus text of s.34, not a transcription mistake here.

Validator: `M082: OK errors=0 warnings=0`.
