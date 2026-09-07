# M049 research notes

Paper 9, question 3, part 03. One Tier A question (M049-Q01),
`candidate_action = enrich`. Reference date 2021-10.

## Queries run

- `acts` — both Registration of Title Act No. 21 of 1998 (`21-1998`) and
  Prescription Ordinance No. 22 of 1871 (`22-1871`) are in the corpus.
- `grep "prescri" --act 21-1998` — surfaced s.57 ("Prescription"), the pivot.
- `toc` on both Acts; `show --full` on 21-1998 s.1, s.14, s.31, s.32, s.33,
  s.38, s.57, s.73, s.75 and on 22-1871 s.3.
- `edges 21-1998/s57` — only outgoing link is the s.75 definition of "land".
- `grep "adverse|possession" --act 21-1998` — only s.14(b) and s.59 matched.
- `check` run on all eight excerpts; all verbatim.

## Alternatives rejected

- 21-1998 s.32 (effect of registration): s.33 covers the same ground more
  directly, so s.32 was dropped rather than duplicated.
- 21-1998 s.29: its ten years is a limitation period for challenging a Second
  Class registration, not a route to prescriptive title.
- Prescription (Amendment) Act No. 26 of 2014: replaces s.15 of Chapter 68
  only, not s.3, so no temporal effect here.
- 21-1998 s.75 (interpretation): the two title classes are not defined there;
  they come from s.14, which is why s.14 is indispensable.

## Corpus gaps

Recorded in `legal-map.json`: the 21-1998 text is an unconfirmed consolidation
with no `amendment_events`; the s.1 Orders declaring areas are subsidiary
legislation and absent; case law on possession predating first registration is
out of scope.

## For the verifier

1. Whether s.14, not s.75, is the right home for the two title classes, and so
   whether it belongs in the indispensable set.
2. Whether `statute_only` survives. The s.57 bar is explicit, but the
   pre-registration possession point may need judicial authority; it is
   confined to a caveat in the conclusion and to claim `CL-M049-Q01-013`.
3. The added facts put Nimal off the register and Somapala on it with a First
   Class Title. That is decisive; the counterfactual is in
   `FACT-M049-Q01-002`.

Validator: `M049: OK errors=0 warnings=0`.
