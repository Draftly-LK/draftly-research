# M004 research notes

Matter M004, one Tier A question (M004-Q01, paper 1 q3(iv), 3 marks). Status
is `unverified` throughout: proposed research output, not lawyer-validated.

## What the question needs

Rule 1 of the Third Schedule to the Land Development Ordinance, which lists
the groups of relatives entitled to succeed where the owner of a holding dies
without a nominated successor.

## Queries tried

- `acts` — the corpus has the Land Development Ordinance as `19-1935`
  (consolidated, 143 sections) and no Land Development amendment instrument.
- `grep "Third Schedule" --act 19-1935` — three hits only: s.48B, s.51, s.72,
  all of them references to rule 1, none of them the rule itself.
- `grep "Schedule" --act 19-1935`, `toc 19-1935` — no schedule appears in the
  table of sections; the extraction runs s.1 to s.172 and stops.
- `grep "brothers|sisters|nephew" --act 19-1935` — no match, so no section
  carries the list in the body text either.
- `grep "THIRD SCHEDULE"` across the whole corpus — hits in other Acts only.
- Read the finalized source JSON directly: `schedules_referenced` includes
  "Third Schedule" but `schedules` is empty, confirming schedules were never
  extracted rather than merely missed by search.
- `defs 19-1935` and `show 19-1935/s2 --full` for "owner" and "holding".
- `show --full` on s.48, s.48A, s.48B, s.49, s.51, s.68, s.72, s.73, s.74,
  s.170.

## Why the question is blocked

`blocked_missing_authority`, with `authority_requirement: statute_only`. The
whole route to the Schedule is in the corpus and is recorded as provisions
(s.170(1) excludes general intestacy law; s.49 gives the nomination route;
s.48B(1) puts a surviving spouse ahead of the Schedule class; s.72 sends title
to rule 1; s.73 fixes the date; s.51 confirms the Schedule is organised as
"groups of relatives"). The list itself is not there and was not guessed.

Also missing: the Land Development (Amendment) Act No. 11 of 2022 named in the
question. It shows up only as `amendment_events` with `operation: unknown` on
29 sections of the consolidated text, and on none of s.48B, s.51 or s.72, so
the corpus cannot say whether it changed the succession order.

## For the verifier

- Check first whether the Third Schedule can be added to the corpus from the
  Government Printer consolidation; if it can, this question converts to
  `proposed_gold` with one extra hop and no other change.
- s.2 excerpt (PROV-M004-002): the extraction drops the quoted defined term at
  the head of most definitions, so the "owner" definition reads as a bare
  "means ..." clause. The excerpt is verbatim but its term is identified by
  position in the section, which is worth a second look.
- PROV-M004-006 and PROV-M004-007 use the full section body as the excerpt
  (s.72 is 699 characters, slightly over the ~600 guide) because each is a
  single sentence that loses its conditions if cut.
- Enrichment was applied even though the question is blocked; the added facts
  (grant-derived holding, no surviving spouse, no nomination by deed or will,
  which relatives survived, the bond and release numbers) make the scenario
  determinate and none of them depends on the Schedule text.
- The validator prints OK with no warnings.
