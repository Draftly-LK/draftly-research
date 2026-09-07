# M014 research notes (status=unverified)

Matter: Sarath buys a portion of a coconut estate in Kurunegala; the notary is
licensed for Colombo. One Tier A question (M014-Q01, `enrich`, 5 marks).

## Queries tried

- `acts`, then `toc 1-1907` and `show 1-1907/s31 --provisions` to map the
  notarial rules; `show --full` on s.31 and text slicing to read rules (6),
  (9), (16), (17), (22) and (29), because sub-provision ids such as
  `1-1907/s31/sub-17/par-a` are not addressable by `show`.
- `grep "coconut"` — this is what turned up Act No. 20 of 2005, which renames
  and extends the Tea and Rubber Estates (Control of Fragmentation) Act to
  coconut estates. Without that grep the fragmentation point is invisible,
  since the corpus stores Act No. 2 of 1958 as enacted.
- `search` on the ceiling and on stamp duty; `toc 23-1927` for the
  registration chain.

## Alternatives rejected

- Survey Act No. 17 of 2002: s.12 and s.13 concern deposit of plans and their
  admissibility in court, not a duty to survey before a conveyance. The survey
  step is carried instead by Notaries Ordinance s.31 rule (16)(b) and
  Registration of Documents Ordinance s.13(2) and (5).
- Land (Restrictions on Alienation) Act No. 38 of 2014: only bites on foreign
  transferees, so it was excluded by making the purchaser a citizen
  (FACT-M014-Q01-001) rather than by citing it.
- Notaries Ordinance s.37 (diligence in registering) and s.4A: post-execution
  or appointment matters, outside "before drafting".

## For the verifier, in order

1. The fragmentation point is the load-bearing one and depends on reading
   2-1958 s.3(1) and s.25 through 20-2005 s.3(1)(c). Check that reading first.
   The four hectare and registration limbs of the coconut estate definition
   point to the Coconut Development Act No. 46 of 1971, which is not in the
   corpus (see `corpus_gaps`).
2. Whether Notaries Ordinance s.31 rule (22) limits the notary by the place of
   attestation only, as the answer states, or is read more widely.
3. Whether the land reform ceiling check (provisions 24 and 25) belongs in a
   five mark answer at all; it is labelled supporting, not indispensable.
4. Enrichment adds three decisive facts (estate size and registration, absence
   of a plan, execution in Colombo). Each is flagged with its counterfactual.

Validator: `validate_legal_map.py M014` prints OK with no errors and no
warnings.
