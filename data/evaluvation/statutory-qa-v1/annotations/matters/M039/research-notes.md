# M039 research notes (status=unverified)

Matter: "A deed of gift states that it is absolute and irrevocable. Could it be
revoked?" One Tier A question (M039-Q01), candidate action `enrich`, reference
date 2023-10.

## Queries tried

- `acts` — the corpus list itself gave the answer: Act No. 5 of 2017,
  Revocation of Irrevocable Deeds of Gift on the Ground of Gross Ingratitude.
- `toc 5-2017`, then `show 5-2017/s1..s7 --full` (all seven sections read).
- `edges 5-2017/s2` and `edges 5-2017/s3` — only one link, s 3
  `procedurally_requires` s 2. No definitions feed s 2.
- `grep "revok"` and `grep "gift"` across the whole corpus, to check whether any
  other Act supplies a revocation route for a deed of gift. Nothing did.
- `check` run on all four excerpts; all confirmed verbatim.

## Alternatives considered and rejected

- **Prevention of Frauds Ordinance, s 2** (read in full). Its opening words
  cover sale, purchase, transfer, assignment and mortgage; gifts are not named,
  so it was not used to support a "revocation must be notarially executed"
  claim. Its 2022 and 2024 amendment events were noted; the 2024 one post-dates
  the matter date in any event.
- **Matrimonial Rights and Inheritance Ordinance, s 12** (gifts between
  spouses). Read in full; it authorises inter-spousal gifts and says nothing
  about revocation, so it is off the point once the enrichment makes the parties
  uncle and nephew.
- **5-2017 s 6** (interpretation) defines only "Registrar of Lands" and "Land",
  neither of which the answer turns on; left out. s 1 and s 7 are formal.

## Corpus gaps

- "Gross ingratitude" is undefined in the Act. Its content is Roman-Dutch and
  judicial and is not in the corpus. The draft therefore states the ground and
  the evidence the donor would rely on, but leaves the finding to the court
  instead of asserting it. This is the reason CL-M039-Q01-003 and -008 are
  marked `inferential`.
- The Act as extracted has no transitional provision, and the prior common law
  on revocation of donations is not in the corpus, so nothing here shows whether
  the Act reaches deeds executed before 2017. The enrichment dates the deed
  12 March 2019 to keep that question out of the scenario.
- Kandyan law (Ordinance No. 39 of 1938) is absent from the corpus; the
  enrichment states the parties are governed by the general law.

## For the verifier

1. The `statute_only` call is the judgment most worth a second look. It rests on
   s 2 answering the question asked (can it be revoked, on what ground, by whom,
   how) without the common law, with the gross-ingratitude finding left open.
   If the verifier thinks the common-law meaning of the term is indispensable,
   the question becomes `mixed_statute_and_case` and `reserved`.
2. Check the two decisive dates against s 3: execution 12 March 2019 (ten-year
   limit) and June 2023 conduct with an October 2023 consultation (two-year
   limit). Both limits are cumulative.
3. The validator prints OK with no warnings.
