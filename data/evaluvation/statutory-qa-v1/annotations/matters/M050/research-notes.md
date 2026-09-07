# M050 research notes (status=unverified)

Paper 9, question 5, part 04. One Tier A question, M050-Q01,
`candidate_action = enrich`, reference date 2021-10.

## Queries tried

- `acts`, then `toc 1-1907` to place the notarial duties in section 31.
- `grep "known to (him|the notary)" --act 1-1907` returned only the rule
  (20)(b) wording; rule (9) came from `show 1-1907/s31 --full`.
- `show 31-2022/s16 --full` and `show 6-2024/s3 --full` to date every change
  to section 31; `show 30-2022/s2` for the Prevention of Frauds position.
- `show 1-1907/s32`, `s34`, `s43`, `defs 1-1907`; excerpts confirmed with
  `check`.

## Temporal point, look here first

The corpus carries only the consolidated Notaries Ordinance as amended in 2022
and 2024. Rule (9) in that text allows identity to be established by
inspecting a national identity card, passport bio-page or driving licence, a
route that did not exist in October 2021. The wording in force at the matter
date survives verbatim in `31-2022/s16` as the words quoted for substitution,
so PROV-M050-002 carries that quotation, is marked
`applicable_to_matter_date: false`, and is supporting rather than
indispensable because the amending Act post-dates the matter. The answer is
written to the 2021 wording. If the verifier rejects sourcing the operative
words from an amending Act, the question should move to
`blocked_temporal_uncertainty`.

Related: 6-2024 s.3(3) deleted "and in the latter case," from rule (9) and
s.3(4) repealed rule (10), so the consolidated body runs the good-repute and
declaration limb on inside rule (9); that limb is otherwise unchanged.

## Alternatives rejected, corpus gaps

Section 32 disapplies rules (20) and (23) to (26) only, not rule (9). Section
34 (penalty) was substituted in 2022 and answers consequence, not
circumstance. Prevention of Frauds Ordinance s.2 is background only: its
corpus text is the 2022/2024 version. No pre-2022 edition of the Notaries
Ordinance exists in the corpus, and no pre-2022 text of rule (20)(b), of
repealed rule (10), or of Prevention of Frauds Ordinance s.2.
