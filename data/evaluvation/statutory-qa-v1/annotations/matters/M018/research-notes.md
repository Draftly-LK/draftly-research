# M018 research notes (statutory-qa-v1, status=unverified)

One Tier A question, M018-Q01 (`keep`), reference date 2025-10.

## Queries run

- `acts` to see what is in scope; the relevant Acts are 7-1840 (Prevention of
  Frauds), 4-1902 (Powers of Attorney), 1-1907 (Notaries).
- `toc 4-1902`, `toc 7-1840`, `toc 28-2022`, `toc 3-2024`.
- `show --full` on 7-1840/s2, 4-1902/s2, s3, s3A, s3B, s3C, s3D, s4,
  28-2022/s8, 1-1907/s31.
- `search "power of attorney attorney executing deed on behalf of principal"`,
  `grep "power of attorney" --act 1-1907`, `grep "special power"`,
  `defs 1-1907`, `search "lease of immovable property registration priority"
  --act 23-1927`.
- All eleven excerpts confirmed as verbatim substrings before writing.

## Alternatives rejected

- Registration of Documents Ordinance No. 23 of 1927: registration of the
  lease deed is a later step and does not bear on who may execute it. Notaries
  Ordinance s.31(30A) already carries the notary's duty to submit for
  registration, so 23-1927 was left out to keep the map on the question asked.
- Stamp Duty Act No. 43 of 1982 and the 2006 special provisions Act: the
  question is about capacity to execute and the mode of execution, not duty.
- 4-1902/s3D (no private irrevocable power) and s.4 (revocation procedure):
  neither is engaged on the facts. s.4 is referred to inside the s.3C excerpt
  and does not need its own entry.
- 1-1907/s32 exempts a power of attorney for use out of Sri Lanka from some
  s.31 rules; the power here is for use inside Sri Lanka, so it does not apply.

## Corpus gaps

The decisive point of the first limb is outside the corpus. Nothing in the
frozen statutes says how far an attorney's mandate reaches, so the corpus
cannot answer whether a Special Power of Attorney "to sell" also permits a
lease; that is the Roman-Dutch law of mandate and judicial authority. There is
also no statutory rule on ratification of an act done beyond authority. The
question is therefore `mixed_statute_and_case` and `reserved`, not
`proposed_gold`.

## For the verifier

1. Check the `reserved` call. The second limb (how to execute in absence) is
   fully statute-backed; a reviewer may prefer to split the question rather
   than reserve the whole of it.
2. Check the temporal reasoning on 4-1902/s3C. The instrument dates from 2017
   and s.3C was only inserted in 2022. The map treats the five-year point as
   raising a doubt, not as settling the matter, because s.8 of Act No. 28 of
   2022 addresses registration and continued validity of pre-commencement
   powers without saying how the five years run for them.
3. PROV-M018-001/002 and PROV-M018-010/011 are two entries each on one corpus
   section (7-1840/s2 and 1-1907/s31), split by subsection because different
   limbs do different work. Confirm that is acceptable practice for this run.
4. Provision 4-1902/s2 paragraph (a) is quoted in its post-2022 form; the 2017
   instrument was granted under the earlier definition, which is not in the
   corpus. Its formal validity as at 2017 cannot be tested here.
