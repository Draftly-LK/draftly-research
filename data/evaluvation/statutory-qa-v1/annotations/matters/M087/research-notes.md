# M087 research notes

Status: `unverified` proposed gold. Not lawyer validated.

## Queries tried

- `acts` to scope the corpus, then `toc 15-1876` and `show --full` on
  Matrimonial Rights and Inheritance Ordinance ss.2, 3, 5, 6, 8, 11, 12,
  20 to 32, 35, 36.
- `search "administrator conveyance to heirs of intestate estate"`,
  `grep "conveyance" --act 2-1889`,
  `search "executor administrator sell immovable property leave of court"`.
- `search "minor guardian consent to deed"`,
  `grep "age of majority|majority"`, `grep "Married Women"`.
- `search "subdivision of land approval local authority"`,
  `grep "sub-division|subdivision" --act 29-1947` (no match) and `--act 41-1978`.
- `edges` on 15-1876/s22 and s25 returned nothing; `defs 15-1876` shows only
  s.3 definitions, none of which the answer turns on.

## Alternatives rejected

- s.27 (half-blood split between the father's side and the mother's side) does
  not govern Amali Perera's estate: she left no full sibling and all her
  half-siblings are on the mother's side, which is the case s.29 addresses.
- s.32 and s.34 (spouse taking everything, escheat) do not arise; collaterals
  survive.
- s.35 (collation) was considered because Lot 1 was gifted to one child in
  2005, but Lot 1 was gifted subject to a life interest and left the estate,
  and the question asks for the pedigree and present shares, not for an
  adjustment between children. Flagged for the verifier rather than used.
- Registration of Documents Ordinance s.10 (will defeated by conveyance by an
  heir) was read and rejected: no will and no competing disposition here.

## What the verifier should look at first

1. The arithmetic: Kamal 1/2, three children 1/6 each; Amali's 1/6 splits
   1/12 to Anura and 1/24 each to Anusha and Anuk; plus Kamal's gift of 1/4
   each. Totals 11/24, 11/24, 2/24.
2. Two stated assumptions the scenario does not supply: the general law
   applies (s.2), and no ascendant of Amali on her father's side survived her
   (s.29 proviso). Both are load-bearing for Q01 and Q03.
3. The scope of "the property" in Q03. The answer is given for Lots 2 and 3.
   "In 2013 she sold this property" has an ambiguous subject; the conclusion
   states the alternative outcome for Lot 1.
4. Matrimonial Rights and Inheritance Ordinance s.8 in the corpus still
   carries the husband's-consent requirement with no amendment history. If the
   Married Women's Property Ordinance No. 18 of 1923 removed it, PROV-M087-016
   should be dropped rather than merely flagged.
5. Q02 is reserved, not blocked on facts. If the verifier holds a source for
   the age of majority or for acceptance by a minor donee, Q02 could become
   answerable.

Validator: `validate_legal_map.py M087` prints OK with no warnings.
