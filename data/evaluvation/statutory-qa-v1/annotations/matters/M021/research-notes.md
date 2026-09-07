# M021 research notes (status=unverified)

Matter: P02-Q09-M00, one Tier A question (M021-Q01), reference date 2025-10.

## Queries run

- `acts` to locate the Wills Ordinance (21-1844) and its amending Acts.
- `toc 21-1844`, `toc 29-2022`, `toc 5-1993`; `show --full` on every Wills
  Ordinance section and on 29-2022 ss.2-6.
- `search "last will testator attested notary witnesses"`,
  `grep "will" --act 7-1840`, `grep "will" --act 1-1907`.
- `show 7-1840/s4 s9 s11 s16 --full`, `show 30-2022/s3 --full`.
- `show 1-1907/s31 --full` and `--provisions` to isolate rules (8), (12),
  (17)(b)(iii) and (20)(h); `show 31-2022/s16` and `show 6-2024/s3` to date
  rule (20)(h) to Act No. 31 of 2022 and rule (17)(b)(iii) to Act No. 6 of 2024.
- `edges 21-1844/s2`, `edges 7-1840/s4`, `defs 21-1844` (no definitions row).

## What the corpus shows

The Wills Ordinance table of sections runs s.1, s.2, then s.5 to s.9. Sections 3
and 4 are gone, repealed by Act No. 29 of 2022 ss.3 and 4. Section 2 as
substituted by that Act carries the age rule: eighteen years. The procedure
comes from outside the Wills Ordinance, mainly Prevention of Frauds Ordinance
s.4 (renumbered and expanded by Act No. 30 of 2022) and Notaries Ordinance
s.31.

## Alternatives considered and rejected

- Wills Ordinance s.7(2) (joint wills, testamentary proceedings under CPC
  Chapters XXXVIII/XXXVIIIB) was left out: the enrichment makes this a single
  will, and the provision bites only after death.
- Prevention of Frauds Ordinance ss.5 to 8 (appointments, revocation,
  alteration, revival) were read but not recorded; none is needed to answer the
  age or first-execution question.
- Notaries Ordinance s.31(11) exempts wills from the requirement to explain the
  instrument before the witnesses. Not recorded, since it removes a step rather
  than adding one.

## For the verifier

1. The classification is `statute_only`. The soundness-of-mind question raised
   by the chronic illness is handled only through the notary's statutory duty in
   Notaries Ordinance s.31(20)(h); the substantive common-law test is listed in
   `corpus_gaps`. Check whether that line holds.
2. Four provisions cite section `1-1907/s31` with different `subsection` values,
   since s.31 is one corpus section holding all notarial rules.
3. `validate_legal_map.py M021` prints OK with no warnings.
