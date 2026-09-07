# M091 research notes (status=unverified)

Paper 14, question 6, April 2019. One Tier A question, `enrich`.

## Queries tried

- `acts` to locate the Notaries Ordinance (`1-1907`) and its four amending Acts.
- `toc 1-1907`, then `show 1-1907/s31 --full` (25,684 characters, all 36 rules).
- `show` on `1-1907/s32`, `s33`, `s34`, `s37`, `s42`, `s43`.
- `grep "30A"` and `grep "thirty days from the date of attestation"` to date the
  registration deadline rule.
- `show 47-2011/s3` and `show 6-2024/s3` to recover the rule numbering and to
  separate pre-2019 text from later substitutions.
- `toc 23-1927`, `show` on `23-1927/s2`, `s4`, `s5`, `s6`, `s7`, `s14`.
- `edges 1-1907/s31` (returned the amending Acts and the s.32/s.33/s.42
  cross-references used here).

## Alternatives rejected

- Rule (30A) of s.31 (submit the deed for registration within thirty days, sixty
  where registration is outside the notary's jurisdiction) is the obvious modern
  answer for the original, but it was inserted by Act No. 31 of 2022 and did not
  exist in April 2019. The duty on the original is put on s.37 plus Registration
  of Documents Ordinance s.14(1) instead.
- Section 34 is in the map only as supporting context, marked
  `applicable_to_matter_date: false`: the corpus holds the 2022 replacement, and
  no claim relies on it.
- Registration of Documents Ordinance s.4 was rejected: it binds judges, Justices
  of the Peace and public officers, not notaries.
- Rule (28) (two or more notaries) was rejected because the enrichment fixes a
  single attesting notary.

## For the verifier, in order

1. Rule numbering. The corpus text of s.31 drops the label "(26)" from the
   duplicate-transmission rule; it appears as "(i) He shall deliver or transmit".
   The number is taken from Act No. 47 of 2011 s.3, Act No. 6 of 2024 s.3(8),
   and s.32(1)/s.34(2). Confirm before the map is shown to a lawyer.
2. Form references. Rules (26) and (29) read "Form F 1" in the corpus; that
   substitution is by Act No. 6 of 2024. In April 2019 both read "Form F".
   The excerpts quote the current text, so the form name in PROV-M091-003 and
   PROV-M091-004 is anachronistic; the duties are not.
3. PROV-M091-004 runs to 713 characters, above the usual 600. Rule (29) is a
   single sentence and cannot be shortened without dropping either the condition
   (land in another district) or the duty (certified copy to that registrar).
4. The Colombo and Nuwara Eliya land registration districts are enriched facts,
   not corpus law; see `corpus_gaps`.

The validator prints OK with no errors and no warnings.
