# M058 research notes

Matter reference date 2021-10 (OCTOBER 2021 session). Only M058-Q03 is Tier A;
Q01 and Q02 are Tier B and were not annotated.

## Queries tried

- `acts` — found both stamp duty enactments (`12-2006`, `43-1982`) plus the
  Western Province Financial Statute (`6-1990`).
- `toc 12-2006`, `toc 43-1982`, `toc 6-1990`.
- `search "stamp duty mortgage bond rate"`; `grep "every one thousand|for every|per centum" --act 43-1982`.
- `grep "Schedule" --act 6-1990`.
- `show --full` on 12-2006 ss.3, 4, 5, 6, 8, 9, 13; 43-1982 s.16; 6-1990 ss.37,
  39, 51; 6-1949 ss.69-71.

## Alternatives rejected

- **Stamp Duty Act No. 43 of 1982 as the operative charge.** Displaced by
  12-2006 s.13 for mortgages; the carve-out covers only transfers of immovable
  property, motor vehicle transfers and court documents. Section 16 is kept as
  background because it shows the base of assessment.
- **Western Province Financial Statute s.37.** Charges only transfers of
  immovable property, court documents and motor vehicle transfers, so it does
  not reach a mortgage bond even though the land is at Rajagiriya. Kept as a
  supporting provision to record that the provincial route was checked.
- **Mortgage Act ss.69-71.** Section 71 gives a one-fifth staged stamp duty
  rule, but only for the s.69 instrument creating a mortgage by deposit of
  title deeds with an approved credit agency, not for a notarial mortgage bond.
  Not recorded.

## Corpus gaps

The rate is the whole answer to this question and it is not in the corpus:
12-2006 s.3(1) fixes it by Ministerial Order in the Gazette, s.5 does the same
for exemptions, and neither Order is extracted. Schedule A of the 1982 Act is
also absent, as is the National Savings Bank Act, so no bank-specific
concession can be checked. Q03 is therefore `blocked_missing_authority`.

## For the verifier

Check first whether `authority_requirement: statute_only` is the right label
when the missing instrument is subsidiary legislation rather than case law. The
schema has no separate value for that, and `reserved` plus `statute_only` is a
validator error, so `statute_only` with `blocked_missing_authority` was used.
Second, confirm that a mortgage bond is outside List I of the Ninth Schedule
(12-2006 s.9), since that decides whether the Western Province or the
Commissioner-General collects. The validator prints OK with no warnings.
