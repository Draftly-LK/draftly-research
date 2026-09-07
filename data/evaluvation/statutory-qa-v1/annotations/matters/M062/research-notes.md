# M062 research notes (statutory-qa-v1, unverified)

One Tier A question (M062-Q01, `enrich`), reference date 2020-10.

## Queries tried

`acts`; `toc` for 1-1972, 1-1907, 2-1958, 38-2014, 12-2006; `show --full` on
1-1972/s3, s5, s8, s13, s66; 2-1958/s3, s25; 38-2014/s1, s2, s4, s18, s25;
1-1907/s31, s37, s38; 7-1840/s2; 23-1927/s7; 12-2006/s3, s4, s6;
`search` in 7-2007 for "major transaction", "execution of deed company seal",
"capacity rights and powers"; `defs` for 1-1972 and 38-2014; `edges 1-1907/s31`;
`show --provisions` on 1-1907/s31 to recover rule numbering; `check` on all 24
excerpts (all returned OK).

## Alternatives rejected

- Stamp Duty (Special Provisions) Act, No. 12 of 2006. Section 4 does not list a
  deed of transfer of immovable property among the specified instruments, so it
  is not the charging provision here. Conveyance duty is a provincial levy and
  the corpus holds only the Western Province Financial Statute; Bandarawela is
  in Uva. Dropped, recorded as a corpus gap.
- Registration of Title Act, No. 21 of 1998. Applies only in declared areas and
  nothing in the corpus shows Bandarawela to be one. Not used.
- Land Reform Law s.13. Concerns alienations on or after 29 May 1971 reported
  within three months of commencement; it cannot reach a 2020 transfer.
- Survey Act, No. 17 of 2002 and Surveyors Ordinance. The plan requirement in
  this answer comes from Notaries Ordinance s.31 rule (16)(a), not from them.

## What the verifier should look at first

1. **Temporal risk in Notaries Ordinance s.31.** The corpus carries the
   consolidated text with the 2022 and 2024 amendments, and its
   `amendment_events` are not mapped to individual rules. Rules (16)(a) and
   (20) opening and (17)(a) are relied on as pre-2020 because Act No. 31 of 2022
   s.16(9)-(11) substituted only other parts of them; that reading should be
   checked. Rule (6) is in its 2022 substituted form, so PROV-M062-003 is marked
   `applicable_to_matter_date: false` and kept as supporting only, and claim
   CL-M062-Q01-006 rests partly on it.
2. **Prevention of Frauds Ordinance s.2** (PROV-M062-007) is the 2022/2024 text.
   The substance relied on (notarially attested writing before two witnesses) is
   older, but the October 2020 wording is not in the corpus.
3. **Tea estate extent** (PROV-M062-018). The corpus records two
   `substitute_not_applied` amendment events on 2-1958/s25 from Act No. 20 of
   2005. Confirm the hundred acre floor stood in October 2020, since the whole
   fragmentation limb of the answer turns on it.
4. The rule numbers quoted for s.31 are inferred from position; the corpus body
   drops the numbers for rules (16), (17) and (26).

No claim in the map cites case law, and the ceiling reasoning (s.66 to s.3(1)(b)
to s.8 to s.5(1)) is the chain behind `legal_hop_count: 4`. The validator prints
OK with no warnings.
