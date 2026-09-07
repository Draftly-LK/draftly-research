# M017 research notes (statutory-qa-v1, unverified)

Matter: two-year lease of a Colombo house, Rs. 100,000 a month, Rs. 300,000
refundable deposit, Rs. 600,000 advance set off against year one. Three Tier A
parts: stamp duty calculation, first-year monthly rental, five lease covenants.
All three are `keep`, so no enrichment was applied.

## Queries tried

- `acts` to find the stamp duty statutes; both are in the corpus (12-2006 and
  43-1982).
- `toc 12-2006` and `show --full` on s3, s4, s5, s6, s7, s8, s12, s13, s14.
- `toc 43-1982`, `grep "[Ss]chedule" --act 43-1982` (no match),
  `grep "per centum" --act 43-1982`, `show 43-1982/s2`, `s13`, `s18`.
- `search "stamp duty rate on lease rental"`,
  `search "covenants of lease lessee lessor obligations"`.
- `show 7-1840/s2 --full`; `search "registration of instruments affecting land
  priority" --act 23-1927`.
- All six excerpts confirmed with `check`.

## Alternatives rejected

- **43-1982 s.18 and s.19** (periodical payments, indeterminate value) look like
  a way to value the lease consideration, but s.13 of the 2006 Act displaces the
  1982 Act's imposition provisions for a lease, so they were not carried into the
  map.
- **Western Province Financial Statute No. 6 of 1990 s.37** charges provincial
  stamp duty on instruments relating to a *transfer* of immovable property in the
  Western Province. A lease is not such a transfer, and s.37 also leaves the rate
  to be "prescribed", so it adds nothing. Left out.
- **Registration of Documents Ordinance s.7** was considered as support for a
  registration covenant in Q03 but is not needed for any claim made.

## Corpus gaps

The decisive one is the rate. Act No. 12 of 2006 s.3(1) delegates the rate to a
Ministerial Order in the Gazette, and no Order (nor any exemption Order under
s.5) is in the corpus; 43-1982 has no rate Schedule either. Q01 is therefore
`blocked_missing_authority` rather than answered with a figure. Q02 and Q03 are
`reserved`: neither the appropriation of an advance against rent nor the content
of lease covenants is governed by any statute in the corpus.

## For the verifier

Look first at the Q01 base-of-charge reasoning: whether the refundable deposit
and the advance enter the consideration is asserted as open, not decided, and
that framing should be checked. Second, PROV-M017-006 (Prevention of Frauds
s.2) carries 2022 and 2024 amendment events while the instrument is dated 2020
and the reference date is 2025-10; the one-month exclusion relied on is
long-standing, but confirm which text governs. Validator prints OK with no
warnings.
