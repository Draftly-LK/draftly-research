# M010 research notes (statutory-qa-v1, proposed, unverified)

Matter: Martin Perera's last will (house to helper Siripala, driver Nihal as
executor, children left nothing). Tier A questions Q01 and Q02, both `enrich`,
reference date 2026-04.

## Queries tried

- `acts`; `grep "legitime"` — no match anywhere, so freedom of testation had to
  be reached through express statutory words, not a doctrine.
- `grep "testamentary"` — surfaced Wills Ordinance s.2, which decides Q01, and
  the whole of Civil Procedure Code Chapter XXXVIII for Q02.
- `toc 21-1844`, `toc 15-1876`, `toc 2-1889`, `grep "will" --act 7-1840`,
  `show --full` on every section recorded, `edges 21-1844/s2`.

## Alternatives rejected

- Matrimonial Rights and Inheritance Ordinance s.24 as an operative limit on
  Q01: s.21 confines Part III to inheritance *ab interstate*, so s.24 is
  background only.
- CPC ss.525, 527: both are worded for a person dying *without* a will. CPC
  ss.520, 523: security is required of an administrator appointed under s.518,
  not of an executor taking probate, and there is no competing claimant.

## Corpus gaps

Listed in `legal-map.json`. The two that matter: Notaries Ordinance duties of
the attesting notary were not brought in (Q01 rests on Prevention of Frauds
Ordinance s.4 alone), and no duty schedule is in the corpus.

## For the verifier, first

1. Wills Ordinance s.2 is cited twice (PROV-001 for s.2(1), PROV-002 for
   s.2(2)); confirm splitting one corpus section into two provisions is allowed.
2. Prevention of Frauds Ordinance s.4 is *indispensable* to Q01 on the view
   that "can he execute the will" includes formal validity. Read narrowly as
   only about giving reasons, it drops to supporting.
3. Dates in the Q02 enrichment (death 14 Feb 2026, will found 17 Feb 2026,
   petition due 17 May 2026) are synthetic and drive the s.524 three-month
   calculation. The validator prints OK with no warnings.
