# M114 research notes (statutory-qa-v1, status=unverified)

Paper 16 Q8, April 2018. Three Tier A parts, all `keep`, so no enrichment.
Two are drafting exercises and one a computation; none ended `proposed_gold`.

## Queries run

`acts`; `search "lease" -k 25`; `toc` on 12-2006, 7-1840, 1-1907; `show
--full` on 12-2006 s3-s6, s8, s13, s14, 7-1840 s2, 23-1927 s8, 6-1990 s37 and
1-1907 s31; `grep "lease"` on 43-1982, 23-1927; `grep "stamp duty" --act
6-1990`; `grep` for "rate of stamp duty", "every one thousand rupees",
"reddendum", "quiet enjoyment", "habendum", "covenant"; `check` on all ten
excerpts.

## Alternatives rejected

- Stamp Duty Act 43-1982: s.13 of 12-2006 displaces its imposition provisions
  for anything but transfers of immovable property, motor vehicles and court
  documents. Its s.19 and s.24 mention leases but carry no rate.
- Western Province Financial Statute 6-1990: s.37 charges duty on transfers,
  court documents and motor vehicles, not leases, and leaves the rate to be
  prescribed. Logged as a corpus gap, not a provision.
- Land (Restrictions on Alienation) Act 38-2014 Land Lease Tax bites on leases
  to foreigners and the lessee is unidentified; Trusts Ordinance 9-1917 s.38
  and Buddhist Temporalities Ordinance 19-1931 s.29 cap lease terms only for
  trustees.

## Corpus gaps

Full list in `legal-map.json`. Two matter: no Gazette Order under s.3 of Act
12 of 2006 is in the corpus, so the rate and chargeable base for a lease are
unavailable and Q02 is `blocked_missing_authority`; and the corpus holds
nothing on the covenants or rent-reservation clause of a residential lease, so
Q01 and Q03 are `reserved` as `mixed_statute_and_case`.

## For the verifier, in order

1. Whether Q02 stays blocked. With a rate Order from outside the corpus the
   chain (s.4(i), s.3(1), s.6(c), s.8(2)) is complete; the open point is
   whether the Rs. 900,000 advance and Rs. 300,000 deposit are added to the
   Rs. 1,800,000 of rent reserved over twenty-four months.
2. Whether the Western Province charge or the national Act governs a Dehiwala
   house lease in April 2018. The map assumes the national Act.
3. Temporal risk on 7-1840 s.2 and 1-1907 s.31, both consolidated to 2024.
   Neither is indispensable, but check the excerpts against an April 2018 text.
