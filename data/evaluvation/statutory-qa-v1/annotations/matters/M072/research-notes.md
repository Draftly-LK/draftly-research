# M072 research notes (status=unverified)

Matter: Galle-zone notary, vendor in Ratnapura too ill to travel. One Tier A
question (M072-Q01, `keep`, 3 marks), reference date 2020-04.

## Queries tried

- `acts` to see which of the 57 statutes could bear on notarial execution.
- `toc 1-1907`, then `grep "jurisdiction" --act 1-1907` and
  `grep "area specified in his warrant|judicial zone|authorized to practice"`
  across the corpus. That surfaced s.2, s.4A, s.9, s.11 and, in the body of
  s.31, rule (22), which is the pivot of the answer.
- `show 1-1907/s31 --full` in two halves (the section is 25k characters) to
  reach rules (22), (29) and (30).
- `toc` and `show` on 7-1840, 4-1902 and 17-1852.
- `check` on all eleven excerpts before writing; all returned OK verbatim.

## Alternatives considered and rejected

- **s.9 (office within the warrant area)** and **s.11 (fresh warrant for
  another zone)**. Dropped. s.9 is about where the office sits, not where the
  notary may attest; s.11 would have Gayan Alwis abandon his Galle practice,
  which is not a method of executing this deed.
- **s.31 rule (12)** (executant and witnesses must sign in the notary's
  presence). True but not disputed here, and it adds nothing to the
  territorial point. Left out to keep the map tight.
- **Registration of Documents Ordinance No. 23 of 1927.** Registration of the
  deed is downstream of execution; the question asks only about execution.
- **Powers of Attorney Ordinance s.3A.** Recorded as background with
  `applicable_to_matter_date: false`. It was inserted in 2022, after the
  matter date, and must not be used to grade an April 2020 answer.

## Corpus gaps and what the verifier should check first

1. **Temporal wording.** The corpus holds only current consolidated editions.
   The quoted text of Prevention of Frauds s.2, Powers of Attorney ss.2 and 3,
   Notaries s.31 rule (30) and s.34 incorporates 2022 and 2024 amendments. In
   each case the proposition relied on predates them, and the temporal_note
   says so, but a pre-2022 edition would settle it. Check
   PROV-M072-003 and PROV-M072-004 first, since both are indispensable.
2. **Territorial extent.** Nothing in the corpus defines the Galle judicial
   zone or places Ratnapura outside it. That step rests on the question's own
   facts.
3. **Third route.** Whether the 1852 Ordinance is still a live option in
   practice is a judgment call; it is recorded as supporting, not
   indispensable, and the second method stands without it.
4. The validator prints OK with no warnings.
