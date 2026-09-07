# M101 research notes (statutory-qa-v1, status=unverified)

Matter: Paper 15 Q8 part 2, exam session October 2018. One Tier A question,
classified `enrich`, so enrichment was applied.

## Queries run

`acts`; `toc 1-1907`; `show --full 1-1907/s31`, `s32`, `s33`, `s38A`, `s43`,
`s5`; `grep "unable to sign|cannot sign|mark" --act 1-1907`;
`grep "Form E" --act 1-1907`; `show --full 7-1840/s2`; `toc 31-2022`;
`show --full 31-2022/s16`, `6-2024/s3`, `47-2011/s2`, `47-2011/s3`,
`13-2013/s2-s4`; `grep` for rules (11), (12), (15), (20)-(22) in 20-1976;
`check` on all twelve excerpts (all returned verbatim).

## Alternatives rejected

- Section 38A (notary to explain the true nature of the transaction) reads as
  if it were on point, but it was inserted only by Act No. 6 of 2024 and is
  not law at the reference date.
- Rule (15A) of section 31 (thumb impression by every executant of a deed
  affecting immovable property) was inserted by Act No. 31 of 2022. Applying
  it would wrongly require a thumb impression from the brother who signs in
  Sinhala; the answer flags this expressly.
- Prevention of Frauds Ordinance s2 is background only. Its corpus text is the
  post-2022/2024 version, so its wording cannot be relied on for 2018.
- Section 32 (rules disapplied in special cases) and section 33 (form defects
  do not invalidate) were read and dropped: neither is engaged by a domestic
  deed of transfer executed in the ordinary way.
- Section 5 (a notary may qualify in a second language) was read and dropped;
  the question is what this notary must do under the licence he holds.

## Corpus gaps

Set out in full in `legal-map.json`. The three that matter: rule (10) of
section 31 is absent from the corpus body because the consolidation applies
the 2024 repeal, yet it was in force in October 2018; Form E of the Second
Schedule is not in the corpus, so the attestation form can only be described
from rule (20); and rule (14) is held only in its 2022 wording, which is why
it is carried as supporting and nothing indispensable rests on it.

## For the verifier, in order

1. The temporal split inside section 31. Rules (11), (12), (15), (18), (20)(a)
   and (d), (21) and (22) were checked line by line against 31-2022 s16 and
   6-2024 s3 and are untouched, so their corpus text is 2018 text. That check
   is the load-bearing step of this map.
2. Whether the missing rule (10) changes the instructions the notary must
   give. It cannot be checked inside the corpus.
3. Whether the brother who signs in Sinhala is properly treated as unable to
   read the English deed. That is an added fact (FACT-M101-Q01-003), not
   something the original scenario states.
4. Whether rule (15) is read correctly as certifying the mark and the
   foreign-language signature in the same words, with the left thumb
   impression required only for the mark.
