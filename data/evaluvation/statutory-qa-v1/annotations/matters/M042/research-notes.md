# M042 research notes (status=unverified)

Matter: lease of a shop at Depanama, Rs.50,000 monthly rent; three Tier A parts.
Reference date 2023-04.

## Queries run

- `acts` to get the closed Act list.
- `toc 1-1907`, `show 1-1907/s31 --full`, `show 1-1907/s38`, `show 1-1907/s33`.
- `toc 7-1840`, `show 7-1840/s2 --full`, `show 7-1840/s16`, `show 7-1840/s19`.
- `toc 12-2006`, `show` on s3, s4, s5, s6, s7, s8, s9, s13, s14.
- `toc 43-1982`, `grep "lease" --act 43-1982`, `grep "mortgage" --act 12-2006`.
- `search "contents of deed of lease parties recitals covenants" -k 12`.
- `show 6-2024/s3`, `show 4-2024/s2` to date the post-2023 changes.
- `check` on all 13 excerpts; all returned OK.

## Alternatives rejected

- Stamp Duty Act, No. 43 of 1982 as the source of a rate. Section 13 of the
  2006 Act leaves its imposition provisions without operation so far as
  inconsistent, and the preserved exceptions (transfers of immovable property,
  motor vehicle transfers, court documents) cover neither a lease nor a
  mortgage bond. The 1982 Act's rate Schedule is not in the corpus either.
- Notaries Ordinance s.31 rules (20) and (21) on the attestation. The question
  excludes the attestation, so they were left out.
- Registration of Documents Ordinance. Registration is downstream of drafting
  and none of the three parts asks about it.

## Corpus gaps

1. No rate Order under s.3 of Act No. 12 of 2006 and no exemption Order under
   s.5. Both Q02 and Q03 ask for a rupee figure that only those Gazette Orders
   can supply, so both are `blocked_missing_authority`.
2. Nothing in the corpus divides a deed of lease into parts or states what each
   part must contain; that is Roman-Dutch letting and hiring plus conveyancing
   precedent. Q01 is `mixed_statute_and_case` and `reserved`.
3. The Notaries Ordinance Schedules (Form E, Forms F and F1) are not extracted.

## For the verifier

- Check the temporal calls first. The corpus bodies of 1-1907/s31 and 7-1840/s2
  are consolidated to 2024. Every excerpt was picked from a passage traced back
  to 2022 or earlier, but the surrounding text is not the April 2023 text.
- Check whether treating rule (17)(a) as supporting rather than indispensable
  for Q01 is right, given the question excludes the schedule.
- Check the Q02 chargeable base. Nothing in the corpus says duty on a lease is
  charged on the rent for the whole term; that is an assumption behind
  `FACT-M042-Q02-001` and should be confirmed against the missing rate Order
  before the figure is ever filled in.
