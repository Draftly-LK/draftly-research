# M051 research notes (status=unverified)

Gift of a Pannipitiya property: stamp duty valuation (Q01) and calculation
(Q02). Reference date 2021-10.

## Queries tried

- `acts` gave three stamp-duty candidates: 43-1982, 12-2006, 6-1990.
- `toc 6-1990`; the stamp duty Part runs from s 37 to s 78.
- `show --full` on 6-1990 ss 37, 39, 40, 48, 49, 51, 62, 63, 64, 76, 77, 78, 106
  and on 12-2006 ss 3, 4, 13.
- `grep "per centum" --act 6-1990`, `grep "prescribed rate"`, `grep "market
  value"`: no rate and no valuation method anywhere in the corpus.

## Alternatives rejected

- Stamp Duty (Special Provisions) Act 12-2006: s 4 does not list a conveyance or
  gift of land, and s 13 carves out instruments relating to transfers of
  immovable property. Kept as background only, to show why 6-1990 governs.
- Stamp Duty Act 43-1982: same charging shape, but the provincial statute is the
  one that applies to Pannipitiya land in 2021. Not recorded.
- 6-1990 ss 64 and 79 are downstream of the determination. Section 48(2) and (3)
  are mentioned in the Q01 draft as the position had there been a reservation,
  but not recorded, since the facts show none.

## Corpus gaps

1. No rate. Section 37 charges duty "at the prescribed rate" and s 77(1)(a)
   leaves it to Gazette regulations; no Western Province rate Order is in the
   corpus, so Q02 is `blocked_missing_authority`. The chargeable value
   (Rs.1,060,000) and the mode of calculation are settled; only the percentage
   is missing.
2. No valuation methodology; s 106 fixes only the test, not the technique.

## For the verifier, first

- Section 106 is OCR-degraded and the head-words of the definitions of
  "transfer", "gift" and "Assessor" are missing, so those excerpts read as bare
  "means ..." clauses. The head-words were inferred from alphabetical position
  and from how ss 37, 48 and 51 use the terms. Check all three against print.
- The excerpt for "value" paragraph (c) runs to about 800 characters, over the
  ~600 guide, because "whichever price is the lower" cannot be split off.
- Confirm that the January 1978 acquisition puts this in paragraph (c) and not
  paragraph (b): the whole Rs.1,060,000 figure turns on it.
