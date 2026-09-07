# M026 research notes (status: unverified)

Paper 4, question 2(3), October 2024. One Tier A question, M026-Q01, `enrich`:
documents to call for on an examination of title, company purchaser, ten
perches with an office building in Colombo.

## Queries tried

Searches on title examination and on registry extracts led to Registration of
Documents Ordinance ss.7, 11, 14 and 42 and to Registration of Title Act
ss.34-37; `toc 23-1927` was used to pick those sections rather than trusting
hit order. Act-scoped searches covered the Companies Act (incorporation, major
transactions, charges), the Western Province Financial Statute (stamp
admissibility), the Urban Development Authority Law (permits) and the
Municipal Councils Ordinance (street lines, certificate of conformity, charges
on premises). All 22 provisions were read with `show --full` before quoting.

## Rejected

Stamp Duty Act No. 43 of 1982 and Act No. 12 of 2006, in favour of the Western
Province Financial Statute s.60, the land being in Colombo. Apartment
Ownership Law: the scenario is a whole building on ten perches, not a
condominium parcel. Registration of Title Act ss.1 and 37 kept as background
only, because an added fact puts the land on a deeds folio.

## For the verifier

1. `statute_only` is the weak point. The thirty-year look-back is a practice
   convention with no source in the corpus, so search depth is grounded on
   Prescription Ordinance s.3 and on registration priority instead. If the
   verifier treats the thirty-year rule as indispensable, the question becomes
   `mixed_statute_and_case`.
2. Prevention of Frauds Ordinance s.2 appears twice (s.2(1)(a) and the
   corporate-transferee proviso in s.2(2)(a)). Both quote the text as amended
   in 2022 and 2024; the commencement date of Act No. 4 of 2024 against the
   matter date is unconfirmed, and the 1986 and 1994 deeds were executed under
   earlier text. Powers of Attorney Ordinance s.3 was substituted in 2022 and
   the same caveat applies to the 1994 deed.
3. Eleven added facts, all pending. FACT-001 (corporate seller), FACT-007 (35
   per cent foreign shareholding) and FACT-008 (price above half the company's
   assets) carry the Companies Act and Land (Restrictions on Alienation) Act
   limbs; rejecting any of them removes that limb.
4. OCR noise: Registration of Documents Ordinance s.11 reads "Us pendens" and
   Municipal Councils Ordinance s.152(2) reads "co-equality" and "(I)".
   Excerpts avoid both while staying verbatim.

`validate_legal_map.py M026` prints OK, no errors, no warnings.
