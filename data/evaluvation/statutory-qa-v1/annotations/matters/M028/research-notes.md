# M028 research notes (status: unverified)

One Tier A question, M028-Q01 (`candidate_action` = keep, so no enrichment):
stamp duty on a deed of gift of a 10-perch land and house at Kalutara.

## Queries tried

- `acts`, then `grep "stamp duty" --act 6-1990`, `toc 12-2006`, `toc 43-1982`,
  `search "stamp duty on deed of gift immovable property rate"`.
- `show 6-1990/s106 --full` gave the definition of "value" for gifted
  immovable property, which is the method the question asks for.
- `grep "per centum|rate of stamp duty"` and `grep "one hundred thousand
  rupees"` corpus-wide, looking for a rate. Nothing.
- `show 1-1907/s31 --full`, `show 31-2022/s16`, `show 6-2024/s3` for the
  current notarial stamping procedure (rule (7A)).

## Alternatives rejected

- Act No. 12 of 2006 as the charging Act: its s.4 list of specified
  instruments omits conveyances of immovable property, and s.13 leaves
  instruments relating to transfer of immovable property outside its
  displacement of the 1982 Act. Only s.9 was kept, as supporting.
- Act No. 43 of 1982 as the charging Act: the land is in the Western Province,
  where 6-1990 applies; its s.15 and s.71 duplicate 6-1990 s.48 and s.106.

## Corpus gap that blocks the question

Section 37 of 6-1990 charges duty "at the prescribed rate" and s.77(1)(a)
leaves the rate to a Gazette regulation that is not in the corpus. The
chargeable value (Rs.2,700,000 = Rs.700,000 + Rs.2,000,000, lower than the
Rs.10,400,000 market value) is fully supported; the money figure is not. Hence
`blocked_missing_authority` rather than `proposed_gold`.

## For the verifier first

1. That Kalutara District is in the Western Province is not established by any
   corpus provision, and the whole map rests on it.
2. Whether Rs.700,000 (paid in 1995) may stand as the Assessor's open-market
   price at acquisition under s.106.
3. Commencement of the Notaries (Amendment) Act, No. 6 of 2024 relative to the
   October 2024 session (PROV-M028-013, -014).
4. The 6-1990 corpus text is poor optical character recognition; excerpts are
   verbatim against the corpus, not against the Gazette.

Validator: OK, no warnings.
