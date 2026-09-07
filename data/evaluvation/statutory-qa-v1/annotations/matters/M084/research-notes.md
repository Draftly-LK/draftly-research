# M084 research notes (status=unverified)

Notary asked to attest a deed; he does not know the executant, who is well
known to one of the witnesses, and that witness is the notary's brother.
Reference date 2019-10. One Tier A question, `enrich`.

## Queries run

- `acts` for the Notaries Ordinance act_id (`1-1907`) and every Notaries
  amending Act held (24-1973, 20-1976, 47-2011, 13-2013, 31-2022, 6-2024);
  `toc 1-1907`; `show 1-1907/s31 --full` and `--provisions`.
- `show` on 31-2022/s16, 6-2024/s3, 47-2011/s2, 47-2011/s3, 20-1976/s10 to fix
  which rules of section 31 were touched, and when.
- `grep` over 1-1907 and the whole corpus for: brother, relation, relative,
  consanguinity, affinity, kindred, spouse, credible witness, disinterest.
- `show 1-1907/s32`, `1-1907/s34`, `7-1840/s2` (all rejected, below).

## Temporal problem: look at this first

The corpus holds section 31 only as consolidated to 2024, so its rule (9) is
**not** the rule in force in October 2019. Rule (9) was substituted by Act
No. 31 of 2022 s.16(6) and altered again by Act No. 6 of 2024 s.3(3), and a
separate rule (10) existing in 2019 was repealed by 6-2024 s.3(4). The 2019
opening words survive in the corpus only in the recital in 31-2022/s16 of the
words it replaced. PROV-M084-001 therefore points at a 2022 amending section
while carrying `applicable_to_matter_date: true`, because what is relied on is
the wording quoted as replaced, not the amending Act. That is the one
judgement call in the map and it produces the only validator warning. If it is
rejected the fallback is `blocked_temporal_uncertainty`, not a different
answer: the outcome is the same on the unamended acquaintance-and-declaration
limb (PROV-M084-003), which needs the witnesses in the plural to be acquainted
with the executant and to sign the declaration.

## Rejected

- s.34 (penalty) and Prevention of Frauds Ordinance s.2: both held only in
  post-2019 forms, so their 2019 content could not be stated. Left out rather
  than quoted; rule (8), unamended, carries the two-witness point.
- s.32 (special cases): does not disapply rules (8), (9) or (13).
- Nothing in the corpus disqualifies a witness related to the notary. The
  brother point rests on that absence plus rule (13), which bars the notary
  only where he is a party. A lawyer should confirm no non-statutory rule of
  practice bites.
