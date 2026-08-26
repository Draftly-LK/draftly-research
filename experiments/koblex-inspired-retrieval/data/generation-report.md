# statute.jsonl generation report

Corpus for the KoBLEX-inspired retrieval experiment. Provision-level records built from the finalized structured statute JSON. Statutory evidence only -- no generated, parametric or synthetic provisions.

## Counts

- Source files inspected: 31
- Statutes indexed: 20
- Records: 6031
- Distinct sections referenced: 1146
- Records without a heading: 9
- `section_id` is a rollup key, not a foreign key: it names the section a record belongs to even where that section has no record of its own (a section whose text lives entirely in its children emits nothing). Group by it to score at section level.
- Temporal metadata: none. `effective_from` / `effective_to` are null on every record; act-level `commencement` is deliberately not propagated to provisions.

### By node type

- `paragraph`: 2330
- `subsection`: 2322
- `section`: 487
- `subparagraph`: 397
- `definition`: 183
- `closing_text`: 147
- `proviso`: 103
- `text`: 36
- `item`: 21
- `schedule`: 3
- `schedule_item`: 2

### By Act

- Companies Act: 3557
- Apartment Ownership Law: 557
- National Housing Act: 447
- Survey Act: 310
- Urban Development Authority Act: 242
- Registration of Title Act: 225
- Land (Restrictions on Alienation) Act: 136
- Tea and Rubber Estates (Control of Fragmentation) Act: 109
- Land Grants (Special Provisions) Act: 78
- Registration of Old Deeds and Instruments Ordinance: 74
- Nindagama Lands Act: 72
- Matrimonial Rights and Inheritance Ordinance: 51
- Jaffna Matrimonial Rights and Inheritance Ordinance: 49
- Thesawalamai Pre-emption Ordinance: 39
- Land Registers (Reconstructed Folios) Ordinance: 24
- Kandyan Succession Ordinance: 20
- State Land (Claims) Ordinance: 20
- Wills Ordinance: 9
- Deeds and Documents (Execution before Public Officers) Ordinance: 7
- Muslim Intestate Succession Ordinance: 5

## Skipped

### Files

- `27-2002-apartment-ownership-amendment.json` -- amending Act (no source_id); already folded into the consolidation
- `39-2003-apartment-ownership-amendment.json` -- amending Act (no source_id); already folded into the consolidation
- `4-1999-apartment-ownership-amendment.json` -- amending Act (no source_id); already folded into the consolidation
- `45-1982-apartment-ownership-amendment.json` -- amending Act (no source_id); already folded into the consolidation
- `11-1973-apartment-ownership-law.json` -- superseded edition (kept 'consolidated')
- `20-2005-tea-and-rubber-estates-control-of-fragmentation-amendment.json` -- amending Act (no source_id); already folded into the consolidation
- `29-2022-wills-ordinance-amendment.json` -- amending Act (no source_id); already folded into the consolidation
- `5-1993-wills-ordinance-amendment.json` -- amending Act (no source_id); already folded into the consolidation
- `21-1844-wills-ordinance-consolidated.json` -- superseded edition (kept 'consolidated-2024')
- `21-2018-land-restrictions-on-alienation-amendment.json` -- amending Act (no source_id); already folded into the consolidation
- `3-2017-land-restrictions-on-alienation-amendment.json` -- amending Act (no source_id); already folded into the consolidation

### Nodes

- Empty own-text (content lives in children): 667 (definition 1, schedule 1, section 659, subsection 6)
- Repealed stubs excluded: 3
  - `11-1973/section-26/closing_text-1` -- '(*Repealed and replaced by the Companies Act, No. 17 of 1982.)'
  - `21-1844/section-3` -- 'Repealed By'
  - `21-1844/section-4` -- 'Repealed By'
- `inserted_provision` / `substituted_provision` encountered: 0 (unwrapped 0, skipped as empty 0)

## Consolidation gaps

Reported, not resolved -- this build does no historical version reconstruction.

- **Apartment Ownership Law** -- verification_status is 'unverified'
- **Survey Act** -- edition kind is 'original_or_unconfirmed_consolidation', not a confirmed consolidation
- **Tea and Rubber Estates (Control of Fragmentation) Act** -- edition kind is 'as enacted (Numbered Acts database)', not a confirmed consolidation; 1 amending Act(s) present (20-2005-tea-and-rubber-estates-control-of-fragmentation-amendment.json) so their changes may be absent
- **Wills Ordinance** -- verification_status is 'unverified'
- **Registration of Title Act** -- edition kind is 'original_or_unconfirmed_consolidation', not a confirmed consolidation
- **Registration of Old Deeds and Instruments Ordinance** -- verification_status is 'needs_structural_review'
- **National Housing Act** -- verification_status is 'unverified'
- **Urban Development Authority Act** -- verification_status is 'unverified'
- **Jaffna Matrimonial Rights and Inheritance Ordinance** -- act_id '1-1911' from citation differs from directory prefix '58-1947'

## Problems

- No parsing failures.
- Duplicate node paths disambiguated: 18. These are source-side labelling defects, not build artefacts -- sibling provisions carrying the same label. Both records are kept, the later one suffixed `-2`, so no provision is silently dropped. Spot-checked examples: Apartment Ownership s.20C(2) genuinely has two `paragraph (bb)` siblings with different text; Companies Act s.529(1) has several definitions collapsed under one `definition:distribution` node, so its `(a)`/`(b)` paragraphs repeat. Affected paths:
  - `11-1973/section-20c/subsection-2/paragraph-bb`
  - `17-2002/section-45/subsection-1/paragraph-c`
  - `38-2014/section-2/subsection-2/paragraph-b/subparagraph-i`
  - `38-2014/section-2/subsection-2/paragraph-b/subparagraph-ii`
  - `41-1978/section-28a/subsection-3/paragraph-a`
  - `41-1978/section-28a/subsection-3/paragraph-b`
  - `41-1978/section-4/subsection-1`
  - `7-2007/section-431/subsection-2/paragraph-c`
  - `7-2007/section-529/subsection-1/definition-distribution/paragraph-a`
  - `7-2007/section-529/subsection-1/definition-distribution/paragraph-b`
  - `7-2007/section-529/subsection-1/definition-group-financial-statements/paragraph-a`
  - `7-2007/section-529/subsection-1/definition-group-financial-statements/paragraph-b`
  - `7-2007/section-529/subsection-1/definition-share-register/paragraph-a`
  - `7-2007/section-529/subsection-1/definition-share-register/paragraph-b`
- Duplicate evidence texts: 117 distinct strings appear more than once (340 records)
- Schedule items carrying `rates` tables: 2. The band/rupees/cents tables are structured numeric data and are not flattened into `text`, so rate lookups will not retrieve them.

## Regeneration

```powershell
uv run python experiments/koblex-inspired-retrieval/build_statute_corpus.py
uv run pytest tests/test_koblex_statute_corpus.py -q
```
