# M089 research notes (status=unverified)

Paper 14 Q5, April 2019. Three Tier A parts, all `keep`, so no enrichment.
Subject: a right of way over road reservation Lot R1 after Lot A is subdivided.

## Queries tried

- `acts` — no enactment on servitudes in general; the corpus has no Roman-Dutch
  law text.
- `search "servitude right of way"`, `grep "servitude"` — hits are Apartment
  Ownership Law ss.13-20 (servitudes implied between condominium parcels),
  Land Reform Law ss.9 and 42E, Land Acquisition Act ss.5, 10, 17, 38 (acquiring
  a servitude for a public purpose), Registration of Title Act ss.36 and 68.
  None governs a private right of way over a road reservation between
  neighbours, so all were rejected.
- `grep "right of way"` — only three hits: Municipal Councils Ordinance s.71 and
  s.327, Urban Councils Ordinance s.249. The Municipal Councils Ordinance is the
  one the third part points to.
- `search "street vested in the Council public thoroughfare" --act 29-1947`,
  `toc 29-1947`, `defs 29-1947 street` — gave s.37(1)(b), s.327, s.46, s.50,
  s.65, s.77.
- `search "sub-division of land into building lots approval road reservation"` —
  only State Lands Ordinance ss.55-57 and s.102, which deal with State road
  reservations, not a private one shown on a subdivision plan. Rejected.
- Every excerpt confirmed with `check`; all eight returned OK.

## Corpus gaps

Recorded in `corpus_gaps`. The controlling gap is that the corpus holds no
statement of praedial servitude law, so parts 1 and 2 are `reserved` as
`mixed_statute_and_case`. Prevention of Frauds Ordinance s.2 sits in the corpus
only in its post-2022/2024 consolidated form, so it is flagged
`applicable_to_matter_date: false` and used as supporting or background only.

## For the verifier

1. Part 3 is the only `proposed_gold`. Test whether s.37(1)(b) read with the
   s.327 definition of "street" really carries the public right of way, or
   whether the definition is circular (a road is a street only if the public
   already have a right of way over it). If that reading fails, part 3 should
   drop to `mixed_statute_and_case` and be reserved with the rest.
2. The map assumes Kaduwela is a Municipality under s.2 because the question
   says so; nothing in the corpus confirms it.
3. PROV-M089-002 and PROV-M089-003 are two definitions from the same section
   (s.327), entered as separate provisions.
4. The s.327 "premises" definition is used only as inferential support in parts
   1 and 2; it is an interpretation clause of one Ordinance, not a general rule.
5. Validator prints OK with no warnings.
