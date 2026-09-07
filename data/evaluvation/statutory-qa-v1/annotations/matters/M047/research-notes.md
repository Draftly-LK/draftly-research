# M047 research notes (status=unverified)

Matter: deed of gift, father to son, land bought December 1977 for Rs.250,000/-,
improved for Rs.800,000/-, now worth Rs.6,500,000/-. Reference date 2022-10.

## Queries tried

- `acts` to find the tax statutes: Stamp Duty Act No. 43 of 1982, Stamp Duty
  (Special Provisions) Act No. 12 of 2006, Western Province Financial Statute
  No. 6 of 1990.
- `toc` on all three; `show --full` on 12-2006 ss.3-6, 12-14; 43-1982 ss.2, 15,
  15A, 22, 71; 6-1990 ss.37, 39, 40, 48, 51, 78, 106.
- `defs` on 43-1982 and 6-1990, then a raw dump of the interpretation sections to
  read the definitions of value, Transfer, gift and conveyance.
- `grep "per centum"` and `grep "prescribed rate"` across the whole corpus, to
  see whether any rate is stated anywhere. Nothing but "at the prescribed rate".

## Route taken

12-2006 s.13 excepts instruments relating to the transfer of immovable property
from the displacement of the 1982 Act, so the older valuation machinery still
speaks to a deed of gift of land. Stamp duty on such transfers is a provincial
charge, and the only provincial finance statute in the corpus is the Western
Province one, so the enrichment places the land at Maharagama in the Colombo
District. The pivot is the definition of "value" in 6-1990 s.106 (and the
identical 43-1982 s.71): the donor acquired in December 1977, after 31 March
1977, so paragraph (c) applies and the value is the lower of Rs.250,000/- plus
Rs.800,000/- of later improvements, and Rs.6,500,000/-. Hence Rs.1,050,000/-.

## Alternatives rejected

- Paragraph (b) of the same definition, pegged to a 31 March 1977 open market
  price, is the trap. It does not apply: the purchase was December 1977.
- 43-1982 s.13 (composition of stamp duty) is about court documents and
  compounding arrangements, not the rate on a conveyance.
- 12-2006 s.4 does not list a conveyance or gift of land as a specified
  instrument, so the 2006 Act is not the charging Act here.

## For the verifier, first

1. Q02 is blocked: no rate Order, regulation or schedule under 6-1990 s.37 (or
   43-1982 s.2) exists in the corpus. Confirm before any figure is added.
2. The 6-1990 text is OCR-damaged. Check s.37 (transposed words), s.106 where
   the definition labels for "Transfer" and "value" are lost, and paragraph (c)
   where the first limb marker is missing. 43-1982 s.71 is the clean parallel.
3. The choice of the Western Province is a synthetic decisive fact, not a fact
   from the paper. If that is not acceptable, Q01 becomes blocked too.
4. Whether ss.37, 48, 51 and 106 of the 1990 Statute stood unamended in October
   2022 cannot be confirmed from the corpus; no amendment is indexed.
