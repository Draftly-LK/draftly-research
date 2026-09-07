# M097 research notes (statutory-qa-v1, unverified)

Matter: deed of gift subject to the donor's life interest over 30 perches at
Battaramulla with one house, to three sons; one wants to sell out and buy a
Colombo apartment, one wants a housing loan and his own house, one wants to
live in the existing house. One Tier A question, `candidate_action = keep`,
so no enrichment.

## Queries tried

`acts` (full list), then `search` on: partition of land among co-owners; life
interest; undivided share co-owner sale; deed of gift; notarially executed
deed transfer of land void; mortgage bond immovable property; condominium
parcel transfer apartment; registration of instrument priority; subdivision of
land approval local authority (also `--act 41-1978`). `toc 11-1973`,
`defs 6-1949`, `grep "minimum extent"`, and `show --full` on 7-1840/s2,
23-1927/s7, 23-1927/s8, 11-1973/s2, s4, s9, s10, s23, 6-1949/s2, 6-1949/s3,
21-1998/s54. All nine excerpts confirmed with `check`.

## Why the question is blocked

The Partition Law No. 21 of 1977 is not in the corpus; the only trace of it is
Apartment Ownership Law s.23, which disapplies it to registered condominium
plans. The law of usufruct (what the sons may do while the father's life
interest subsists) and the law of co-ownership (sale of an undivided share,
building on common land) are Roman-Dutch and non-statutory. Battaramulla
subdivision controls are absent too, which matters because 30 perches split
three ways is close to the practical minimum. So `mixed_statute_and_case` and
`blocked_missing_authority`, with no indispensable provisions and hop count 0.

## Alternatives rejected

* Registration of Title Act ss.24, 54 (prescribed minimum extent) — that Act
  applies only in declared title settlement areas; nothing places Battaramulla
  in one, so it would have been speculative.
* Tea and Rubber Estates (Control of Fragmentation) Act s.4 (partition by deed
  of co-owners) — ranked first on the partition query but is confined to tea
  and rubber estates; not a residential 30-perch block.
* Revocation of Irrevocable Deeds of Gift Act No. 5 of 2017 — no ingratitude
  or revocation issue on these facts.
* Urban Development Authority Law ss.8D-8J — development plans and permits,
  not lot-size or subdivision approval for a private partition.

## For the verifier first

1. PROV-M097-008 (Mortgage Act s.2): the corpus body of that interpretation
   section has lost its defined terms, so the excerpt reads as a bare
   "includes" clause. Confirm from source that it is the definition of "land".
   It is recorded as background only.
2. PROV-M097-001 (Prevention of Frauds s.2): the corpus body is the post-2024
   consolidated text. The excerpt is the opening words of subsection (1),
   which predate the 2022 and 2024 amendments, but paragraphs (a) and (b) of
   that subsection must not be applied to an October 2018 matter.
3. Confirm the blocked call rather than the provision list. If a verifier
   thinks the expected answer is purely "release the life interest, then
   partition", the corpus still cannot support it.
