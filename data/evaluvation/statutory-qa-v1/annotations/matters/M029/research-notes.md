# M029 research notes (status=unverified)

Matter: P04-Q08-M01, October 2024 session. One Tier A question (M029-Q01,
`enrich`): "A father intends to revoke a gift granted upon a Deed of Gift.
Discuss the grounds on which he can do so."

## Queries tried

- `acts` — spotted Act No. 5 of 2017 (Revocation of Irrevocable Deeds of Gift
  on the Ground of Gross Ingratitude) as the obvious governing enactment.
- `search "revocation of gift ingratitude" -k 15`, then `toc 5-2017` and
  `show --full` on all seven sections.
- `edges 5-2017/s2` and `edges 5-2017/s3` — the only typed link inside the Act
  is s.3 `procedurally_requires` s.2.
- `grep "gift"` corpus-wide, and `grep "gift" --act 7-1840`.
- `grep "lis pendens" --act 23-1927`, then `show 23-1927/s11 --full`.
- `check` on the s.2 and s.11 excerpts; the validator re-checks all six.

## Alternatives rejected

- Prevention of Frauds Ordinance s.2 — its list ("sale, purchase, transfer,
  assignment, or mortgage") does not name a gift, so I did not stretch it into
  a formal-validity or revocation-instrument point.
- Matrimonial Rights and Inheritance Ordinance s.12 — spousal gifts only; the
  donor here is a father, not a spouse.
- Kandyan Succession Ordinance No. 23 of 1917 — four sections on succession,
  nothing on revoking gifts to children.
- Trusts Ordinance s.80 (revocation of trust) — a trust is a different
  instrument; including it would be a false lead.

## Corpus gaps and why the question is reserved

Act No. 5 of 2017 gives the route (court order, donor v. donee), the time
bars, the lis pendens step and the procedure, but never defines "gross
ingratitude" — s.6 defines only "Registrar of Lands" and "land". The content
of the ground sits in Roman-Dutch common law and judicial authority, which
this corpus does not carry, and the corpus says nothing about deeds that
reserve a power of revocation. So `authority_requirement` is
`mixed_statute_and_case` and `research_status` is `reserved`, not
`proposed_gold`. Enrichment was still applied (five added facts) so the
scenario is determinate for the statutory conditions that do exist.

## For the verifier, first

1. The corpus body of `5-2017/s6` is garbled: the defined terms have been
   stripped into a `defined_terms` field, leaving two dangling "means"
   clauses. Read it against the Gazette before relying on my reading that the
   Act defines nothing else.
2. `23-1927/s11` has an OCR artefact ("Us pendens" for "lis pendens"); my
   excerpt avoids the affected words.
3. Check whether the reserved classification is right, or whether a marker
   would expect a statute-only answer confined to Act No. 5 of 2017.

`validate_legal_map.py M029` prints OK with no warnings.
