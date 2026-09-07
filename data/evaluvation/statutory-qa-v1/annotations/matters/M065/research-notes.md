# M065 research notes (statutory-qa-v1, unverified)

Paper 11, question 4, parts 2 and 3. Reference date 2020-10. Both Tier A
questions are `keep`, so no enrichment was applied.

## Queries tried

- `acts`, then `toc 1-1907`, `show 1-1907/s31 --full`, `show 1-1907/s32 --full`.
  Section 31 is one 25,684-character section holding all the numbered rules, so
  every rule shares the `section_id` `1-1907/s31` and is distinguished by the
  `subsection` field.
- `show` on `31-2022/s16`, `6-2024/s3`, `47-2011/s2`, `47-2011/s3` and
  `20-1976/s10` to establish which rules of section 31 changed after 2020-10.
- `grep "common seal|execution of documents|method of contracting" --act 7-2007`
  found Companies Act s.19 (method of contracting).
- `show 7-1840/s2 --full` for the notarial-execution requirement for leases.

All 22 excerpts were confirmed verbatim by `validate_legal_map.py`, which
checks every `relevant_excerpt` as a whitespace-normalised substring of the
corpus body. Validation prints OK with no warnings.

## Alternatives rejected

- Deeds and Documents (Execution before Public Officers) Ordinance No. 17 of
  1852: execution before public officers, not a second notary.
- Registration of Documents Ordinance No. 23 of 1927: registration, not
  execution; s.31 rules (28) and (29) already carry the registration steps.
- Notaries Ordinance s.33 (defects of form): neither question asks about the
  consequences of non-compliance.

## Corpus gaps, verifier first stops

1. Why Q02 is `blocked_temporal_uncertainty`: only the consolidated Ordinance
   is in the corpus. Rule (20)(b) and (e) are 2022 substitutions and (h) is a
   2022 insertion, so the October 2020 list of attestation contents cannot be
   given in full. Rules (9) and (14) are in the same position and are
   supporting only. The pre-2022 wording of rule (9) survives verbatim inside
   `31-2022/s16`; nothing equivalent survives for rule (20)(b) or (e).
2. Prevention of Frauds Ordinance s.2 is also post-date text, so it is
   supporting for Q01. Q01 stands on the Notaries Ordinance and Companies Act
   s.19(1)(a), both unamended at the matter date.
3. The company "wishes to lease out" a warehouse owned by Russel Perera, so
   lessor and lessee are ambiguous. The answer does not turn on it and the map
   names the parties rather than their roles.
4. Form E of the Second Schedule is not a corpus section. The corpus text of
   rule (21) also has a transcription artefact (capitalised "With"); the
   excerpt stops before it.
