# M071 research notes (statutory-qa-v1, unverified)

One Tier A question (M071-Q01, `keep`), 3 marks, April 2020 session.

## Queries run

- `acts` to confirm the Notaries Ordinance (1-1907) and its amendment Acts are
  in the corpus.
- `toc 1-1907`, then `show 1-1907/s31 --full` and `--provisions`. Section 31 is
  one 25k-character section, so the rules had to be read whole and sliced.
- `show` on 1-1907/s32, s33, s34, s9, s4A, s43.
- `show 31-2022/s16 --full` and `show 6-2024/s3 --full` to work out which of
  the section 31 rules were rewritten after the matter date.
- `show 7-1840/s2 --full` (Prevention of Frauds) as a cross-check.

## Alternatives rejected

- Prevention of Frauds Ordinance s.2: the question is expressly confined to the
  Notaries Ordinance, and the corpus text of s.2 is the post-2022 version, so
  it is not cited.
- Rule 31(9) (identification of executants) and rule 31(20)(b), (e), (g): all
  substituted by 31-2022 or 6-2024, so their corpus wording is not April 2020
  law. Left out rather than quoted with a caveat.
- Rule 31(21) and the Second Schedule forms: the Schedule is not a searchable
  section in the corpus, so Form E could not be quoted.

## Corpus gaps

Recorded in `legal-map.json`. The main one: the Ordinance is held only as a
consolidated post-2024 text, so temporal fit was established rule by rule
against the two amending Acts rather than from a 2020 snapshot. Section 34 is
the 2022 replacement, so it is supporting only and flagged not applicable.

## For the verifier

1. Confirm the rule-by-rule temporal check against 31-2022 s.16 and 6-2024 s.3;
   the whole answer depends on rules (12), (22) and (25) being untouched.
2. Check whether rule 31(22) should be read as barring a Colombo notary from
   attesting in Kandy at all, or only outside his judicial zone under s.4A.
   Kandy and Colombo are different zones, so the conclusion holds either way,
   but the reasoning in claim CL-M071-Q01-003 turns on it.
3. The facts do not say which notary attests first or where the land lies; the
   answer states those points conditionally.
