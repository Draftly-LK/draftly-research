# M034 research notes (statutory-qa-v1, status=unverified)

Gift of business premises at Assessment No.78, Maradana Road, Borella. Tier A:
M034-Q01 (acceptance clause), M034-Q02 (stamp duty). Q03 is Tier B, not annotated.

Queries: `acts`; `toc` on 12-2006, 43-1982, 6-1990; `search "acceptance of gift
by donee deed of gift"`; `grep` on donee, accept, "per centum", "prescribed
rate"; `show --full` on 12-2006 ss.3-10/13/14, 6-1990 ss.37-40/48/51/76-78/106,
43-1982 ss.2/15, 1-1907 s.31, 7-1840 s.2, 31-2022 s.16, 6-2024 s.3. All 13
excerpts confirmed with `check`.

## Route chosen, alternatives rejected

The deed is charged under the Western Province Financial Statute No. 6 of 1990,
not the 2006 or 1982 stamp duty Acts: 12-2006 s.4 does not list a conveyance of
immovable property as a specified instrument, s.13 carves such instruments out
of the displacement of the 1982 Act, and s.9 sends provincial stamp duty to the
Provincial Council; 6-1990 s.37 charges duty on instruments transferring
immovable property in the Western Province, with "Transfer" defined in s.106 to
include a gift. 43-1982 ss.15 and 71 carry near-identical valuation and "value"
wording and were rejected as the operative charge, not as saying anything else.
Q02 turns on the s.106 definition of "value": for gifted immovable property the
base is acquisition-date open market price plus improvements, or present open
market price, whichever is lower. The Rs.100,000,000 figure is a distractor.

## Corpus gaps

1. No prescribed rate. s.37 charges duty "at the prescribed rate", s.77 leaves
   rates to regulations, and no rate order or schedule is in the corpus (43-1982
   s.2 has the same gap). Q02 is `blocked_missing_authority`.
2. No statutory rule on acceptance of a donation; that is Roman-Dutch common law
   and practice. Q01 is `mixed_statute_and_case` and `reserved`.

## For the verifier, in order

1. Whether a Western Province rate order exists in `data/legal-sources/` but was
   never extracted into `corpus/sections.jsonl`. If so, Q02 becomes gold.
2. "In 1977" does not fix whether paragraph (b) or (c) of "value" applies; both
   give the same comparison, hence no `blocked_scenario_ambiguity`.
3. Rs.100,000 is the purchase price; the statute uses the Assessor's opinion of
   open market value. The draft treats it as a proxy and says so.
4. 6-1990 records no amendment events since 1990, which is unlikely.
5. PROV-M034-011 sits on Prevention of Frauds Ordinance s.2, amended in 2024
   (year-level dating only), so its force in April 2024 is unconfirmed; it is
   supporting, not indispensable.
