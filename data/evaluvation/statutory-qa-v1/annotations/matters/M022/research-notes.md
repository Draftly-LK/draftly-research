# M022 research notes (statutory-qa-v1, status=unverified)

One Tier A question, M022-Q01 (`enrich`), reference date 2025-10. Notary's
duty of secrecy when the testator's children ask whether he has made a will.

## Queries run

- `acts` and `acts` filtered for Notaries to fix the amendment chain in scope
  (13-2013, 47-2011, 31-2022, 6-2024, 20-1976, 24-1973).
- `grep "divulg|secre|disclos" --act 1-1907` and `grep "divulg"` corpus-wide;
  the only notarial secrecy provision is s.31 rule (1). The other hits
  (17-2002/s58, 6-1990/s102, 7-2007/s180) are unrelated official-secrecy
  clauses.
- `toc 1-1907`, `show 1-1907/s31 --full` (one 25.6k-character section holding
  all the rules), `show 1-1907/s34 --full`, `show 1-1907/s41 --full`,
  `show 1-1907/s43 --full`, `defs 1-1907`, `edges 1-1907/s31`.
- Temporal check: `toc 6-2024`, `toc 31-2022`, `show 31-2022/s16 --full` and a
  grep for "rule (1)" in `6-2024/s3`. Neither amendment touches rule (1);
  31-2022 s.16 starts its substitutions at rule (3). s.34 as substituted by
  31-2022 s.17 still lists rule (1), which corroborates that rule (1) stands.
- All five excerpts confirmed with `check` before writing.

## Alternatives rejected

- Wills Ordinance No. 21 of 1844: `toc` and grep show nothing on secrecy or on
  disclosure by the attesting notary, so it adds nothing.
- s.21 (inquiry into notary's misconduct) and s.31 rule (34) (explanation to
  the Registrar-General): both are about the disciplinary route, not about
  whether disclosure is permitted, so they were left out. The answer mentions
  misconduct only as a possibility, without citing a provision for it.
- s.31 rule (36)(b) (inspection of records by named officials) was considered
  as an illustration of "required to do so by law" but applies only to
  notaries who are not attorneys-at-law, so it would narrow the point wrongly.
- s.41(4) kept as `background` only: it bites on death, retirement or sale of
  a practice, not on a lifetime request.

## Corpus gaps

The Evidence Ordinance is not in the corpus, so the professional-communications
privilege and the notary's compellability as a witness could not be checked;
that matters only to the "required to do so by law" exception, which the added
facts exclude. No professional-conduct rules for notaries are in the corpus
either. The conclusion rests entirely on s.31 rule (1), which is self-contained,
so the question is still `statute_only` and `proposed_gold`.

## For the verifier

1. The reading of "his employer" in rule (1) as the testator who instructed
   the notary. This is the load-bearing step and it is an interpretation of an
   undefined term (s.43 defines only three terms, none of them "employer").
2. Whether s.34(1)(a) should be `indispensable` (it supports the consequence
   claims the "Discuss" element calls for) or merely `supporting`. If it is
   demoted, `legal_hop_count` drops to 1.
3. The inherited first paragraph of the shared background (Sunil, aged 20,
   chronic disease) is flagged `inherited_shared_background_irrelevant` in the
   candidate file and has nothing to do with this part. It is preserved in
   `enrichment.original_background` but deliberately dropped from
   `enriched_background`, which covers only the notary-secrecy scenario.
4. `validate_legal_map.py M022` prints OK with no warnings.
