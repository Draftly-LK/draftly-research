# M067 research notes (status=unverified)

Matter: paper 11, q9, part 5, October 2020. One Tier A question, `enrich`.
"A minor owns a land. Is it possible for the father of the child to sell the
property? If so, explain the procedure."

## Queries tried

- `acts` to see the corpus. No Age of Majority Ordinance, no Guardianship or
  Maintenance statute.
- `grep "minor" --act 2-1889` — surfaced CPC Chapter XXXVII (ss.476-502) and
  Chapter XLII (ss.582-594).
- `search "guardian of minor sale of minor property leave of court"`,
  `search "leave of court to sell immovable property of minor curator"`,
  `grep "curator"`, `grep "sell or mortgage"`, `grep "natural guardian|upper
  guardian|venia aetatis"`.
- `grep "minor"` over the Notaries Ordinance and the Powers of Attorney
  Ordinance: no match in either.
- `toc 2-1889`, `show --full` on ss.502, 571, 582, 583, 585, 586, 587, 588,
  752; `show --full` on 7-1840/s2 and 23-1927/s7. `edges 2-1889/s582` returns
  nothing in either direction.
- Every excerpt confirmed with `check`; all eleven return OK.

## Alternatives rejected

- CPC Chapter XXXVII (next friend, guardian ad litem, ss.476-500) is about
  minors as parties to actions, not about alienating their property.
- CPC s.530 and s.743 concern minor heirs in testamentary matters, not a sale
  of land the minor already owns outright.
- Prevention of Frauds Ordinance s.2(2)(b) (guardian may act for a minor
  transferee) was inserted by Act No. 30 of 2022, after the matter date, and
  in any event covers the transferee, not a transferor. Not relied on.
- Land Development Ordinance s.76 and State Lands Ordinance ss.106-107
  (curators appointed by a Government Agent) apply to state land holdings,
  not to privately owned land, so they were left out.

## Why reserved

Statute alone does not answer this. The father's position as natural guardian,
and the rule that he cannot alienate the child's immovable property without the
sanction of the court as upper guardian, are Roman-Dutch common law and case
law. CPC s.571 states that restriction expressly for a person of unsound mind
and there is no parallel provision for a minor, which is what makes the gap
visible. Classified `mixed_statute_and_case`, `research_status: reserved`.

## For the verifier, first

1. CPC s.584 is absent from the corpus edition with no repeal note (recorded in
   the source JSON under `omitted_provisions`). It falls inside the chapter this
   answer relies on, so the procedure set out here may be incomplete.
2. s.587(4) is the only sale power found in the corpus. It is framed as raising
   a maintenance allowance out of the corpus after a certificate under s.586,
   not as a general power of sale. Confirm that reading before it is treated as
   the statutory basis for a sale here.
3. The corpus text says "Family Court" in ss.582, 583 and 588 but "District
   Court" in s.752. Which court actually entertains the petition cannot be
   settled from the corpus.
4. Prevention of Frauds Ordinance s.2 is held only post-2022; the wording quoted
   is not the October 2020 wording, though the notarial requirement itself dates
   from 1840.

Validator: `M067: OK errors=0 warnings=0`.
