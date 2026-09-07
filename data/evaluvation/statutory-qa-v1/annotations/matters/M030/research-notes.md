# M030 research notes (status: unverified)

Matter: a foreigner wants to buy land in Sri Lanka for an apartment business;
you act as his Attorney-at-Law and Notary. One Tier A question (M030-Q01, 3
marks, October 2024, `candidate_action: enrich`).

## Queries tried

- `acts`; `toc` on 38-2014, 3-2017, 21-2018, 11-1973.
- `show --full` on 38-2014 ss.2, 3, 4, 5, 5A, 8, 11, 14, 16, 18, 20, 25;
  21-2018 s.2; 11-1973 ss.2, 9, 26.
- `defs 11-1973`, `defs 11-1973 "condominium parcel"`.
- `grep "unlawful|illegal|void"` and `grep "shall not attest"` over 1-1907,
  looking for a notarial duty to refuse a void instrument.
- `check` on all twelve excerpts; all OK.

## Alternatives rejected

- Notaries Ordinance: nothing in this corpus makes it an offence or a breach of
  s.31 to attest an instrument void under another Act, so no provision was
  recorded. The notary limb rests on 38-2014 s.18 and s.4(1) instead.
- 11-1973 s.26 ("condominium parcel") rejected as an excerpt: extraction has
  stripped the term labels and garbled the text ("a parcel intended for
  separate ownership and was with any other specified condominium parcel").
  11-1973 s.9(4) carries the same point cleanly and was used instead.
- 38-2014 ss.6, 7, 13 (Land Lease Tax rates, valuation) dropped once s.5A
  showed no tax is chargeable on a lease executed after 1 January 2016;
  ss.16, 20, 21 read and rejected as not engaged on these facts.

## For the verifier, first

1. The s.25 excerpts (PROV-002, PROV-003) are verbatim but the corpus body has
   lost the term labels. Confirm the mapping to "foreigner", "foreign company",
   "land", "Minister", "transfer" against the printed Act.
2. 38-2014 s.11 (PROV-010) is corrupted in the corpus; confirm the five-year
   mortgage bar and that it runs from execution of the instrument.
3. Consolidated s.3 used for the post-2018 text; 21-2018 s.2 body is truncated.
4. Whether the enrichment should instead have made the client a dual citizen or
   a condominium purchaser; as drafted every exemption is closed off, so the
   answer is a clean "no purchase; lease or local company instead".
