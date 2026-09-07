# M064 research notes (status=unverified)

Paper 11 q4, October 2020. One Tier A question (M064-Q01, action `enrich`):
a client asks whether the notary attested his father's will.

## Queries

`acts`; `grep "secre|divulge|disclos" --act 1-1907` (hits s.23, s.25, s.31 —
only s.31 rule (1) on point); `grep "divulge"` corpus-wide (other hits are
bank/company/provincial secrecy regimes, not notaries); `search "duty of
secrecy will testator confidential notary"` and `toc 21-1844` (nothing on
confidentiality — Wills and Prevention of Frauds hits are execution
formalities); `show --full` on 1-1907 s.31, s.34, s.21, s.32, s.43;
`edges 1-1907/s31`; `check` on all three excerpts (all verbatim).

## Rejected

- s.31 rules (24), (27) and s.42 (only number and date of a will go into the
  register; a copy of a will may not be destroyed). Show that wills are kept
  confidentially but do not carry the duty; unnecessary for a one-mark answer.
- s.32 does not disapply rule (1). s.43 defines neither "employer" nor
  "secrets", so no definition hop exists. s.39 (fraud) is not engaged.

## Temporal

The `amendment_events` list on 1-1907/s31 is not mapped to individual rules,
so I read 31-2022 s.16 and 47-2011 s.2 and s.3 in full: none touches rule (1),
and the 6-2024 events post-date the matter. Rule (1) is treated as in force
at 2020-10. Section 34 is different — the corpus text is the whole section
substituted by 31-2022 s.17, after the matter date, and the pre-2022 penalty
text is not in the corpus. It is recorded as supporting with
`applicable_to_matter_date: false` and is not relied on for the conclusion.

## For the verifier

1. The load-bearing interpretive step is reading "employer" in rule (1) as the
   testator (the father), not the son who is now asking.
2. Check the `statute_only` call. Attorneys' professional conduct rules are
   outside the corpus; my view is they duplicate rather than displace rule (1).
3. The enrichment keeps the testator alive on purpose. For the harder variant
   (testator dead, heir asking) the corpus has no provision and the question
   would have to be blocked instead.

`validate_legal_map.py M064` prints OK, no errors, no warnings.
