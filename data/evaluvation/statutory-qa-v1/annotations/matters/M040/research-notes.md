# M040 research notes (statutory-qa-v1, status=unverified)

Matter: Paper 7 Q1, exam session April 2023. Two Tier A parts, both `keep`, so
no enrichment was applied. Both are `reserved` as `mixed_statute_and_case`.

## Queries run

`acts`; `toc 15-1876`; `show --full` on 15-1876 s20 to s36 and on s2, s3;
`show --full` on 7-1840 s2 and 5-2017 s2; `edges` on 15-1876 s22, s24, s25;
`defs 15-1876`; `search "partition final decree conclusive title"`;
`search "life interest usufruct reserved donor"`; `grep "life interest"`;
`grep "donat"`; `grep "deed of gift"`;
`search "gift of immovable property notarially executed donee accepts"`;
`check` on all thirteen excerpts, all verbatim.

## Alternatives rejected

- Kandyan Succession Ordinance 23-1917, Jaffna Matrimonial Rights and
  Inheritance Ordinance 1-1911, Muslim Intestate Succession Ordinance 10-1931:
  nothing in the scenario points to any personal law, so the general law in
  15-1876 was used. 15-1876 s2 is carried as background for that assumption.
- Revocation of Irrevocable Deeds of Gift Act 5-2017: it deals with revocation
  by court order for gross ingratitude. No ingratitude facts, and the Act
  postdates the 2002 deed.
- 15-1876 s26, s28, s29: all presuppose that both parents have failed. Thilaka
  and Roshini each survived the relevant intestate, so s25 governs instead.
- 15-1876 s35 (collation): the gift was to Pethum, and no heir is claiming
  against a parent's estate, so collation is not in issue.
- Notaries Ordinance 1-1907 s31: attestation rules, not devolution.

## Corpus gaps

Listed in full in `legal-map.json`. The ones that matter: nothing in the
corpus states that a deed of gift passes dominium or that a reserved life
interest falls in on the holder's death, and the Partition Law is absent. That
is why both parts are `reserved` rather than `proposed_gold`.

## For the verifier, in order

1. The s27 question. The map applies the full-blood preference in s27 to the
   sibling portion created by s25, following matter M001, giving Kalum and
   Shanthi 3/32 each and Sadun's line 1/32. s27 is textually placed after s26,
   which deals with both parents failing, so a narrower reading is arguable; on
   that reading all four siblings take 1/16 each. This is the weakest link.
2. The arithmetic. Sadana 1/2, Thilaka 1/4, Kalum 3/32, Shanthi 3/32, Nadun
   1/32, Roshini 1/32, summing to unity, with Thilaka also holding the
   reserved life interest over the whole land.
3. Whether Thilaka is assumed alive. The background never says she died, so
   her life interest is treated as still running and she is listed as an owner.
4. Whether the Q01 pedigree answer should be `proposed_gold` on the footing
   that the gift and life interest are recited facts rather than legal steps.
   The same call was flagged in M001.
