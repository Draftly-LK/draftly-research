# M098 research notes (statutory-qa-v1, status=unverified)

Tier A: M098-Q02 (correction procedure) and M098-Q03 (stamp duty on the deed).
Q01, Q04 and Q05 are Tier B and were not annotated.

## Queries run

- `acts` to see what is in scope; `toc 23-1927` and `grep "error" --act 23-1927`
  landed on s.35 "Correction of errors" straight away.
- `show --full` on 23-1927 ss.2, 13-14, 35-39, 49-50; `edges 23-1927/s35`.
- `toc` on every Registration of Documents amendment in the corpus (22-1958,
  27-1969, 19-1976, 50-1982, 5-1990, 21-2013, 32-2022, 18-2024) to date s.35.
- `toc 12-2006`, `toc 43-1982`, `toc 6-1990`; `search "rate of stamp duty on
  transfer of immovable property prescribed rate"`; `grep "per centum"` in both
  6-1990 and 43-1982.
- `check` on all 18 excerpts; all returned verbatim.

## Alternatives rejected

- s.39 (District Court cancellation or rectification) - that is for forgery,
  registration without authority or contravention, and needs a court. The facts
  are a registering officer's folio error, which s.35 handles administratively.
- s.38 appeal against refusal - kept as background only. It answers the refusal
  of the lease, not the underlying folio error.
- s.13(5A)/(5B), inserted by Act No. 50 of 1982, is an appeal against refusal
  for a defective description of the land, not for a mis-folioed registration.
- Stamp Duty (Special Provisions) Act No. 12 of 2006 as the charging act for
  Q03 - rejected: s.13 carves transfers of immovable property out, and s.4 does
  not list them as specified instruments.

## Corpus gaps and flags for the verifier

- Q03 is blocked. Both s.37 of the Western Province statute and s.2 of the 1982
  Act charge duty "at the prescribed rate" and no rate order is in the corpus,
  so the rupee figure cannot be produced without inventing a rate.
- Check first: whether the Commissioner of Revenue's "opinion of valuation"
  counts as the Assessor's opinion under the s.106 definition of "value" - the
  definition names the Assessor, the facts name the Commissioner.
- Also check: commencement of the stamp duty Part of the 1990 statute (s.1
  leaves it to Ministerial Order, which is not in the corpus).
- The 6-1990 corpus text is OCR-damaged in places (s.37 word order, "ofRevenue").
  Excerpts are verbatim against the corpus, not against a clean print edition.
- s.14(1)'s excerpt contains a stray "1974]" marker from the consolidated source.
