# M016 research notes (statutory-qa-v1, unverified)

Matter: caveat under the Registration of Documents Ordinance; one Tier A
question (M016-Q01), reference date 2025-10.

## Queries tried

- `acts` to see which land-registration statutes are in the corpus.
- `grep "caveat"` across the whole corpus. Ten hits: Civil Procedure Code s 536
  (testamentary caveat, not this one), Registration of Documents Ordinance
  ss 32, 33, 34, 43, 44, and Registration of Documents (Amendment) Acts
  No. 21 of 2013 (fees) and No. 32 of 2022 (ss 2, 3, 5).
- `show 23-1927/s32 --full`, `show 32-2022/s2 --full`, `show 32-2022/s3 --full`,
  `show 32-2022/s1 --full`, `toc 32-2022`.
- `edges 23-1927/s32` returned no typed links in either direction, so the
  amendment link was found by grep, not by the graph.
- `check` confirmed all five excerpts verbatim.

## What the answer turns on

Section 32(5) gives the caveator an action in a competent court, timed from the
posting of the section 32(4) notice. The corpus principal text is the 1990
consolidation and reads "thirty days"; Act No. 32 of 2022 s.2(5) substitutes
"sixty days". At the October 2025 matter date the answer is sixty days, so the
question is only answerable by reading principal plus amendment together. Hop
count 3: s 32(5), the 2022 substitution, and s 32(4) for the start of the
period.

## Alternatives rejected

- Registration of Title Act No. 21 of 1998 has no caveat provision in the
  corpus, so the deeds-registration route is the only one available.
- Civil Procedure Code s 536 is a testamentary caveat and is unrelated.
- Sections 33 and 34 (cancellation, damages for caveat without reasonable
  cause) are real but answer a different question; not included.
- The 2013 fee amendment was not used; the two-year currency now comes from
  s 32(3) as substituted in 2022, not from the fee paid.

## Corpus gaps

1. No consolidated post-2022 text of s 32; the sixty-day rule is assembled.
2. Act No. 32 of 2022 has no commencement section in the corpus (short title
   only), so its date of operation is assumed, not verified.
3. Prescribed forms (VIII, X, XI) and rules are not separate corpus sections.
4. No corpus provision on reckoning of days; the "11 August 2025" date in the
   conclusion is arithmetic and is flagged `inferential`.

## For the verifier, first

- Confirm from an authoritative consolidation that Act No. 32 of 2022 was in
  operation before June 2025, and whether it applies to caveats registered
  before it. If not, the answer reverts to thirty days.
- Check whether "within sixty days" is reckoned from the day of posting or the
  day after; claim CL-M016-Q01-010 assumes the day after.
- Check that the enriched facts (posting date, deed of transfer by a stranger)
  are neutral enough not to give the answer away.
