# M038 research notes (status=unverified)

One Tier A question, M038-Q01 (`keep`, so no enrichment). Stamp duty on a deed
of gift of land and a house at Kadawatha, exam session October 2023.

## Queries tried

- `acts` to find the stamp duty enactments: 43-1982, 12-2006, 6-1990.
- `toc 12-2006` and `show --full` on ss.1, 3-10, 12-14. Section 13 carves
  instruments relating to the transfer of immovable property out of the 2006
  Act, and s.4 does not list a conveyance as a specified instrument, so the
  2006 Act does not charge this deed.
- `toc 6-1990`, then `show --full` on ss.1, 37-40, 48, 51, 62, 76, 78, 106.
- `defs 6-1990` and `grep "\"value\"" --act 6-1990` to reach the definitions.
- `grep "per centum" --act 6-1990` and `grep "100,000|four per|three per"` to
  look for a rate. No match in either 6-1990 or 43-1982.

## Alternatives rejected

- **Stamp Duty Act No. 43 of 1982** as the operative charge. It survives
  12-2006 s.13 for immovable property, but stamp duty on Western Province land
  transfers is charged by 6-1990 s.37, and 6-1990 s.78(5) treats the two as
  alternatives only for instruments stamped between January and July 1991.
- **Paragraph (b) of the s.106 definition of "value"**. It is confined to
  property acquired on or before 31 March 1977; the donor bought in February
  1980, so paragraph (c) governs.
- **Rs. 5,400,000 as the base.** It is only the second limb of the lower-of
  test in paragraph (c)(ii), and it loses to Rs. 3,500,000.
- Notaries Ordinance provisions on attestation. 6-1990 s.78 covers the
  stamp-duty-specific notarial duties directly and s.78 is the closer fit.

## Corpus gaps

Recorded in `corpus_gaps`. The one that blocks the question: s.37 charges duty
"at the prescribed rate" and no prescribing Order is in the corpus, so the
rupee figure the question asks for cannot be derived. Status is
`blocked_missing_authority`, not `reserved`, because the missing authority is
subsidiary legislation rather than case law; `authority_requirement` stays
`statute_only`.

## For the verifier, in order

1. Is 6-1990 (not 43-1982) the right charging enactment for a 2023 Western
   Province gift? Everything else follows from that.
2. The s.106 "value" arithmetic: Rs. 400,000 + Rs. 3,100,000 = Rs. 3,500,000,
   lower than Rs. 5,400,000. Check that construction cost counts as
   "improvements, alterations and additions".
3. The three s.106 provisions (PROV-002, -004, -005, -012) share one
   `section_id`. The corpus body of s.106 has lost the quoted defined-term
   labels through OCR, so the excerpts start mid-definition ("means a sale
   and shall include..."). Terms were matched using the section's
   `defined_terms` metadata; confirm against the source PDF.
4. Kadawatha being in the Western Province is assumed, not sourced.

Validator: `M038: OK errors=0 warnings=0`.
