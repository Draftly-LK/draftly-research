# M066 research notes (status=unverified)

Paper 11 q7, OCTOBER 2020. Both questions are Tier A and `keep`, so no
enrichment was applied. `validate_legal_map.py M066` prints OK, no warnings.

## Queries tried

- `acts`; `toc` on 1-1907, 7-1840, 12-2006, 6-1990.
- `show --full` on 7-1840/s2, s16; 1-1907/s31 (25k chars, read in full),
  s37, s38; 12-2006/s3-s6, s13; 6-1990/s37-s40, s48, s51, s52, s76-s78, s106;
  and on 30-2022/s2, 4-2024/s2, 31-2022/s16 to date the consolidated text of
  the two key sections against October 2020.
- `grep "prescribed rate"`, `"per centum"`, `"100,000"`,
  `"three per centum|four per centum"`, `"SECOND SCHEDULE|Form E"`.

## Alternatives rejected

- Stamp Duty (Special Provisions) Act No. 12 of 2006 as the charging Act.
  Its s.4 list has no conveyance of land and s.13 leaves out instruments
  relating to transfers of immovable property. The charge sits in the
  Western Province Financial Statute because the shop is in Kollupitiya.
- Stamp Duty Act No. 43 of 1982 s.2: displaced by s.13 of the 2006 Act, and
  it gives no rate either.
- Land (Restrictions on Alienation) Act No. 38 of 2014 (no foreign
  transferee) and the Registration of Documents Ordinance (registration
  follows the deed rather than forming part of drafting or of the duty).

## Gaps and what the verifier should check first

1. Q02 is blocked only for the missing rate. Add a Western Province stamp duty rate instrument in force in October 2020 and it becomes answerable.
2. The corpus holds only the post-2024 text of 7-1840/s2 and 1-1907/s31.
   Every provision carries a `temporal_note` on which words predate the
   matter; PROV-M066-002 is `applicable_to_matter_date: false` and
   supporting only. Check those notes against the amending Acts.
3. Q01 is reserved as `mixed_statute_and_case`: a drafting answer needs the
   conveyancing precedent, which no statute in the corpus supplies. If
   drafting questions are to be scored on statutory content alone, flip it
   to `proposed_gold` without changing the provision set.
4. 6-1990 s.37 and s.78 carry OCR noise; excerpts are verbatim to the corpus, not to a clean print. Worth a source check.
