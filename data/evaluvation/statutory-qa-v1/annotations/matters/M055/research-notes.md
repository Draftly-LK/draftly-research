# M055 research notes (status=unverified)

One Tier A question, M055-Q01 (paper 10, q3 part 2, 2 marks, October 2021).

## Queries tried

- `acts` to confirm the Registration of Title Act No. 21 of 1998 is in the
  corpus as `21-1998` (75 sections, principal, edition flagged
  `original_or_unconfirmed_consolidation`).
- `toc 21-1998`, then `show --full` on ss. 4, 5, 14, 15, 16, 20, 28, 32, 33,
  36, 37, 38, 39, 40, 43, 44, 45, 46, 47, 48, 49, 54, 56, 63, 67, 70, 73, 75.
- `edges 21-1998/s46` and `edges 21-1998/s48`: both only point out to the s. 75
  definition of "instrument"; the incoming links are from the Apartment
  Ownership Law and its 2003 amendment, which are irrelevant here.
- `check` on all fourteen excerpts; all confirmed verbatim.

## What the answer turns on

Two halves. The life interest is saved by the express proviso to s. 46. The
gift to two daughters under one deed is caught by s. 46's neighbour s. 48,
which voids an ownership instrument in favour of two or more persons in
common. s. 47 blocks the divided-portion workaround until the parcel is
sub-divided, and s. 36(1) supplies the cure. s. 39 makes all of this go to
validity, not just to registry practice.

## Alternatives rejected

- ss. 14(d), 15 and 16 (registration as co-owners with a Manager) look like an
  escape from s. 48, but they sit in the initial-compilation Part and operate
  on a declaration by the Commissioner of Title Settlement, not on an
  instrument between parties. Kept out of the map; flagged here because
  s. 48's opening words ("Except in accordance with the provisions of this
  Act") invite the argument and the verifier should form a view on it.
- Prevention of Frauds Ordinance s. 2 and the Notaries Ordinance: not cited,
  because s. 43 supplies the form requirement for instruments under this Act
  and s. 73 gives this Act priority.
- s. 63 (Partition Act excluded) and s. 54(1), (3): not on point; s. 54(2) is
  kept only as background on the Act's policy against undivided shares.

## Corpus gaps

- No Registration of Title (Amendment) Act is in the corpus and the principal
  Act carries no `amendment_events`, so the 2021 wording of ss. 36, 46, 47 and
  48 is unconfirmed.
- The s. 67 regulations are absent: the prescribed instrument form and the
  prescribed minimum extent of a land parcel cannot be stated.
- No s. 70 Gazette notice is in the corpus, so whether a two-way sub-division
  of this parcel is registrable is left open in the answer.

## For the verifier, in order

1. The s. 48 point above (initial-compilation co-ownership as a possible
   exception).
2. Whether s. 46's proviso covers a life interest *reserved* by the donor, as
   opposed to one granted to a third party; the map reads it as covering both.
3. The s. 75 excerpt: the corpus body has lost the defined-term labels, so the
   quoted text runs the "instrument" and "interest in land parcel" definitions
   together. The reading is recorded in that provision's `temporal_note`.
4. Whether a 2-mark answer should carry a hop count of 3; the reasoning chain
   is real, but the marks suggest the examiner wanted only ss. 46 and 48.
