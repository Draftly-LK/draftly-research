# M103 research notes

Matter: children of a living testator ask the notary whether he attested their
father's will. One Tier A question (M103-Q01, `enrich`), reference date 2018-10.

## Queries tried

- `acts` to find the notarial statute; `toc 1-1907`.
- `grep "divulge|secre|confiden" --act 1-1907` returned s.23, s.25 and s.31.
  Only s.31 rule (1) is about secrecy; the other two are about transmitting
  certificates and were discarded.
- `show 1-1907/s31 --full` and `--provisions` for the rules on wills:
  (11), (16)(a), (17)(b), (20)(h), (23), (24), (26), (28), (29), (41).
- `edges 1-1907/s31`, then `show` on 20-1976/s10, 47-2011/s2, 47-2011/s3,
  31-2022/s16 and 6-2024/s3 to see whether rule (1) was ever amended. None of
  them touches it, so the corpus text of rule (1) is the 1907 text and was in
  force in October 2018.
- `defs 1-1907` — only three defined terms, none of them "employer".
- `toc 21-1844` (Wills Ordinance) — nothing on custody or revocability.
- Every excerpt confirmed with `check`.

## Alternatives rejected

- s.31 rule (20)(h) (attestation of a will, entry of the testator's name in the
  deed register) was inserted by 31-2022 s.16(11)(d), after the matter date, so
  it is not used at all.
- s.21 (misconduct inquiry, cancellation of warrant) and s.41 (delivery of a
  dead or retired notary's documents) are about later consequences and a
  different trigger; neither bears on whether to answer this inquiry.
- s.34 is kept only as supporting, and marked `applicable_to_matter_date:
  false`, because the corpus text is the section substituted by 31-2022 s.17.
  A penalty for breach of the s.31 rules existed in 2018, but its wording is
  not in the corpus, so nothing in the answer turns on the figure.

## For the verifier

- The hop count is 1. Rule (1) carries its own exceptions in one sentence, so
  nothing outside it is indispensable. Check that reading first.
- "Employer" is undefined in the Ordinance. Treating the testator as the
  employer rests on ordinary meaning plus the added facts, not on a definition.
- The two decisive added facts (FACT-M103-Q01-003 and -004) close the two
  statutory exceptions. If either is thought to over-determine the scenario,
  the conclusion is the part to re-examine.
- The "required to do so by law" limb has no anchor in the corpus; see
  `corpus_gaps`.
