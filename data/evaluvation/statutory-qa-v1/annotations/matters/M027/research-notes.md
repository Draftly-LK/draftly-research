# M027 research notes (statutory-qa-v1, unverified)

Matter: Paper 4, Q4(2)(a)-(c), October 2024. Three Tier A questions, all
`keep`, so no enrichment was applied.

## Queries tried

- `acts`, then `toc` for `1-1907` (Notaries), `7-1840` (Prevention of Frauds),
  `4-1902` (Powers of Attorney), `23-1927` (Registration of Documents),
  `12-2006` and `43-1982` (stamp duty), `17-1852`.
- `show --full` on every section cited; `show --provisions` on `1-1907/s31` to
  see how the 25,684-character rule block is split.
- `grep "lease"` over `12-2006`, `43-1982` and `11-1973`;
  `search "registration of condominium property instruments" --act 11-1973`.
- All excerpts were sliced directly out of `corpus/sections.jsonl` by a build
  script, so each is verbatim by construction; the validator confirms it.

## Alternatives considered and rejected

- Deeds and Documents (Execution before Public Officers) Ordinance No. 17 of
  1852 s.2 (execution before a District Judge or a gazetted Justice of the
  Peace) is a genuine alternative route, but it turns on offices and a Gazette
  notification the corpus cannot confirm are still operative, so it was left
  out rather than asserted.
- Notaries Ordinance s.9 (office within jurisdiction) and s.4A (warrant deemed
  to extend to the judicial zone) were read but not recorded: they bear on
  where the notary may hold office, not on where she may attest, which is rule
  (22).
- Apartment Ownership Law s.10 is recorded as background only, because nothing
  in the matter says this apartment is a registered Condominium Property.

## For the verifier, first

1. `PROV-M027-007` (attorney's affidavit) has no usable rule number: the
   corpus text of s.31 has lost the numbering between rules (15) and (18).
   Confirm the printed rule number against the Act.
2. `PROV-M027-013` is called rule (26) on the strength of the cross-references
   in s.21(1)(d) and s.34(2), not on a number printed in the rule itself.
3. M027-Q01 assumes Negombo falls outside the area Kanthi is authorised for;
   the corpus has no zone list, so the answer is phrased conditionally.
4. M027-Q03 is `blocked_missing_authority`: the rate Order under s.3(1) of Act
   No. 12 of 2006 is not in the corpus, so no figure is given.
5. Commencement dates are absent from the corpus, so the 2024 amendments to
   the Notaries Ordinance, the Prevention of Frauds Ordinance and the Powers of
   Attorney Ordinance are assumed to have been in force by October 2024.

Validator: `M027: OK errors=0 warnings=0`.
