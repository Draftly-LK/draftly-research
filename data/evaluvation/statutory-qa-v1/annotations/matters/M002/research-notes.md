# M002 research notes (status: unverified)

Sea View Company (Pvt) Ltd buying seafront land in Galle for a hotel. Tier A
parts annotated: Q01, Q02, Q03. Q04 is Tier B and was not touched.

## Queries tried

- `show 1-1907/s31 --full` for the notary's duties; `toc 23-1927` plus `show`
  on s.7, s.11, s.13, s.30, s.32, s.42 for the registry side.
- `toc 38-2014`, `defs 38-2014`, `show` s.2, s.4, s.18, s.25 for the
  foreign-shareholding restriction on transfers to a Sri Lankan company.
- `toc 4-1902`, `show` s.3 and s.3B for execution by attorney; `search
  "certificate of incorporation conclusive evidence" --act 7-2007`.
- `search "coastal zone development permit"`, `grep "coast"` — nothing on point.
- `toc 12-2006`, `toc 43-1982`, `grep "prescribed rate"`, `show 43-1982/s67` —
  no stamp duty rate anywhere in the corpus.

## Alternatives rejected

- Land Reform Law No. 1 of 1972 ceilings: seafront hotel land, not stated to be
  agricultural; nothing engages the ceiling.
- Street lines under Municipal Councils Ordinance s.69/s.70 and Urban Councils
  Ordinance s.74: the certificate regime sits in the Housing and Town
  Improvement Ordinance, which is absent.
- Survey Act No. 17 of 2002 imposes no pre-purchase check, so the survey plan
  is grounded on Notaries Ordinance s.31 rule (16)(a) and Registration of
  Documents Ordinance s.13(1) instead.
- Registration of Title Act No. 21 of 1998: no fact places this land under it.

## Corpus gaps

Listed in `corpus_gaps`. Blocking two: no coastal zone enactment (Q02); no
stamp duty rate schedule or Order and no Southern Province statute (Q03).

## For the verifier, first

1. Whether Q01 is properly `statute_only`; a lawyer may say a complete answer
   needs conveyancing practice (tracing thirty years of title), not statute.
2. Subsection labels on the seven Notaries Ordinance s.31 provisions: the
   corpus body drops the rule numbers for rules (16), (17) and (26), so the
   labels follow conventional numbering and are not machine-checkable.
3. Excerpts for `23-1927/s11` and `23-1927/s32` start mid-sentence to avoid an
   OCR artefact ("No Us pendens") and a quoted-term clause.
4. Whether Q02 should be `reserved`, and whether Urban Development Authority
   Law s.8J belongs there even as background. Q02 and Q03 carry
   `enrichment.applied: false` because both are blocked.

`validate_legal_map.py M002` prints OK with no warnings.
