# M077 research notes

Status: unverified. One Tier A question (M077-Q01, `keep`), reference date 2020-04.

## Queries tried

- `acts`: the Partition Law No. 21 of 1977 is not in the corpus.
- `grep "accurate and clear description"`: Notaries Ordinance s.31, Act No. 47
  of 2011 s.2, Registration of Documents Ordinance s.13, Act No. 48 of 2011 s.2.
- `grep "divided or undivided share"`: only s.31(16)(b), no amending act, so
  that paragraph is unchanged since before the matter date.
- `search "description of land in schedule of deed boundaries extent lot number
  plan surveyor"`: nothing beyond those four; the Survey Act, Surveyors
  Ordinance and Apartment Ownership Law hits are condominium and cadastral
  plans, not the schedule of an ordinary transfer.
- `show 1-1907/s31 --provisions`, `edges 1-1907/s31`, `defs 1-1907`,
  `defs 23-1927`: no defined term governs "land", "deed" or "share", so no
  definition section is indispensable. `check` confirmed all seven excerpts.

## Alternatives rejected

- Definition of Boundaries Ordinance and Survey Act: boundary disputes and
  survey administration, not the content of a deed schedule.
- Prevention of Frauds Ordinance s.2: form of the deed as a whole.
- Ids such as `1-1907/s31/sub-16/par-a` appear in `show --provisions` but not in
  `corpus/sections.jsonl`, so the map cites `1-1907/s31` with the rule number in
  `subsection`.

## Corpus gaps and verifier notes

Gaps are listed in `legal-map.json`; the material one is the missing Partition
Law, so the answer uses the statutory words "particular boundaries and extent"
rather than a lot-in-plan requirement. Two corpus editions lag the 2011
amendments, hence the separate citation of the amending sections. The scenario
says the brothers hold equal undivided shares of the 45 perch
portion and are only now considering a partition action, yet part (iii) calls
the subject "Anuk's divided block". The draft treats the undivided one third as
the position on the stated facts and gives the divided-block description as the
alternative. If a completed partition was intended, CL-M077-Q01-009 and
CL-M077-Q01-010 swap emphasis and the provisions do not change. Validator
prints OK with no warnings.
