# M024 research notes (status=unverified)

Two-year lease of business premises in Galle, Rs 150,000 a month; the lessor
cannot travel to the Colombo notary. Both Tier A questions are `keep`, so no
enrichment was applied.

## Queries tried

- `acts`, then `toc` for 1-1907, 4-1902, 7-1840, 12-2006, 43-1982, 17-1852.
- `show --full` on 7-1840/s2, 1-1907/s31, s32, s4A, s9, 4-1902/s2, s3, s3A,
  s3B, s3C, and 12-2006/s3, s4, s6, s8, s9, s12, s13, s14.
- `grep "lease"` corpus-wide and inside 43-1982; `grep "stamp"` inside 6-1990.
- `check` on all 18 excerpts before writing them into the map.

## Alternatives considered and rejected

- Deeds and Documents (Execution before Public Officers) Ordinance No. 17 of
  1852 s.2 lets a Prevention of Frauds s.2 instrument be executed before a
  District Judge or an authorised Justice of the Peace instead of a notary.
  Left out because the section is tied to the district where the party resides
  and names offices (Commissioner of a Court of Requests) that the corpus text
  still marks with asterisks. Worth a verifier's eye as a third route for Q01.
- Notaries Ordinance s.9 (office within jurisdiction) dropped in favour of
  rule (22) with s.4A, which state the attestation restriction directly.
- Western Province Financial Statute No. 6 of 1990 s.37 charges duty at "the
  prescribed rate" and covers the Western Province; the premises are in Galle.

## Corpus gaps

- No Ministerial Order under 12-2006 s.3(1) fixing the lease rate. That alone
  makes Q02 `blocked_missing_authority`; chargeability, liable party and mode
  of payment are all in the corpus.
- 43-1982 is extracted only to s.71, with no rate schedule.

## For the verifier, in order

1. Whether rule (27)(c)(ii) should be indispensable rather than supporting on
   the split-execution route (s.32(2) with s.31 rule (25)).
2. Whether the power of attorney route belongs in `indispensable` rather than
   `supporting` for Q01, given the question asks "how can" not "must".
3. Seven provision entries share `section_id` `1-1907/s31` (rules 6, 7, 12, 22,
   25, 27, 30); the rule number is carried in `subsection`. Two entries share
   `7-1840/s2` (the lease carve-out and the execution formality). The validator
   reports OK with no warnings.
