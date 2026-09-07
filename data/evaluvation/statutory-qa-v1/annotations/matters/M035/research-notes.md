# M035 research notes (statutory-qa-v1, unverified)

Both Tier A questions (M035-Q01 pedigree, M035-Q02 shares) are `keep`, so no
enrichment was applied. Both are `mixed_statute_and_case` and therefore
`reserved`, not `proposed_gold`. The full provision set, IRAC draft and claims
are still recorded so the verifier has something concrete to attack.

## Queries tried

- `acts` to see what succession law is in the corpus.
- `toc 15-1876`, then `show --full` on ss.20-32 and s.36 of the Matrimonial
  Rights and Inheritance Ordinance. Part III carries the whole answer.
- `grep "life interest"` and `grep "usufruct"` across the corpus: only Land
  Reform Law ss.3, 12, 42F and Registration of Title Act s.46 mention the
  term, and none states when a life interest ends.
- `grep "[Aa]dministrator's [Cc]onveyance"`: no match. Nearest hook is Civil
  Procedure Code s.542 (extent of the power of administration).
- `show 7-1840/s2`, `show 15-1876/s2` for the notarial and personal-law
  gateways.

## Alternatives rejected

- Jaffna Matrimonial Rights and Inheritance Ordinance, Kandyan Succession
  Ordinance and Muslim Intestate Succession Ordinance: excluded by MRIO s.2 on
  the assumption the family is under the general law. Nothing in the facts
  states this, so it is an assumption, not a finding.
- Wills Ordinance No. 21 of 1844: every death in the chain is intestate.

## What the verifier should check first

1. The s.27 question. This map applies the one-side proviso in s.27 to the
   sibling half created by s.25, giving Lalani 90/192, Ravi 41/192, Salinga
   25/192, Seena 36/192. If s.27 governs only the s.26 case and the sibling
   half is split three ways, the answer becomes Lalani 5/12, Ravi 5/24,
   Salinga 5/24, Seena 1/6. Everything downstream turns on this.
2. Ravi is excluded from Suneth's estate (half-blood through the surviving
   parent) but included in Akash's (both parents then dead). Confirm.
3. The grantee of Administrator's Conveyance No. 2635 is not stated in the
   facts; the map assumes it conveyed to Suneth's intestate heirs.
4. Two steps rest on Roman-Dutch law outside the corpus: the deed of gift
   vesting ownership in Suneth at once, and each life interest ending with its
   holder. MRIO s.36 points to that law but the corpus does not contain it.
