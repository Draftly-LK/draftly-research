# M086 research notes (statutory-qa-v1, status=unverified)

Matter: Paper 13 Q9(i), exam session October 2019. One Tier A part, action
`keep`, so no enrichment was applied. Five marks.

## Queries run

`acts`; `toc 22-1871`; `toc 23-1927`; `toc 7-1840`; `toc 26-2014`;
`show --full` on 22-1871 s2, s3, s15, on 23-1927 s4, s6, s7, s8, s13, s14,
on 7-1840 s2 and on 1-1907 s31; `edges 22-1871/s3`;
`search "declaration of title deed"`;
`grep "deed of declaration|declaration of title|declaratory"` over the whole
corpus; `grep "prescriptive|prescription" --act 23-1927`;
`grep "declar" --act 12-2006`; `show 1-1907/s31 --provisions`.

## Alternatives rejected

- Registration of Title Act No. 21 of 1998. It has a Declaration of Title
  (s.14, s.22, s.24) but that is an order of the Commissioner or the District
  Court in a title settlement area, not a deed a notary draws. Nothing places
  Thalawathugoda under that Act, and the scenario is a deeds-registration one.
- Civil Procedure Code s.35 (action for a declaration of title). It is the
  litigation route, not a deed, and the question asks for a deed.
- Prevention of Frauds Ordinance s.2 as an operative requirement. The listed
  transactions are dispositive; a declaration is not one of them. Kept as
  background only, and its corpus text carries 2022 and 2024 amendments.
- Notaries Ordinance s.31 generally. The corpus edition is consolidated to
  2024, so only rule (30A), inserted in 2011, was used, as supporting.
- Notaries Ordinance s.31 rule (33) (endorsement on the title deed). It
  presupposes a transfer and an existing title deed; there is neither here.
- Survey Act No. 17 of 2002 and Surveyors Ordinance No. 15 of 1889. Nothing
  in them bears on which deed to draw; the plan is already made.

## Corpus gaps

Set out in full in `legal-map.json`. The two that decide the status: no
provision names or shapes a deed of declaration, and nothing says prescriptive
title vests without a decree. Both are needed, so the question is
`mixed_statute_and_case` and `reserved`, not `proposed_gold`.

## For the verifier, in order

1. The `reserved` call itself. If the verifier reads Registration of Documents
   Ordinance s.8(b), which deems an instrument that declares a right or title
   to land registrable, as statutory recognition of the instrument, the
   question becomes arguable as `statute_only`. That is the single contested
   judgement in this map.
2. Whether s.15(a) of the Prescription Ordinance deserves to be indispensable
   rather than supporting. The scenario is silent on State land, so the point
   is a check the notary must make, not a condition the facts fail.
3. The hop count of 3. It counts Prescription s.3, Registration of Documents
   s.8(b) and s.7(1) and excludes the two out-of-corpus steps.
4. The Prevention of Frauds s.2 excerpt against a pre-2022 edition; the corpus
   text is post-2024.

The validator prints OK with no warnings.
