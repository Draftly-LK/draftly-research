# M048 research notes (status=unverified)

Paper 9 question 1, parts 01 and 02. Both Tier A, both `keep`, so no enrichment.
Reference date 2021-10.

## Queries run

`acts`; `toc 15-1876`; `show --full` on 15-1876 ss 2, 3, 20-32, 36;
`search "life interest" -k 12`; `search "administration of estate vests in
administrator heirs" --act 2-1889`; `grep "vest(ed|s)? in the
(executor|administrator|heirs)" --act 2-1889` (no match);
`grep "heirs of the deceased" --act 2-1889`; `show 7-1840/s2 --full`;
`check` on all eleven excerpts, all OK verbatim.

## Alternatives rejected

- Jaffna MRIO 1-1911, Kandyan Succession 23-1917, Muslim Intestate Succession
  10-1931: excluded by 15-1876/s2 on the assumption the family is under the
  general law. The facts never say so, so it is recorded as an assumption.
- Prevention of Frauds 7-1840/s2: its list does not name a gift, and the corpus
  text carries amendment events dated 2022 and 2024, after the reference date.
- Civil Procedure Code testamentary provisions (ss 521-554), searched because of
  case 4620/T: nothing there makes a grant of letters change who inherits;
  s 531 only makes a certificate of heirship proof of the heirs.
- Revocation of Irrevocable Deeds of Gift Act 5-2017: no ingratitude facts, and
  it post-dates the deed.

## Corpus gaps

1. Nothing governs a life interest reserved by a donor on a deed of gift or its
   determination on the donor's death. That is link 2 of the pedigree.
2. Nothing states that a building accedes to the land; 15-1876/s3 only makes
   things attached to the earth "immovable property" for that Ordinance.
3. 15-1876/s25 does not say how the collateral half divides between full-blood
   and half-blood siblings. s 27 states a full-blood preference but sits after
   s 26 (both parents failing); s 30 directs per capita "except when otherwise
   expressly provided". The readings give different fractions.
4. 15-1876/s3 has lost its defined-term labels in the corpus; the excerpt taken
   is the "immovable property" definition and should be checked against source.

## For the verifier, first

Both questions are `reserved` / `mixed_statute_and_case`; gap 3 is the point to
test first. The fractions offered (Nishi 1/2, Kanthi 7/24, Dushani 5/48, Minoli
5/48) sum to unity; check the 2009 and 2010 rounds separately. Facts the paper
leaves open: personal law; whether Minoli was living in 2009 and 2010; whether
Nishantha's earlier marriage ended by death or divorce. The validator prints OK
with no warnings.
