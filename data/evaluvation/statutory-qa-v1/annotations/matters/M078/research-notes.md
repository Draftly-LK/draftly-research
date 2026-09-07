# M078 research notes

Paper 12 question 9, APRIL 2020. Tier A annotated: Q01, Q03, Q04. Q02 is
Tier B and untouched. All three are `keep`, so no enrichment.

## Queries tried

- `acts`, then `toc 23-1927`, `toc 12-2006`, `toc 6-1990`.
- `show --full` on 23-1927 sections 6, 7, 8, 14, 15, 26, 27, 30.
- `search "priority of mortgage over lease registration"` returned only the
  statutory charges in the housing and State Mortgage Bank statutes, which
  cover loans by those bodies and not a private lender.
- `search "stamp duty rate mortgage bond every rupees hundred"` and
  `grep "for every one thousand"`: no rate table anywhere in the corpus.
- `grep "stamp" --act 1-1907`, then `show 1-1907/s31 --full`, then `show` on
  47-2011, 31-2022 and 6-2024 to date the section 31 rules against April 2020.
- `check` was run on every excerpt in the map; all passed.

## Alternatives rejected

- Mortgage Act sections 5, 24 and 25 rank mortgage against mortgage in a
  hypothecary action, not mortgage against lease, so they miss Q01.
- Stamp Duty Act No. 43 of 1982: section 13 of Act No. 12 of 2006 displaces it
  where inconsistent for instruments other than transfers of immovable
  property, motor vehicles and court documents, so it was not used here.
- Notaries Ordinance section 31 rules (7A) and (30A) were left out; both were
  inserted by Act No. 31 of 2022 and were not law in April 2020. A verifier
  reading the consolidated corpus text could pick them up by mistake.

## For the verifier, first

1. Q03 is blocked only because the Gazette rate Order under section 3(1) of
   Act No. 12 of 2006 is outside the corpus. Add a rate source and the
   question becomes answerable with no other change.
2. Q01 is answered in the alternative because the scenario never says whether
   the lease was registered or for what term. Consider whether it should be
   `blocked_scenario_ambiguity` instead.
3. Check the reading of Western Province Financial Statute section 37 as not
   charging mortgage bonds; paragraph (a) of the corpus text is garbled.
4. PROV-M078-009 is flagged not applicable to the matter date because the
   corpus carries the 2022 and 2024 text of Prevention of Frauds section 2.
