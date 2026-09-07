# M003 research notes (status=unverified)

Matter: mortgage of Land Development Ordinance land in Anuradhapura to a
commercial bank for Rs. 10,000,000. Both questions are Tier A and both are
`enrich`. Reference date 2026-04.

## Queries tried

- `acts` to see what stamp duty and land legislation the corpus holds.
- `search "stamp duty payable on mortgage bond"`, then `toc 12-2006`,
  `toc 10-2008`, `show --full` on 12-2006 ss.3, 4, 5, 6, 8, 9, 12, 13, 14.
- `grep "Schedule" --act 43-1982` and
  `grep "for every one thousand|per centum of the amount secured"` across the
  whole corpus, to look for a rate. Both returned nothing.
- `search "mortgage of land held on permit or grant written consent" --act 19-1935`
  and `grep "mortgag" --act 19-1935`, then `show --full` on ss.2, 19, 41A, 43, 46.
- `edges 19-1935/s19` and `edges 19-1935/s43`; `grep "stamp" --act 1-1907`.
- `check` on all 17 candidate excerpts before writing: all verbatim.

## Alternatives rejected

- Stamp Duty Act No. 43 of 1982 as the charging statute. Section 13 of the 2006
  Act displaces its imposition provisions where inconsistent, so s.16 of the
  1982 Act is kept only as supporting authority on the measure of the charge.
- Western Province Financial Statute No. 6 of 1990 (ss.46, 48). It ranked well
  on stamp duty searches but the land is in Anuradhapura, outside that province.
- Mortgage Act No. 6 of 1949. It governs enforcement, not the approval or duty
  questions asked here.

## Corpus gaps

Listed in full in `legal-map.json`. The one that blocks Q01 is the absence of
any Order under s.3 of the 2006 Act fixing the rate; there is no rate schedule
anywhere in the corpus, so the arithmetic on Rs. 10,000,000 cannot be done
without quoting a rate from memory. Q01 is therefore
`blocked_missing_authority`, although the "where do you pay" limb is fully
supported.

## For the verifier first

1. `PROV-M003-009` (Notaries Ordinance s.31): the lettered clauses making the
   notary pay the duty follow rule (7) in the corpus text with no rule number
   of their own. `subsection` is null. Confirm the number against the
   Government Printer text.
2. The paper cites "Land Development Ordinance 27 of 1981". The corpus statute
   is No. 19 of 1935; 27-1981 is only an amending Act. Check whether the
   benchmark should keep the paper's citation.
3. Q02 turns entirely on the grant/permit distinction, which the original
   background does not supply. `FACT-M003-Q02-001` makes Herath a grant holder;
   if a lawyer prefers the permit reading, the answer reverses via s.46.
