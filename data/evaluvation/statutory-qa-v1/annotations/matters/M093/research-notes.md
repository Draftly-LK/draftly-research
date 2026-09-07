# M093 research notes (status=unverified)

One Tier A question (M093-Q01, 5 marks, April 2019), classified `enrich`:
a Colombo notary asked to attest a deed for the purchase of a portion of a
rubber estate in Ratnapura.

## Queries

`acts`; `toc 2-1958` then `show --full` on s 3, 4, 8, 9, 11, 14, 23A, 25;
`toc 1-1907` and `show --full 1-1907/s31` (25,684 chars, read in one pass);
`toc 23-1927` with `show --full` on s 2, 7, 13, 14, 29, 30, 42;
`search "licensed surveyor survey plan of land"` (Survey Act s 13);
`search "ceiling on the extent of agricultural land" --act 1-1972`;
`grep "search or cause to be searched"`; `check` on the longest excerpt.

## Rejected

- 2-1958 s 4 and s 6 (partition): this is a sale by one owner.
- Notaries Ordinance s 31 rule (6) (stamp duty assurance): substituted by Act
  No. 31 of 2022 s 16(4), so the corpus wording postdates the matter. Stamp
  duty is carried instead by 12-2006 s 3 and s 6.
- Rules (27) to (30A) and s 37: duties after attestation, not before drafting.
- Registration of Title Act No. 21 of 1998: no fact puts the land in a
  declared title registration area.

## Corpus gaps

Full list in `legal-map.json`. The two that bite: the Rubber Control Act is
absent, so the registration limb of the s 25 definition of "rubber estate"
cannot be checked against text; and the corpus Notaries Ordinance is a
consolidation carrying the 2022 and 2024 amendments, with no as-at-2019
edition.

## For the verifier, first

1. The temporal reconstruction of s 31. Rules (16)(a), (16)(b), (17)(a), (22)
   and (33) are quoted from the post-2024 body. Act No. 31 of 2022 s 16(10)
   repeals only para (b) of rule (17) and adds (c) to (e); s 16(9) touches
   only the tail of (16)(a) and the proviso to (16)(b). The whole
   `applicable_to_matter_date: true` set rests on those mappings.
2. Whether `statute_only` holds. How far back title should be traced is
   practice, not statute; the answer says so rather than asserting a period.
3. Whether 212 acres and registered status is a fair enrichment, given the
   original says only "a Rubber Estate".
4. The s 25 excerpts read as bare "means ..." clauses because the corpus body
   lists defined terms separately. Confirm the term each attaches to.

`validate_legal_map.py M093` prints OK, no errors, no warnings.
