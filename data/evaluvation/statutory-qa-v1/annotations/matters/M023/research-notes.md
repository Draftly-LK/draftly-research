# M023 research notes (status=unverified)

Matter: Paper 3 Q1, April 2025. Lot 1 (40 perches, Battaramulla), three
successive intestacies. Both Tier A questions are `keep`, so no enrichment.

## Queries tried

- `acts` to find the succession statutes. Corpus holds three: Matrimonial
  Rights and Inheritance Ordinance 15-1876 (general law), Jaffna Matrimonial
  Rights and Inheritance Ordinance 1-1911, Kandyan Succession Ordinance
  23-1917, Muslim Intestate Succession Ordinance 10-1931.
- `toc 15-1876`, then `show --full` on ss.20-30, 35 and 36.
- `grep "life interest"`, `grep "usufruct"`, `grep "irrevocab"` — nothing
  usable; hits are Land Reform Law ceiling provisions, Registration of Title
  Act s.46, and Act 5-2017 on revocation for gross ingratitude.
- `search "partition final decree conclusive title"` — no Partition Law in the
  corpus.
- `toc 21-1844` (Wills Ordinance) — nothing that presumes intestacy.
- `check` run on all 13 excerpts; all confirmed verbatim.
- `edges` on 15-1876/s22 and s25 returned no typed links, so the reasoning
  edges in the map are hand-built, not corpus-derived.

## Alternatives rejected

- Jaffna, Kandyan and Muslim succession statutes: no fact points to
  Thesawalamai, Kandyan or Muslim law, so the general law applies.
- 15-1876/s27 (half-blood division) and s.28: neither governs Anusha's estate,
  because she left no full siblings. s.27 is kept as `supporting` to record
  that it was considered; s.28 needs half-siblings on both sides.
- 15-1876/s35 (collation): could matter between Kapila and Mithila in Mahesh's
  estate, but the question is about title to this land only, which Mahesh had
  already gifted away.
- 7-1840/s2 kept as background only. Its consolidated text carries 2022 and
  2024 amendment events and does not state the 2006 wording.

## Corpus gaps

Partition Law absent; no provision on a donor's reserved life interest; no
presumption of intestacy. See `corpus_gaps` in the map.

## For the verifier, first

1. The Q01 / Q02 split. Q01 (pedigree) is `reserved` as
   `mixed_statute_and_case` because two links, the partition decree and the
   deed of gift with a reserved life interest, have no support in this corpus.
   Q02 (shares) is `proposed_gold` because it treats Kapila's ownership of the
   entirety as a fact given in the background. Confirm that split is the right
   call rather than reserving both.
2. Two assumptions the facts do not state: that Anusha and Prema each died
   intestate, and that no ascendant on Sandya's side survived Anusha (the
   s.29 exception). Both are stated in the Q02 conclusion.
3. The arithmetic: Champa 55/96, Rupa 35/192, Seetha 35/192,
   Hasitha Perera 1/16. Totals 192/192.
4. Malani (Kapila's mother) is a paternal ascendant of Anusha, so she is on
   the same side as the half-sisters and does not trigger the s.29 exception.
   Worth a second look.

`validate_legal_map.py M023` prints OK with no warnings.
