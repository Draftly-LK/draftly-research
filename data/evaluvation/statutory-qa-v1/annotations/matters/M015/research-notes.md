# M015 research notes (statutory-qa-v1)

Status: `unverified`. One Tier A question (M015-Q01), `proposed_gold`,
`statute_only`, 14 provisions, hop count 3. Validator prints OK with no warnings.

## Queries tried

- `acts` — located the Registration of Documents Ordinance (23-1927) and its
  six amendment Acts in the corpus.
- `grep "caveat"` — returned 23-1927 ss.32, 33, 34, 43, 44; 32-2022 ss.2, 3, 5;
  21-2013 s.5; and 2-1889 s.536 (testamentary caveat, a different institution).
- `show 23-1927/s32 --full`, `show 32-2022/s2 --full`, `show 32-2022/s3 --full`,
  `show 32-2022/s5 --full`, `toc 23-1927`, `toc 32-2022`, `toc 18-2024`.
- `show 23-1927/s3`, `s6`, `s8`, `s25`, `s26`, `s33`; `show 4-1902/s3`;
  `show 21-2013/s5`.
- `edges 23-1927/s32` returned nothing in either direction, and `defs 23-1927`
  returned nothing, so the amendment and definition links were traced by hand
  from the section bodies.

## Alternatives rejected

- Civil Procedure Code s.536 ("Who may file caveat") is about caveats against a
  testamentary petition, not a caveat over land. Out of scope for the question,
  which names the Registration of Documents Ordinance.
- Registration of Title Act No. 21 of 1998 has its own caveat machinery, but the
  question is confined to the Ordinance and nothing suggests the Battaramulla
  land is on a title register, so it was not used.
- Act No. 18 of 2024 amends the Ordinance but leaves s.32 alone; noted for the
  temporal check and otherwise not recorded.
- The fee item in Act No. 21 of 2013 s.5 was left out: it goes to cost, not to
  who may file.

## Corpus gaps

Recorded in `corpus_gaps`. The important one: the corpus carries the 1990
consolidation of the Ordinance, so s.32(1), (3), (4) and (5) are pre-2022 text.
Every operative statement about the current s.32 in this map is cited to the
amending section in Act No. 32 of 2022 rather than to a consolidated section.

## For the verifier, in order

1. Check that reading amended text off the amending Act is acceptable here, and
   that PROV-M015-001 is correctly marked `applicable_to_matter_date: false`
   while still being cited (as background contrast) by CL-M015-Q01-002 and -016.
2. Confirm the commencement of Act No. 32 of 2022. Its s.1 in the corpus gives
   only the short title, so "in force at 2025-10" rests on the enactment year.
3. Test whether s.32(1)(b)(i) and (b)(iv) really are indispensable rather than
   supporting. They were treated as indispensable because the question asks
   whether Romani *can* file, and departure abroad makes the Sri Lanka address
   requirement the operative condition.
4. Review the five added facts. FACT-M015-Q01-001 (sole ownership under a
   registered deed) and -003 (Sri Lanka address for service) are the two marked
   `synthetic_decisive`; the rest only make the scenario determinate.
5. The extended definition of "caveator" in s.32(1)(c)(i) is drafted as
   "includes". The answer treats the list as illustrative, not exhaustive.
