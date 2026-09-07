# M081 research notes (statutory-qa-v1, status=unverified)

Matter: Paper 13 Q3 part (iv), exam session October 2019. Two Tier A items,
both `keep`, so no enrichment was applied. Stamp duty on a Deed of Gift of
Kohuwala land, so the Western Province regime applies.

## Queries run

`acts`; `search "assessor value of property stamp duty"`; `toc 6-1990`;
`toc 12-2006`; `show --full` on 6-1990 s37, s39, s40, s47, s48, s49, s51,
s62, s63, s64, s76, s78, s106 and on 12-2006 s3, s4, s13;
`grep "market value|value of the property|prescribed" --act 6-1990`;
`grep "per centum" --act 6-1990`; `grep "per centum of the value"` (no match);
excerpt checks against `sections.jsonl` for all twelve provisions.

## Alternatives rejected

- Stamp Duty Act No. 43 of 1982: its s.15 and s.38 mirror the provincial
  sections almost word for word, but the question names an Assessor attached
  to the Western Provincial Council, and 12-2006 s.13 carves instruments
  transferring immovable property out of the displaced 1982 regime. Statute
  No. 6 of 1990 was used and 12-2006 s.13 kept only as background.
- Stamp Duty (Special Provisions) Act No. 12 of 2006 as the charging Act: its
  s.4 list of specified instruments contains no conveyance or deed of gift.
- 6-1990 s.48(3) (gift subject to a reservation): no reservation, life
  interest or condition appears in the scenario, so only s.48(1) was used.
- 6-1990 s.39 exemptions: none covers a gift between private individuals.
- Paragraph (b) of the definition of "value" in s.106: it applies to property
  acquired on or before 31 March 1977, and the purchase was March 1978.

## Corpus gaps

Listed in full in `legal-map.json`. The one that decides Q02: s.37 charges
duty "at the prescribed rate" and the rate lives in a Gazette instrument that
is not in the corpus, so the money figure cannot be produced. Q02 is
`blocked_missing_authority` with the chargeable value still recorded.

## For the verifier, in order

1. The `relevant_excerpt` for PROV-M081-003 is 771 characters, over the ~600
   guideline. Paragraph (c) of the definition of "value" cannot be cut without
   losing either the improvements uplift or the "whichever price is the lower"
   rule, so it was kept whole. It verifies as verbatim.
2. Whether the March 1978 purchase price of Rs.120,000 may stand as the
   Assessor's opinion of the open-market price on that date. The statute asks
   for his opinion, not the deed figure; the draft says so but still uses
   Rs.120,000, which is what makes the answer Rs.3,020,000.
3. The corpus text of 6-1990 is a consolidated edition with no amendment
   events and heavy OCR noise ("ofthe", "have: fetched"). Whether ss. 37, 48
   and 106 read the same in October 2019 cannot be confirmed inside the
   corpus.
4. `validate_legal_map.py M081` prints OK with no warnings.
