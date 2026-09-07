# M088 research notes

Two-year lease of an upstair floor at Nawala Road, Rajagiriya, April 2019
session. Four Tier A questions, all `keep`, so no enrichment was applied.

## Queries tried

- `acts` for the stamp duty statutes: 12-2006, 43-1982, provincial 6-1990.
- `toc 12-2006`, then `show --full` on s.3, s.4, s.5, s.6, s.8, s.9, s.13.
- `toc 6-1990` and `show --full` on s.37, s.40, s.51, s.76.
- `grep "lease" --act 43-1982` and `grep "[Ll]ease" --act 6-1990` looking for a
  lease rate or schedule; nothing on rates came back.
- corpus-wide `grep` for `reddendum`, `habendum`, `covenant of the lessee`: no
  match. `sublet` matches only 37-1954/s91A and 8-1947/s53, neither relevant.
- `show 7-1840/s2 --full` and `show 1-1907/s31 --full` for the notarial frame.
- `check` on all nine excerpts; each returned OK.

## Alternatives rejected

- Stamp Duty Act No. 43 of 1982: its imposition provisions are displaced for a
  lease by s.13 of Act No. 12 of 2006, so its s.19 and s.24 were not used.
- Western Province Financial Statute s.37 charges transfers of immovable
  property, court documents and motor vehicle transfers, not leases, so it is
  background rather than the charging provision.
- Notaries Ordinance s.31 was read and set aside: it carries many 2011, 2022 and
  2024 amendment events, so the consolidated text is unsafe for a 2019 matter,
  and none of its rules bears on covenant or reddendum content.

## Corpus gaps

- No Gazette Order under s.3(1) fixing the lease rate, and no rule on the
  chargeable amount. This is what blocks Q01.
- List I of the Ninth Schedule to the Constitution, referred to in s.9, is
  absent, so the Provincial Council limb of Q02 is stated as qualified.
- Regulations prescribing banks and the certificate form under s.8(2) and s.12.
- Nothing on conveyancing clause content, hence Q03 and Q04 are reserved.

## For the verifier, first

1. Q02 claim CL-M088-Q02-008 (Western Provincial Council) is inferential and
   rests on a Ninth Schedule step that cannot be closed inside the corpus.
2. PROV-M088-009 quotes 7-1840/s2, whose consolidated text carries 2022 and 2024
   material; the quoted words predate that, but confirm the April 2019 wording.
3. PROV-M088-008 quotes a garbled paragraph (a) of 6-1990/s37 verbatim from the
   corpus; check it against the Gazette.
