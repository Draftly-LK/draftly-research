# M061 research notes (status=unverified)

Matter: Paper 11 Q1, October 2020. Two Tier A questions, both `keep`, both
`statute_only` and `proposed_gold`. Validator prints OK with no warnings.

## Queries run

- `acts` to see what succession statutes exist in the frozen corpus.
- `toc 15-1876`, then `show --full` on ss.2, 3, 20-36 of the Matrimonial
  Rights and Inheritance Ordinance.
- `search "intestate succession surviving spouse children shares"`,
  `search "deed of gift donee absolute irrevocable"`.
- `grep "life interest"`, `grep "usufruct"`.
- `edges 15-1876/s25` returned nothing in either direction, so the graph gives
  no help here; the links in `reasoning_edges` are read off the section text.
- `check` on all twelve excerpts: all verbatim.

## Alternatives rejected

- s.27 and s.28 (divided half-blood shares): not reached, because Neesha's
  only collaterals were half-siblings on the father's side, which s.29 covers.
- s.32, s.33, s.34: no failure of heirs, no illegitimacy, no escheat.
- Kandyan Succession Ordinance 23-1917 and Muslim Intestate Succession
  Ordinance 10-1931: excluded by the assumption recorded below.
- Revocation of Irrevocable Deeds of Gift Act 5-2017: post-dates the deed and
  no ingratitude is alleged.

## Corpus gaps and things for the verifier to check first

1. Arithmetic. Dinesh 2009: Lochana 1/2, four children 1/8 each. Neesha 2012:
   Rohan 1/16, three paternal half-siblings 1/48 each. Kasun 2015 (holding
   7/48): Lochana 7/96, Kavindu and Piyumi 7/192 each. Result 110/192, 35/192,
   35/192, 12/192, summing to 1. Check the order of deaths: Nimali (2010) died
   after Dinesh (2009), so both of Neesha's parents were dead by 2012.
2. Personal law. The background says nothing about it. The answer states the
   assumption that the general law applies. If the family were Kandyan the map
   is wrong end to end.
3. The s.29 proviso. No fact about Neesha's maternal grandparents. If one was
   alive on 20 May 2012 her half-siblings take only half of the collateral
   portion and every share below changes.
4. The deed of gift step is treated as a fact from the instrument, not as a
   legal claim. The corpus has no provision on a reserved life interest, and
   s.36 sends that question back to Roman-Dutch law, which is out of scope.
5. The corpus text of s.26 reads "balf-blood"; the excerpt keeps the scan
   artefact so it matches verbatim.
