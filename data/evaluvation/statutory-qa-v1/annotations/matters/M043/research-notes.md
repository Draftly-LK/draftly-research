# M043 research notes (status=unverified)

Both Tier A questions (M043-Q01 pedigree, M043-Q02 shares) run on one fact
pattern, so they share the same provision set and reasoning edges.

## Queries tried

- `acts` to find the succession statutes. Candidates were 15-1876 (general
  law), 1-1911 (Jaffna), 23-1917 (Kandyan), 10-1931 (Muslim).
- `toc 15-1876`, then `show --full` on ss.20-32 and s.36, plus s.3 for the
  definitions and `defs 15-1876`.
- `grep "life interest"`, `grep "usufruct"`, `grep "gift"` across the whole
  corpus.
- `search "letters of administration intestate estate vest heirs"` for the
  testamentary case.
- `edges 15-1876/s25` returned nothing in either direction, so the s.25 to
  s.27 and s.25 to s.30 links in the map are mine, not the graph's.

## Alternatives rejected

- Jaffna (1-1911), Kandyan (23-1917) and Muslim (10-1931) succession: nothing
  in the scenario points to Thesawalamai, Kandyan law or Muslim law. Property
  is at Battaramulla and the general law applies.
- Prevention of Frauds s.2: the deed of gift is stated to be notarially
  attested, so execution is not in issue, and the consolidated corpus text
  carries 2022 and 2024 amendments that postdate the 2002 deed.
- Revocation of Irrevocable Deeds of Gift Act No. 5 of 2017: no ingratitude
  facts, and it postdates the gift and the donor's death.

## What the verifier should look at first

1. The s.25 sibling half. Section 25 does not say how the full and paternal
   half-siblings divide it. The draft applies s.30 per capita (1/8 each to
   Aruna, Leela, Nikitha, Rikitha). The competing reading applies the s.27
   proportions, giving 3/16, 3/16, 1/16, 1/16. Every later figure turns on
   this. This is the single most load-bearing choice in the map.
2. Whether Anusha survived Rikitha (02.08.2016). The background is silent.
   The draft assumes she did not, so ss.26-27 govern. If she survived, s.25
   applies and Anusha takes 1/32.
3. The root of the pedigree. That Nihal kept only a life interest after Deed
   of Gift No. 663, and that a life interest is not inheritable, is
   Roman-Dutch law reached through s.36, not a corpus provision. This is why
   both questions are `mixed_statute_and_case` and `reserved`.

## Notes

- The corpus body of 15-1876/s26 reads "balf-blood". The excerpt is quoted
  verbatim as required, so the typo is reproduced in the map.
- The validator prints OK with no warnings.
