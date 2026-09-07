# M056 research notes (statutory-qa-v1, status=unverified)

Tier A: M056-Q01 and M056-Q04, both `keep`, so no enrichment. Q02/Q03 are Tier B.

Background fact labels: `BG-1` notary practising in Galle; `BG-2` commercial
building in Colombo; `BG-3` 4-year lease at Rs. 60,000 per month; `BG-4` lessor
illiterate; `BG-5` lessor is the notary's neighbour; `BG-6` parties are Sudath
(lessor) and Kapila Warnakulasooriya (lessee); `BG-7` request to insert a lower
amount to save stamp duty (from the Q04 stem).

Queries: `acts`; `toc 1-1907`; `show --full` on 1-1907 ss. 4A, 5, 9, 10, 11, 20,
21, 31, 34, 38, 38A, 39, 43; `toc 7-1840` and `show 7-1840/s2`; `toc 12-2006`
and `show` on ss. 3, 4, 6, 10, 11; `toc 31-2022` with `show` on ss. 11, 16, 17,
18, 19 to date the Notaries amendments; `show 30-2022/s2` and `show 4-2024/s2`
to date the Prevention of Frauds amendments; `edges 1-1907/s38`;
`grep "stamp duty" --act 6-1990`; `check` on every excerpt (all verbatim).

Rejected: Western Province Financial Statute No. 6 of 1990 s.37 charges duty on
instruments relating to a *transfer* of immovable property in the Province; a
lease is not a transfer, so the provincial regime was not relied on for the
Colombo building (worth a second look). Notaries Ordinance s.38A fits Q04 but
was inserted by Act No. 6 of 2024, after the matter date, so it is omitted.
Section 31 rules (12) and (15) belong to Tier B question Q03 on execution.

For the verifier, in order of risk:

1. Temporal drift. The corpus holds consolidated text including the 2022 and
   2024 amendments, all later than the 2021-10 matter date. Every excerpt was
   chosen to sit outside an amended passage and each `temporal_note` names the
   amending section. The two provisions that could not be cleared that way,
   s.31 rule (6) and s.34, carry `applicable_to_matter_date: false` and no claim
   depends on them.
2. Q01 territorial point. The reasoning is that rule (22) limits where the
   notary attests, not where the land lies, with rule (29) as the positive
   indication. That inference is the load-bearing step.
3. "Deed" in s.38 is undefined; s.38 says "any deed" while s.31 mostly says
   "deed or instrument". Applying s.38 to a lease reads the Ordinance as a whole.
4. The Gazette rate Order under s.3 of Act No. 12 of 2006 is not in the corpus,
   so no duty figure is asserted anywhere.

`validate_legal_map.py M056` prints OK, 0 errors, 0 warnings.
