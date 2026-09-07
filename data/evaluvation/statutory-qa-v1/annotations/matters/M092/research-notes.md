# M092 research notes

Status: `unverified`. One Tier A question (M092-Q01), `enrich`, reference date
2019-04. Validator reports OK, 0 errors, 0 warnings.

## Queries tried

`acts`; `toc` on 1-1907, 21-1844, 7-1840, 17-1852; `show 1-1907/s31 --full`
(25k chars, read in full for rules 8, 9, 11, 12, 18, 20, 21, 22, 24, 36(c)) and
`show --provisions` to test sub-rule ids; `show` on 7-1840/s4,s5,s9,s11,s14,
21-1844/s2,s9, 1-1907/s3,s4,s4A,s9,s10,s11,s13,s32,s33,s34,s37,s43 and
17-1852/s2; `grep "judicial zone"`; `grep "bedridden|sick|point of death"`.

## Alternatives rejected

- 17-1852/s2 (execution before a District Judge or authorised Justice of the
  Peace) reaches only instruments under Prevention of Frauds Ordinance s.2, not
  wills under s.4. Kept as background so it is visibly considered.
- 7-1840/s14 (soldiers and mariners): no facts engage it. 1-1907/s32: its
  relief from rules (20) and (24) does not cover this pattern. 1-1907/s3, s4,
  s4A fix the warrant area at admission but say nothing about attesting outside
  it; rule (22) and s.11 carry that instead.
- Sub-provision ids such as `1-1907/s31/sub-22` are listed by `--provisions`
  but rejected by `show` and absent from `sections.jsonl`, so every s.31 entry
  uses `1-1907/s31` with the rule number in `subsection`.

## Corpus gaps

Five recorded in `corpus_gaps`. The two that bite: judicial-zone delimitation
(Judicature Act and ministerial orders) is absent, and the corpus holds only
post-2022 text for Prevention of Frauds s.4, Wills Ordinance s.2 and several
s.31 rules.

## For the verifier, in order

1. FACT-M092-Q01-002 carries the result. It asserts Mount Lavinia lies outside
   the area named in a warrant expressed as "Colombo". The corpus neither
   proves nor disproves this; if a Colombo warrant does reach Mount Lavinia,
   the answer collapses to "he may attest at the bedside himself".
2. PROV-M092-002 quotes the 2022 text of s.4(2) including the thumb impression
   but is relied on only for the pre-2022 elements. Check that split.
3. PROV-M092-003 (rule 22) is treated as unamended since 1907 because no
   amendment_event maps to it; the s.31 event list is unordered and unmapped,
   so verify against the 2022 and 2024 amending Acts.
4. PROV-M092-019 and PROV-M092-020 are `applicable_to_matter_date: false` and
   used as background or supporting only.
