# M013 research notes (statutory-qa-v1, unverified)

Matter: Wimala buys land in Galle but cannot come to Sri Lanka to sign the
deed of transfer. One Tier A question (M013-Q01), classified `enrich`.

## Queries run

- `acts` — to see which Prevention of Frauds amendments exist in the corpus.
  Only two: No. 30 of 2022 and No. 4 of 2024.
- `toc 7-1840`, `toc 30-2022`, `toc 4-2024`, then `show 7-1840/s2 --full`,
  `show 30-2022/s2 --full`, `show 4-2024/s2 --full`.
- `edges 7-1840/s2` — surfaced `4-1902/s3A` as `qualifies`, which is the link
  from the Prevention of Frauds Ordinance to the 2022 power-of-attorney regime.
- `toc 4-1902`, `toc 28-2022`, `toc 3-2024`; `show` on 4-1902 s.2, s.3, s.3A,
  s.3B, s.3C.
- `grep "power of attorney" --act 1-1907`, then `show 1-1907/s31 --full` for
  the attorney affidavit rule and rule (30).
- `show 38-2014/s2 --full` to settle the foreign-purchaser point.

## What the answer turns on

Section 2 of the Ordinance was renumbered as subsection (1) and a new
subsection (2) added by Act No. 4 of 2024. Subsection (2)(a) now makes the
transferee a signatory of a transfer deed, and its proviso is the only route
for a transferee who cannot attend: written authorisation of another person,
who must then satisfy subsection (1). Because the authorisation is for a
section 2 transaction and will be signed abroad, Powers of Attorney Ordinance
s.3A(1) and (3) and the s.2 definition govern its execution, and s.3 its
registration.

## Alternatives considered and rejected

- Deeds and Documents (Execution before Public Officers) Ordinance No. 17 of
  1852 s.2 cross-references Prevention of Frauds s.2 and allows execution
  before a District Judge or Commissioner. It is about execution inside Sri
  Lanka before a public officer, not about a party who is overseas, so it does
  not answer this question. Not recorded.
- Registration of Documents Ordinance provisions on registering the deed
  itself were left out: the question is about execution, and a 5-mark answer
  that ranged over registration priority would dilute the gold map.
- Notaries Ordinance s.32 exempts a "power of attorney for use out of Sri
  Lanka" from the boundary-description rule. Wimala's power is for use *in*
  Sri Lanka, so s.32 does not apply and s.3A(3)(b) of the Powers of Attorney
  Ordinance still requires metes and bounds.

## Corpus gaps

Recorded in `corpus_gaps`. The two that matter most: the corpus stores only a
year, not a date of operation, so "in force at 2025-10" rests on the year
alone; and the corpus cannot itself confirm that Act No. 4 of 2024 is the
latest amendment as at the October 2025 session, which is exactly what the
question asks about.

## For the verifier, first

1. Confirm the commencement date of Act No. 4 of 2024 and that no later
   Prevention of Frauds amendment exists before October 2025.
2. Check PROV-M013-013: the corpus text of Notaries Ordinance s.31 renders the
   attorney-affidavit block without a visible rule number, so the label
   "rule (16)(c)" is inferred from position, not read off the corpus.
3. Check whether the enriched date sequence (authority 12 November 2025, deed
   first week of December 2025) should instead require registration to be
   completed before execution as a matter of law rather than prudence; the map
   states it as a practical point because s.3B only obliges the notary to
   search the register.

Validator: `uv run python scripts/statutory-qa/validate_legal_map.py M013`
prints OK with 0 errors and 0 warnings.
