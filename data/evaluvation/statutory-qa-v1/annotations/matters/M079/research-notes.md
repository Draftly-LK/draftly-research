# M079 research notes (statutory-qa-v1, status=unverified)

Paper 13 Q1, October 2019. Three Tier A parts, all `keep`, so no enrichment.

## Queries tried

- `acts` to scope the corpus, then `toc 15-1876`, `toc 1-1911`, `toc 2-1889`.
- `search "minor guardian sale of immovable property court sanction"`,
  `grep "guardian" --act 2-1889`, `grep "majority"`, `grep "eighteen years"`.
- `show --full` on 15-1876 ss.20-24, 1-1911 ss.2, 3, 6, 7, 8, 14, 19, 20, 21,
  22, 39, 2-1889 ss.502, 518, 530, 531, 534, 582, 585, 586, 7-1840 ss.2, 3,
  21-1844 s.2, and the amending sections 30-2022/s2 and 4-2024/s2.
- `grep "donee"` and `grep "gift" --act 7-1840` for acceptance of the 2008
  Deed of Gift. Nothing usable; dropped.

## Alternatives rejected

- Thesawalamai Pre-emption Ordinance No. 59 of 1947. Lots 5A and 5B are
  divided lots in sole ownership, so no notice to a co-owner arose.
- 1-1911 s.3. Nothing says Mala Nadaraja's husband was outside the
  Thesawalamai, so the sub-rule about mixed marriages was not applied.
- Registration of Documents Ordinance priority sections. Nothing in the facts
  raises a competing registration.
- Wills Ordinance s.2 is kept as background only: the corpus text is the 2022
  substitution, later than the 2010 will and later than the matter date.

## Corpus gaps

Listed in full in `legal-map.json`. The two that block Q01 and Q03 are the
Partition Law No. 21 of 1977 and the Age of Majority Ordinance, plus the
Roman-Dutch rules on a minor's deed and on the effect of a Thesawalamai
disposition made without the husband's written consent.

## For the verifier, in order

1. The Q02 shares turn on treating Deed No. 1234 as severable, valid as to
   Malika Peiris's Lot 5B and defective only as to the minor's Lot 5A. If
   severability does not hold, Q02 is not statute_only either.
2. 1-1911 s.19(a) excludes consideration drawn from the spouse's separate
   estate. The scenario is silent on where Mala Nadaraja's purchase money came
   from, so the thediatheddam characterisation of Lot 5B is an inference.
3. s.20 of the same Ordinance divides only the deceased spouse's
   thediatheddam. The reading that Mala Nadaraja kept the whole of her own
   should be checked; the Q02 result depends on it.
4. PROV-M079-015 quotes only the opening words of Prevention of Frauds s.2,
   which predate the 2022 and 2024 amendments carried in the corpus text.
