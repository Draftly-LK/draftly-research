# M046 research notes (statutory-qa-v1, unverified)

Neela Kumari, prospective buyer of a condominium parcel in Colombo, October
2022. One Tier A question, M046-Q01, action `enrich`.

## Queries

- `toc 11-1973` and `grep "value" --act 11-1973` surfaced the share-value
  chain: s.5(1)(h) and (m), s.9(3) and (4), s.11, s.20A, and the s.26
  definitions of "share parcel" and "prospective purchaser".
- `edges 11-1973/s20A` confirmed the s.5 cross-reference and the s.20H link;
  `defs 11-1973` confirmed the defined terms relied on.
- `grep "value of the (condominium|property|parcel|unit)"` and
  `grep "valuer|Valuer"` corpus-wide, looking for a general valuation route.
- `toc 6-1990` and `toc 43-1982` for stamp-duty valuation machinery.
- `check` on all thirteen excerpts; every one came back verbatim.

## Rejected

- Stamp Duty Act No. 43 of 1982 ss.15, 22: same wording as Western Province
  Financial Statute ss.48, 78, but the property is in Colombo. Neither is
  indispensable, because the corpus does not settle which stamp-duty
  instrument governs a 2022 conveyance.
- Land (Restrictions on Alienation) Act No. 38 of 2014 s.13 has a real
  valuation rule, but it applies to alienation to foreigners and nothing
  makes the purchaser one. Enriching her into one would change the question.
- Municipal Councils Ordinance s.235 kept as background only: annual value is
  a rating measure, and inspection as of right belongs to the owner or
  occupier, not a prospective buyer.

## Why blocked

`blocked_scenario_ambiguity`, `authority_requirement: unclear`. "Value" is
either the share value on the registered Condominium Plan, which is statute
only and fully mapped here, or the open market price, for which the corpus
has nothing. The other four parts of the same exam question are all on the
Apartment Ownership Law, favouring the share-value reading, but that is a
call about what was asked, not a fact gap. `block_reason` says exactly what
to drop if a lawyer confirms that reading.

## Verifier, start here

1. The corpus text of s.20A(2) is garbled ("The determine- share parcels
   shall"); s.78(2) carries "before doing SO". Check both against print.
2. Two provisions share section_id 11-1973/s5 and two share 11-1973/s26.
   Intentional, different subsections and definitions, not duplication.
3. Validator prints OK, zero errors, zero warnings.
