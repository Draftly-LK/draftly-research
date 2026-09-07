# M025 research notes (status: unverified)

Both Tier A questions (M025-Q01 pedigree, M025-Q02 shares) are `keep`, so no
enrichment. Both are `statute_only` and drafted as `proposed_gold`.

## Queries tried

- `acts`, then `toc 15-1876`: Part III (ss.20-36) is the whole rule set needed.
- `show --full` on 15-1876 ss.20-36, s.2 and s.3.
- `grep "administrator'?s? conveyance" --act 2-1889` returned nothing; `grep
  "conveyance"` and `grep "heirs"` over the Civil Procedure Code led to ss.531
  and 724B, the closest corpus support for the testamentary step.
- `check` run on all twelve excerpts; each is verbatim. Validator prints OK
  with no warnings.

## Alternatives rejected

- Kandyan Succession Ordinance 23-1917, Muslim Intestate Succession Ordinance
  10-1931, Jaffna Matrimonial Rights and Inheritance Ordinance 1-1911: nothing
  brings any party under a special personal law, so 15-1876 s.2 leaves the
  general law in place.
- 15-1876 s.26 (both parents failing): at each death one parent is taken to be
  alive. Named in both conclusions as the alternative if that reading is wrong.
- 15-1876 s.35 (collation) and 5-2017 (gifts revoked for ingratitude) raise no
  issue on these facts.

## For the verifier, in order of risk

1. The background never states who the grantees of Administrator's Conveyance
   No.6231 are. The map reads it as a distribution to Kasun's intestate heirs.
2. The background never states that Namal Silva is the father of Sarathi and
   Amal, nor that he outlived her. Both are assumed, and this is the only open
   fact that moves a share: with it Namal takes 1/16 and Amal 5/16; without it
   Amal takes 3/8 and Namal nothing.
3. Excluding Sunil and Lalith from Kasun's estate turns entirely on the words
   "by the side of the deceased parent" in s.25.
4. Prevention of Frauds Ordinance s.2 is background only: the corpus text is
   the 2022/2024 version, later than the 2011 and 2014 deeds.
5. Corpus gaps are listed in `legal-map.json`; the Partition Law is the main
   one, but the allotment to Gamini Jayasinghe is a given fact.
