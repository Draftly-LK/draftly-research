# M110 research notes (statutory-qa-v1, unverified)

Paper 16, Q5(A)(5), April 2018. One Tier A question, `enrich`. Background:
"The executant has signed in Japanese." Asks the notary's duty.

## Queries tried

`acts`; `grep "language" --act 1-1907` (hit s.2, s.3, s.5, s.23, s.31, s.40);
`show 1-1907/s31 --full` and `--provisions`; `toc 1-1907`; `show` on s.2, s.32,
s.33, s.34, s.38A, s.43; `toc`/`show` on 31-2022/s16, 6-2024/s3, 47-2011/s2,
47-2011/s3, 20-1976/s10. Rule (15) exists as provision `1-1907/s31/sub-15`, but
only `1-1907/s31` is a valid `section_id` in `corpus/sections.jsonl`, so the map
cites the parent section with `subsection` set to the rule number.

## Temporal work

`1-1907/s31` carries 41 section-level amendment events with no mapping to
individual rules, so I read the amending sections. Act No. 31 of 2022 s.16
substitutes rules (3)-(7), (9), (14), (16), (17), (20), (27), (30) and inserts
(15A); Act No. 6 of 2024 s.3 touches (5), (7A), (9), (10), (15A), (17), (20),
(26), (29), (30); Act No. 47 of 2011 touches only (16)(a) and (26). None
substitutes rule (11), (15) or (22), so those read as at April 2018. Rule (15A)
(thumb impression beside the signature) is post-2018 and is excluded.

## Alternatives rejected

- Rule (14) (ascertain full names) is relevant but was wholly substituted by
  Act No. 31 of 2022 s.16(7), so the corpus text is not the 2018 text.
- s.34 (penalty for breach of the s.31 rules) was replaced by Act No. 31 of 2022
  s.17 and its fine figures are post-2018; the answer says nothing on penalties.
- Rules (20)(d) and (21) were both amended after 2018 and add nothing here.
- s.33 (no invalidity for a defect of form) invites a validity conclusion the
  question does not ask for and that turns on case law on "matter of form".

## Corpus gaps

Listed in `legal-map.json`: no as-at-2018 edition of the Ordinance; s.34 text is
post-2018; nothing on interpreters or certified translations.

## For the verifier

1. Confirm rule (15) covers a signature in a foreign script as well as a foreign
   language, and that the thumb-impression limb is confined to marks
   (CL-M110-Q01-003).
2. Rule (11) is engaged only by the synthetic decisive fact FACT-M110-Q01-005
   (executant cannot read English). Cut that and claims 005, 009 and part of 010
   go with it.
3. The enriched background uses fictional names, address and consideration.
