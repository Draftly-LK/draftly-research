# M070 research notes

Matter: P12-Q02-M01, April 2020. One Tier A question (M070-Q01, `keep`):
"Calculate the stamp duty payable by him on the Mortgage Bond" on a Rs. 3
million bank loan secured over a Ratmalana house.

## Queries tried

- `acts` — two stamp duty statutes in the corpus (43-1982, 12-2006) plus
  amendment 10-2008.
- `toc 12-2006`, `toc 43-1982`; `show --full` on 12-2006 s.3, s.4, s.5, s.6,
  s.8, s.12, s.13, s.14 and 43-1982 s.2, s.16, s.67.
- `grep "mortgage" --act 43-1982` — hits only in s.5, s.15, s.16, s.71; no
  rate for a mortgage anywhere in the 1982 Act.
- `grep "every (one )?thousand rupees|Rs. ?1,?000|per centum of the|rate of
  stamp duty"` across the whole corpus — no stamp duty rate table anywhere.
- `defs 12-2006` (only Assessor, Commissioner-General, Inland Revenue Act);
  `edges 12-2006/s3` and `edges 12-2006/s4`.
- `check` run on all six excerpts; all confirmed verbatim.

## Why the question is blocked

Everything except the number is on the corpus record: s.3(1) charges the duty,
s.4(g) makes a bond or mortgage for a definite and certain sum a specified
instrument, s.6(e) puts it on the person executing, s.13 sends a mortgage to
the 2006 Act rather than the 1982 Act. But s.3(1) delegates the rate to a
Ministerial Order in the Gazette, and no Order or rates schedule is in the
corpus. Producing "Rs. X" would mean quoting a rate from memory, so the
question is `blocked_missing_authority`, not `proposed_gold`. The authority
requirement is still `statute_only` — the missing instrument is subordinate
legislation, not case law.

## Alternatives rejected

- 43-1982 s.2 as the charging provision: displaced for a mortgage by 12-2006
  s.13, and it too says only "at the prescribed rate".
- 43-1982 s.13 (composition of stamp duty): 8.7k characters, none of it
  reaching a bond or mortgage.
- Mortgage Act No. 6 of 1949: relevant to the bond itself but silent on stamp
  duty; not recorded.
- 43-1982 s.16 kept as *supporting* only. It gives the computation base (the
  limited sum secured), but whether it survives 12-2006 s.13 cannot be settled
  from the corpus, so no indispensable step rests on it.

## For the verifier

1. Confirm the corpus really has no Gazette Order under 12-2006 s.3; if one is
   added later this question becomes answerable and should be re-run.
2. Check the s.16 (1982) survival point — that is the one place where I chose
   `supporting` over `indispensable` on a judgement call.
3. `enrichment.applied` is false, as required for a `keep` question.
4. Validator prints OK with 0 errors and 0 warnings.
