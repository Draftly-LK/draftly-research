# M020 research notes (statutory-qa-v1, status=unverified)

One Tier A question, M020-Q01, `enrich`, 4 marks. Validator: OK, 0 errors,
0 warnings.

## Queries

`acts`; `toc 1-1907`; `show 1-1907/s31 --full` (25k chars, read whole);
`grep "judicial zone"` to tie the Colombo licence to s.3, s.4A and rule (22);
`show` on 1-1907 s.3, s.4A, s.9, s.11, s.13, s.32, s.33, s.34, s.43,
7-1840/s2, 4-1902 s.2, s.3, s.3A, s.3B, s.3C, 17-1852 s.2-s.5, s.7;
`edges` on 1-1907/s31 and /s32; `search "deed of partition co-owners"`.
Every excerpt was `check`ed; one failed (17-1852/s2 begins "be valid", not
"shall be valid") and was corrected.

## Rejected

- Tea and Rubber Estates (Control of Fragmentation) Act No. 2 of 1958 s.4 was
  the only partition-specific hit; excluded by an added fact that the land is
  a residential block. Drop that fact and s.4 becomes indispensable.
- Notaries Ordinance s.11 (fresh warrant for another zone) and s.13 (penalty
  for practising with no warrant at all): neither fits practising outside
  one's area. The penalty for that is s.34(1)(c).
- Prevention of Frauds Ordinance s.2(2)(a) proviso (transferee unable to be
  present may authorise another in writing) is expressed for a transfer deed;
  the attorney route rests on the general words of s.2(1)(a) instead.
- Registration of Documents Ordinance: the question is signature and
  attestation, not registration priority.

## For the verifier, in order

1. Ordinance No. 17 of 1852 s.2 (PROV-M020-017): in the corpus with no
   recorded repeal, but it names the abolished Court of Requests. If spent,
   CL-010, CL-017 and part of CL-019 fall away and the answer still stands on
   the two-notary and attorney routes.
2. Prevention of Frauds Ordinance s.2(1)(a) as amended in 2022 and 2024
   requires signing before a notary "present at the same time and in the
   presence of one another". This map reads that as attaching to each signing
   event, so Notaries Ordinance s.31 rule (25) and s.32(2) still allow two
   notaries at two sittings. A stricter reading kills the primary route.
3. PROV-M020-016 is cited as rule (15A)(c); the corpus carries that paragraph
   in an unnumbered group after rule (15). Check the printed amendment.
4. PROV-M020-011: the corpus row for Powers of Attorney Ordinance s.2 drops
   the defined-term lemmas, so the excerpt starts at "means".

Corpus gaps are listed in `corpus_gaps` in `legal-map.json`.
