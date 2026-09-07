# M032 research notes (status=unverified)

Matter: paper 5, question 2, April 2024. Only Q01 is Tier A (Q02 is Tier B and
was not annotated). Q01 asks what steps a notary retained by an intending
purchaser of a thirty-acre Kurunegala coconut estate with a bungalow should
take. `candidate_action` is `enrich`, so the background was enriched.

## Queries run

- `acts` to see the closed statute list.
- `toc 1-1907`, `show 1-1907/s31 --full`, `show 1-1907/s37 s38 s38A`.
- `toc 23-1927`, `show 23-1927/s7 s14 s30 s42`.
- `show 7-1840/s2 --full`; `show 4-2024/s2`, `show 6-2024/s1 s3`, `toc 6-2024`.
- `search "ceiling on extent of agricultural land which may be owned" --act 1-1972`,
  `show 1-1972/s3`.
- `search "stamp duty payable on deed of transfer of immovable property"`,
  `toc 12-2006`, `show 12-2006/s3`.
- `search "no permit holder or owner shall alienate land granted without written consent"`,
  `show 19-1935/s19`.
- `show 38-2014/s3`, `show 2-1958/s3`, `show 22-1871/s3`.
- `check` on the section 31 and stamp duty excerpts.

## Alternatives rejected

- **Tea and Rubber Estates (Control of Fragmentation) Act, s.3** — kept only as
  background. The consent regime covers tea and rubber, not coconut.
- **Land (Restrictions on Alienation) Act, No. 38 of 2014** — dropped. It bites
  on foreign transferees; the enrichment makes the buyer a citizen, so the Act
  has no work to do and adding it would have inflated the map.
- **Prescription Ordinance, s.3** — dropped. It underpins the practice of
  checking possession and of a thirty-year search, but that practice is not
  itself statutory and no claim needed it.
- **Notaries Ordinance, s.37** (diligence in registering) — dropped as
  duplicative of rule (30A), which sets the actual deadline.
- **Western Province Financial Statute, No. 6 of 1990** — inapplicable;
  Kurunegala is not in the Western Province.

## For the verifier, in order

1. `PROV-M032-020` (s.38A) is marked `applicable_to_matter_date: false`. It was
   inserted by Act No. 6 of 2024 and the corpus carries years, not commencement
   dates, so it could not be confirmed as in force in April 2024. It is
   supporting only, and claim CL-M032-Q01-018 flags the doubt in terms.
2. The same year-only limitation affects the consolidated wording of s.31
   (Act No. 6 of 2024) and of Prevention of Frauds s.2 (Act No. 4 of 2024).
   Every indispensable point relied on predates 2024, but the quoted wording is
   the post-2024 consolidated text. Check whether that is acceptable or whether
   the excerpts should be re-cut from the 2022 text.
3. `authority_requirement` was set to `statute_only`. That is the judgement
   most open to challenge: a full exam answer would also draw on conveyancing
   practice (thirty-year title chain, non-vesting certificate, rates receipts),
   which is not in the corpus. Every claim in the map is nevertheless tied to a
   recorded provision, and the practice points are listed in `corpus_gaps`.
4. Fact `FACT-M032-Q01-004` (the bank mortgage) is the main decisive addition;
   it is what gives the registry search something to find. Confirm it is
   acceptable as a synthetic decisive fact.
5. `validate_legal_map.py M032` prints OK with no errors and no warnings.
