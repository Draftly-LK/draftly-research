# M080 research notes (statutory-qa-v1)

Matter: paper 13, question 3(i), October 2019. One Tier A question, marked
`enrich`. Status `unverified`: proposed only, pending verifier and lawyer.

## Queries run

- `acts` — the corpus list itself surfaced the governing statute, Revocation of
  Irrevocable Deeds of Gift on the Ground of Gross Ingratitude Act No. 5 of 2017.
- `toc 5-2017`, then `show --full` on all seven sections.
- `grep "revocab|revocation|revoke"` and `grep "deed of gift|donation|donee|donor"`
  across the whole corpus, to check nothing else governs revocation of gifts.
- `edges 5-2017/s2|s3|s4`, `show 23-1927/s11 --full`, `show 7-1840/s2 --full`.
- `check` on all six excerpts: all confirmed verbatim.

## Alternatives considered and rejected

- Muslim Intestate Succession Ordinance s.3 has a proviso that no deed of
  donation is irrevocable unless the deed says so. It only applies to donations
  by Muslims, and the scenario does not raise a personal-law issue, so it was
  left out rather than made a background provision.
- Prevention of Frauds Ordinance s.2 was rejected on two grounds: its corpus
  text is the consolidated edition carrying 2022 and 2024 amendments, so it is
  not the text in force at the October 2019 matter date, and its operative words
  are sale, transfer, assignment and mortgage rather than gift.
- Registration of Documents Ordinance s.11 was kept only as background, on
  subsection (6), because s.4 of the 2017 Act makes lis pendens registration
  compulsory but the effect of registration is context, not a step in the answer.

## Corpus gaps

- Gross ingratitude is undefined in the Act and the Roman-Dutch law and case law
  that fill it are outside this corpus. The answer states the statutory route
  and both time limbs as determinate and expressly leaves the grading of the
  donee's conduct to the court.
- Nothing in the corpus states the pre-2017 position, so the enrichment dates
  the deed at March 2018, after the Act, to avoid a retrospectivity question.
- Only the as-enacted edition of Act No. 5 of 2017 is held; no amending Act is
  in the corpus, so the enacted text is assumed unamended at October 2019.

## For the verifier, in order

1. The `statute_only` call. It is defensible only because the conclusion turns
   on s.2 and the s.3 time bar, not on grading the conduct. If the verifier
   thinks the answer cannot stand without the case law on gross ingratitude,
   this becomes `mixed_statute_and_case` and the question is `reserved`.
2. The s.6 excerpt begins mid-sentence because the corpus body of that section
   has the defined terms stripped out of the lead-in. Check against the source.
3. The corpus text of Registration of Documents Ordinance s.11 has OCR damage
   (lis rendered as Us); the excerpt used avoids the damaged subsections.
4. Hop count 2 assumes s.4 and s.5 are procedural rather than indispensable.

Validator: `validate_legal_map.py M080` prints OK, 0 errors, 0 warnings.
