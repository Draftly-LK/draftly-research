# M075 research notes (statutory-qa-v1, unverified)

Paper 12 question 7, April 2020. One Tier A question (M075-Q01, `keep`).
M075-Q02 is Tier B and was not annotated.

## Queries tried

- `acts` — confirmed the Partition Act, No. 21 of 1977 is absent from the corpus.
- `search "partition deed co-owners amicable division"`, `grep "partition"` — the
  only corpus texts mentioning partition by deed are Tea and Rubber Estates
  (Control of Fragmentation) Act ss.4, 6, 8, 11, 14, 15, 25; Stamp Duty Act
  s.5(11); Western Province Financial Statute s.106; Registration of Title Act
  s.63; Apartment Ownership Law s.23. None reaches a 45-perch Ratnapura allotment.
- `toc` and `show --full` on 1-1907, 23-1927, 1-1844, 12-2006, 17-2002;
  `show 1-1907/s31 --provisions`.
- `search "licensed surveyor plan of subdivision of land"` — nothing makes a survey
  plan a condition of validity of a private deed of partition.
- `search "mortgage of undivided share partition mortgagee" --act 6-1949` — nothing
  on the effect of a partition on a mortgage of an undivided share.
- `check` run on all ten excerpts; all returned "OK verbatim".

## Alternatives rejected

- Definition of Boundaries Ordinance ss.8-11: defines boundaries between adjoining
  proprietors, not division of a co-owned allotment.
- Registration of Title Act s.36 and Apartment Ownership Law s.12: both presuppose
  registration under regimes the facts do not engage.
- Stamp duty: left to Tier B M075-Q02; exemptions under 12-2006 s.5 depend on
  Gazetted Orders that are not in the corpus.

## For the verifier

1. The status call. Q01 is `reserved` / `mixed_statute_and_case`. Every step of the
   alternative is statute-backed, but the alternative itself — a co-owner's
   common-law right to partition, and to do so amicably rather than by action — is
   not in the corpus, and neither is the Partition Act. If the benchmark treats
   that recognition as statutory, Q01 could be re-scored `statute_only`.
2. PROV-M075-001: the corpus text of Prevention of Frauds Ordinance s.2 is
   consolidated to 2024 and the quoted paragraph (a) wording postdates 2020-04.
   The notarial-execution requirement is not in doubt; the 2020 wording is.
3. Notaries Ordinance s.31 excerpts were trimmed to fall outside the 2022 and 2024
   substitutions (checked against 47-2011/s2 and 31-2022/s16 items 9 and 10).
4. Corpus artefacts reproduced verbatim: "staled" in 23-1927/s13(3),
   "therin"/"therto" in 1-1907/s31(16)(a), duplicated paragraph (a) in 17-2002/s13.

Validator: OK, 0 errors, 0 warnings.
