# M073 research notes (status=unverified)

Matter: beneficiary asked to attest the testator's own will; one Tier A
question (M073-Q01, `enrich`, 3 marks, April 2020 session).

## Queries tried

- `acts` to see what is in the corpus; only the Wills Ordinance No. 21 of 1844
  and the Prevention of Frauds Ordinance No. 7 of 1840 carry will law.
- `search "attesting witness beneficiary will devise legacy void"` put
  `7-1840/s11` first by a wide margin, with s.10, s.12 and s.13 behind it.
- `toc 7-1840`, `toc 21-1844`, `toc 1-1907`; `grep "will" --act 1-1907`.
- `show --full` on 7-1840 s.4, s.10, s.11, s.12, s.13 and `show --provisions`
  on 1-1907/s31; `show --full` on 31-2022/s16 and 6-2024/s3 to date the rules.
- `check` on all seven excerpts: all verbatim.
- `edges 7-1840/s11` returns nothing in either direction, so the links to
  s.10, s.12 and s.13 in the map are my reading, not corpus edges. Worth a
  second look by the verifier.

## Alternatives rejected

- Wills Ordinance No. 21 of 1844: s.2 is about capacity to dispose and s.5 to
  s.9 about foreign wills, re-execution, survivorship and settlements. Nothing
  on attesting witnesses, so no provision from it is in the map.
- Notaries Ordinance s.31(9) (witnesses of good repute) looked apt, but it was
  substituted by Act No. 31 of 2022 s.16(6) and the corpus holds only the later
  text, so I used rules (8) and (12), which neither amending Act touches.

## Corpus gaps

- Prevention of Frauds Ordinance s.4 in the corpus is the post-2022 text
  (thumb impression). The April 2020 wording is absent, so s.4 is background
  and marked not applicable to the matter date.
- Notaries Ordinance s.31 rule (10) was in force in April 2020 but was
  repealed by Act No. 6 of 2024 s.3(4) and its text is not in the corpus. If
  it bore on interested witnesses, the map is missing it.

## Look at first

Whether s.12 deserves indispensable status: the charge-for-debt exception is
inside s.11 itself, and s.12 only confirms the creditor's competence. Dropping
it would take the hop count from 3 to 2. The added debt and executor facts
(FACT-...-004, FACT-...-005) are what make s.12 and s.13 bite; a reviewer who
thinks a 3-mark question should stay simpler may want them cut.
