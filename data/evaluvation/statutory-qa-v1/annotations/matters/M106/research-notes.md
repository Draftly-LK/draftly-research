# M106 research notes (status=unverified)

Both Tier A questions (M106-Q01 pedigree, M106-Q02 shares) share one scenario
and one set of provisions, so the same legal map serves both. Both are `keep`,
so no enrichment was applied.

## Queries tried

- `acts` to confirm which succession statutes are in the corpus.
- `toc 15-1876`, then `show --full` on ss.2, 3, 20-33 and 36.
- `defs 15-1876` (only s.3 carries definitions; "immovable property" is the one
  the answer relies on).
- `grep "half-blood"` to confirm ss.25-29 are the only half-blood rules.
- `edges` on ss.22, 24, 26, 27 returned nothing in either direction, so the
  chain between them was built by reading, not from the graph.
- `check` run on all twelve excerpts; all came back verbatim.

## Alternatives rejected

- Kandyan Succession Ordinance (23-1917) and Muslim Intestate Succession
  Ordinance (10-1931) are in the corpus but excluded by 15-1876 s.2, since
  nothing in the facts points to Kandyan, Muslim or Thesawalamai status.
- 15-1876 s.33 (illegitimate children) was rejected. Achini is described as a
  daughter by a first wife, so she is a lawful child of Nimal.
- 15-1876 s.28 and s.29 were rejected: full siblings survive Bimal, and the
  half-sibling is on one side only, so s.27's final limb governs.
- 15-1876 s.36 and Prevention of Frauds Ordinance s.2 are recorded as
  background only. Nothing in the answer rests on them.

## For the verifier, first

1. The arithmetic. Amal 203/1152, Krishni 203/1152, Achini 86/1152, Amali
   84/1152, Sunil 5/12, Kusum 1/12. The six add to 1152/1152.
2. The s.27 split of Bimal's sibling portion. The reading taken is that Amal
   and Krishni take 7/192 between them first, then the remaining 7/192 goes per
   capita to Amal, Krishni and Achini.
3. The scenario says Bimal died but does not say he died intestate. Intestacy
   is assumed and the assumption is stated in both gold answers and carried by
   claims CL-M106-Q01-015 and CL-M106-Q02-018. If a lawyer rejects the
   assumption, the question should move to `blocked_scenario_ambiguity`.
4. Whether 15-1876 ss.22-27 were amended after 1876. The corpus records no
   amendment events for them; this was not checked outside the corpus.

`validate_legal_map.py M106` prints OK with no errors and no warnings.
