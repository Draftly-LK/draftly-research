# M006 research notes (statutory-qa-v1)

Status: `unverified`. One Tier A question (M006-Q01), `proposed_gold`.

## Queries tried

- `acts`, then `toc 1-1907` for the Notaries Ordinance section list.
- `grep "judicial zone" --act 1-1907` — s.3, s.4, s.4A, s.11, s.28, s.31.
- `show --full` on s.3, s.9, s.11, s.13, s.31, s.32, s.33, s.34, s.43.
- `defs 1-1907` — three defined terms only, none of them "area" or "zone".
- `edges 1-1907/s31` — amendment chain (1976, 2011, 2022, 2024).
- `search` over 23-1927 for the registration side; kept s.14(1).
- `check` run on all ten excerpts before writing; all verbatim.

## Alternatives rejected

- s.13 (practising without a warrant): Saman holds a warrant, so the penalty in
  point is s.34(1)(c).
- s.4A: deems a division warrant to authorise practice in the zone. His licence
  is already a zone licence, so it adds nothing.
- s.33 (non-compliance in matters of form): the question is whether he may
  attest, not whether the deed would be void. s.32's exclusions do not reach
  rules (22) or (29).
- 23-1927/s4: overlaps rule (29); s.14(1) states the principle more directly.

## Corpus gaps

Four recorded in `corpus_gaps`. The important one: nothing in the corpus
defines the territorial extent of a judicial zone, so "Kurunegala is outside
the Colombo zone" rests on the scenario, not on a cited provision.

## For the verifier, first

1. Whether rule (22) of s.31 bears the place-of-attestation reading, and
   whether rule (29) is fairly used as confirmation rather than as the rule.
2. Whether s.34(1)(c) is the right penalty limb — it turns on rule (22) being
   absent from paragraphs (a) and (b) of the 2022 text.
3. The two `synthetic_decisive` facts (place of attestation, language). They
   decide the answer; if the decisive facts should have been left open, the
   question becomes `blocked_scenario_ambiguity`.
