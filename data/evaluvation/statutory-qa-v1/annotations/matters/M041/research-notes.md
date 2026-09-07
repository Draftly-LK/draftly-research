# M041 research notes (status: unverified)

Paper 7 Q2, April 2023. Tier A: M041-Q01 only (M041-Q02 is Tier B, not
annotated). Validator: `OK errors=0 warnings=0`.

## Queries run

`acts`; `toc` on 1-1907, 38-2014, 7-2007; `show --provisions` and `--full` on
1-1907/s31; `show` on 1-1907/s37-s38, 7-2007/s18-s21, s92, s185, 38-2014/s2,
s4, s18, 1-1972/s3, s5, s8, s66, 7-1840/s2, 23-1927/s7, 12-2006/s3;
`defs 1-1972`; searches for "agricultural land ceiling company", "major
transaction assets", "common seal contracts company", "restriction transfer of
land company shareholding", "execution of deeds by company signature seal
attorney"; `grep "deed .{0,80}(company|corporate)" --act 7-2007`.

## Temporal work (check this first)

The corpus holds consolidated text that already includes 2024 amendments, but
the matter date is April 2023, so I dated each quoted rule against the
as-enacted `31-2022/s16`, `6-2024/s3` and `4-2024/s2`. Traps avoided:

- Prevention of Frauds Ordinance s.2(2) (transferee signs; corporate board may
  authorise a signatory) came only from Act No. 4 of 2024. The excerpt is
  confined to the 1840 opening words.
- Notaries Ordinance s.31 rule (7A)(a) reads "every deed or instrument" only
  since Act No. 6 of 2024; in April 2023 it covered a transfer, gift or
  exchange. I used rule (6), untouched in 2024, instead.
- Rules (14), (16)(a), (17)(b)(i), (17)(d) come from Act No. 31 of 2022 and
  were in force; rule (30A) from Act No. 47 of 2011.

## Rejected alternatives

Tea and Rubber Estates (Control of Fragmentation) Act (tea and rubber only,
not coconut); Land Development Ordinance alienation limits (nothing suggests a
State grant, and I would not invent one); Companies Act s.20 and s.21
(redundant once s.19(1)(a) plus a board resolution are in the map);
Registration of Title Act (Kuliyapitiya not stated to be a declared area);
Survey Act (a surveyor's plan is a practical need, not a notarial duty).

## Gaps

See `corpus_gaps` in `legal-map.json`. The two that bite hardest are the
missing stamp duty rate order and the loss of defined-term labels in Land
Reform Law s.66, where the definition of agricultural land had to be located
by position rather than by its label.
