# M005 research notes (status=unverified)

Matter: Paper 1 Q5. One Tier A question, M005-Q01, `candidate_action = enrich`.
Reference date 2026-04.

## Queries run

- `acts` to confirm the Notaries Ordinance is in the corpus as `1-1907`, plus
  the three Notaries amendment Acts (12-2005, 13-2013, 31-2022).
- `toc 1-1907`, then `show 1-1907/s31 --full` and `show 1-1907/s31 --provisions`.
  Section 31 is one 25,684-character node; the sub-provision ids
  (`1-1907/s31/sub-17/par-a`, `.../pro-39`) are how the rule numbering was
  confirmed, because the printed body does not show the "(16)" and "(17)"
  markers.
- `show --full` on s32, s33, s34, s37, s38, s38A, s39.
- `edges 1-1907/s31` and `defs 1-1907`. No defined term the answer turns on:
  s.43 defines only "Council of Legal Education", "High Court Judge" and
  "Registrar-General".
- `check` on all seven excerpts; all returned verbatim.

## Decisions

- Rule (17)(a) is the operative rule and the proviso to rule (17) is the only
  exception, so both are indispensable along with the s.31 chapeau. Hop count 2.
- Rule (17)(b)(i) (certified folio extract), rule (33) (best endeavours to
  obtain the title deed) and s.34(1)(c) (penalty) are supporting: the yes/no
  answer stands without them.
- s.34(1)(c) applies by residue. Rule (17) is not named in s.34(1)(a) or (b),
  which list rules (1), (31), (32) and (2), (3), (6), (7), (11), (18), (21),
  (23), (24), (30A). The verifier should confirm that reading first.
- s.33 is background only. Its terms cover non-compliance "in respect of any
  matter of form", and whether omitting a title search is a matter of form is
  not settled by the text, so the gold answer leaves the validity of the deed
  open and confines itself to Saman's liability.

## Rejected

- s.38A (true nature of the transaction) and s.39 (fraud): no fact in the
  scenario suggests a disguised transaction or fraud, so including them would
  have imported an issue the question does not raise.
- s.31 rule (22) (area and language): Saman is licensed for the Colombo zone
  and the land is in the Colombo District, so no territorial issue arises. The
  enrichment fixes the execution in Colombo to keep it that way.
- Registration of Documents Ordinance No. 23 of 1927: the question asks for
  Notaries Ordinance provisions, and priority of registration is not needed to
  answer it.

## Corpus gaps

Recorded in `corpus_gaps`. The one that matters: the Ordinance is held only as
a consolidated edition, so the temporal check for rule (17) rests on the
section-level `amendment_events` (31 of 2022 and 6 of 2024, both before the
matter date) rather than on a per-rule commencement date. Act No. 6 of 2024
itself is not in the corpus as a separate Act.

## For the verifier

1. The s.34(1)(c) residual reading described above.
2. Whether rule (33) should be promoted to indispensable, since it is a second
   title-related duty on a deed of transfer.
3. Whether the five added facts overreach. FACT-001, FACT-003 and FACT-004 are
   marked `synthetic_decisive`; FACT-004 (no written authority) is the one that
   determines the answer.
