# M112 research notes (statutory-qa-v1, unverified)

Notary in Colombo asked to attest a transfer of Matara land worth
Rs.1,000,000. Reference date 2018-04. Four Tier A questions, all `enrich`.

## Queries tried

`acts`; `toc 1-1907`; `show 1-1907/s31 --full`/`--provisions`; `grep "district
in which he resides"`; `toc`/`show` on 31-2022 s16, 6-2024 s3, 47-2011 s2 and
s3, 13-2013 to date the s.31 rules; `show` on 1-1907 s4A, s9, s10, s32, s34,
s37, s43; `edges 1-1907/s31`; `toc 12-2006`, `toc 43-1982`; `show` on 12-2006
s3, s4, s6, s8, s9, s13, s14 and 43-1982 s2, s6, s15, s24, s58, s69; `grep
"per centum" --act 43-1982`; `search "stamp duty on transfer of immovable
property provincial council"`; `show 6-1990` s37, s40, s43(a). Every excerpt
confirmed with `check`.

## Alternatives rejected

* Reading rule (22) as a bar on attesting deeds for out-of-district land. It
  speaks of the area in which the notary attests; rule (29) exists precisely
  because he may attest such deeds.
* s.31 rule (7A) and rule (30A) for Q03/Q04: both were inserted in 2022 and
  were not in force in April 2018.
* Western Province Financial Statute No. 6 of 1990 as a source of rate or
  payment office: its s.37 reaches only Western Province land.
* Answering Q03 with a computed figure. No rate order is in the corpus and
  none was quoted from memory.

## Corpus gaps

Rate order or regulation under 43-1982 s.2 and s.69 (and 12-2006 s.3); the
Southern Province finance statute; the Constitution (Ninth Schedule List I);
Form F/F 1 of the Notaries Ordinance Second Schedule; the pre-2022 s.34 text.

## For the verifier, first

1. Rule numbering in the consolidated s.31 body. The monthly-return rule is
   printed unnumbered; it is treated as rule (26) on the strength of s.32(1),
   s.34(2) and Act No. 47 of 2011 s.3. The corpus also records rule (26) as
   repealed in 2022 while still carrying its text. Neither point affects 2018.
2. PROV-M112-009 (s.34) is `applicable_to_matter_date: false` because only the
   2022 replacement is in the corpus. It supports only the proposition that a
   s.31 breach is an offence; the fifty thousand rupee figure is not relied on.
3. Q02 deadline is read as the fifteenth of the month following execution.
4. Whether Q04 is over-blocked: many would read the property-situated limb of
   12-2006 s.9 as governing, but that reading needs the Ninth Schedule.

`validate_legal_map.py M112` prints OK, no errors, no warnings.
