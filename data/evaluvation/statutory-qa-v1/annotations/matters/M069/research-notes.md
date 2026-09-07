# M069 research notes (statutory-qa-v1, status=unverified)

Tier A: M069-Q03 only ("Draft this Notice to be submitted to the Land
Registry"). Q01 and Q02 are Tier B and were not annotated.

## Queries tried

- `acts` to see the corpus, then `toc 23-1927` — the Registration of Documents
  Ordinance is the only registration statute in scope.
- `grep "notice of" --act 23-1927`, `grep "priority notice"` across the whole
  corpus. Section 30 ("Priority notices") is the only provision that matches
  the facts: a notice registered before execution so that the deed and bond,
  once registered, take effect from the date of the notice.
- `show --full` on 23-1927 ss. 2, 3, 6, 7, 8, 13, 14, 25, 26, 27, 28, 29, 30,
  33, 34, 36, 43, 44, 49, 50.
- `edges 23-1927/s30` returned nothing in either direction, so the links to
  ss. 13, 26 and 43 were built by hand from s.30(4) ("register it in the same
  manner as other instruments").
- `grep "Second Schedule"` and `toc` on 22-1958, 21-2013, 32-2022, 18-2024 to
  check the amendment history of s.30 and to look for the prescribed form.
- Every excerpt was confirmed with `check`.

## Alternatives rejected

- Caveat (s.32): a caveat asks to be served with notice of other registrations;
  it does not confer priority and does not fit "release the Loan ... without
  awaiting the completion of registration formalities".
- Seizure priority notice (s.31) and lis pendens (s.11): both presuppose
  execution or litigation, absent here.
- Registration of Title Act No. 21 of 1998: title registration, a different
  register, and nothing in the facts puts Ratmalana in a declared area.

## Corpus gaps

- The Second Schedule to Ordinance No. 23 of 1927 (the prescribed forms) is
  not in the corpus, although s.50 makes those forms mandatory. This is why
  Q03 is `blocked_missing_authority` rather than `proposed_gold`.
- The s.49 regulations and the First Schedule fees are likewise absent.

## For the verifier

1. Check the block: if a Second Schedule priority notice form is added to the
   corpus, Q03 could move to `proposed_gold` on the same provisions.
2. Check issue ISS-M069-Q03-04. The draft treats Gamini Perera as transferee
   and his vendor as transferor. A defensible reading makes the Bank the
   transferee for the bond, which would change the parties in the draft.
3. s.30(4) is used as the bridge to ss. 13 and 26; that step is inferential,
   since "instrument" in ss. 6 and 25 does not expressly cover a notice.
