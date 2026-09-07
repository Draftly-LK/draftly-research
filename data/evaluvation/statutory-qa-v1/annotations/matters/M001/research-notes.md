# M001 research notes (statutory-qa-v1, status=unverified)

Matter: Paper 1 Q1, exam session April 2026. Three Tier A parts, all `keep`,
so no enrichment was applied.

## Queries run

`acts`; `toc 15-1876`; `toc 38-2014`; `toc 21-2018`; `toc 5-2017`;
`show --full` on 15-1876 s3, s20-s27, s35, s36, on 7-1840 s2, on 38-2014 s1,
s2, s3, s18, s20, s25, and on 21-2018 s1, s2 and 3-2017 s2;
`edges 38-2014/s3`; `search "life interest usufruct"`; `grep "usufruct"`;
`grep "life interest"`; `check` on the section 3(1)(d) and section 27
excerpts.

## Alternatives rejected

- Kandyan Succession Ordinance 23-1917, Jaffna Matrimonial Rights and
  Inheritance Ordinance 1-1911 and Muslim Intestate Succession Ordinance
  10-1931: nothing in the scenario points to any personal law, so the general
  law in 15-1876 was used. A verifier should confirm that reading first.
- Revocation of Irrevocable Deeds of Gift Act 5-2017: it deals with revocation
  of a gift by a court for gross ingratitude. Deed No. 525 of 1991 is a
  renunciation of Vinitha's own life interest, not a revocation of the gift,
  and the Act postdates it.
- 15-1876 s33 (illegitimate children): Samantha is described as a child of a
  first marriage, so s24 applies directly.
- Land Reform Law 1-1972 and Registration of Title Act 21-1998 s46 mention
  life interests but neither states when a life interest ends.

## Corpus gaps

Listed in full in `legal-map.json`. The two that matter: no provision anywhere
in the corpus governs the extinction or renunciation of a life interest, which
is why Q01 is `reserved` as `mixed_statute_and_case`; and the corpus text of
38-2014 s3(1)(d) has words missing after "of the", while 21-2018 s2 is
truncated and does not reproduce the substituted paragraph (b) or the new
paragraph (i).

## For the verifier, in order

1. The arithmetic in Q02. Kanthi 123/192 (41/64), Ann 16/192 (1/12), Samantha
   53/192. The contested step is Rakitha's estate: s25 puts the half-blood
   sister Samantha in the sibling class because she is related through the
   deceased parent Suresh, and s27 then gives the full sister Muditha 3/4 of
   the sibling portion and Samantha 1/4.
2. Muditha's estate. Rakitha predeceased her without issue, so no full-blood
   sibling or issue survived to take the first half under s27 and the whole
   sibling portion went to Samantha. This reading of s27 where no full sibling
   survives is the weakest link in the chain.
3. Two facts assumed, not stated: that Rakitha died without issue, and that
   Kanthi is still living. Both are flagged in the Q02 conclusion.
4. Whether Q01 should instead be `proposed_gold`. The call turns on treating
   the life interest steps as indispensable to a pedigree rather than as
   background recited in the scenario.
