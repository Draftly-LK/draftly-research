# M100 research notes (statutory-qa-v1, status=unverified)

One Tier A question, M100-Q01, October 2018 session: what precautions a notary
should take about witnesses when a testator executes a last will. Classified
`enrich`, so the background was enriched.

## Queries tried

`acts`; `toc` on 1-1907, 7-1840, 21-1844; `search "witnesses to last will
attestation notary" -k 20`, which surfaced s.31 rule (9) and Prevention of
Frauds s.4; `show 1-1907/s31 --full` and `--provisions` to read every rule;
`show` on 1-1907 s.32, s.33, s.34, s.39 and on 7-1840 s.4, s.7, s.9 to s.13;
`edges 1-1907/s31`; `defs 1-1907` and `defs 7-1840` (no relevant defined
terms); `show 31-2022/s16`, `6-2024/s3`, `30-2022/s3`, `30-2022/s4` to work
out the 2018 wording of section 31 and of section 4.

## Alternatives rejected

- Wills Ordinance No. 21 of 1844: its corpus text has no witness provision
  (sections 1, 2, 5 to 9 only), so it adds nothing.
- Section 31 rule (15), on marks and foreign-language signatures: rule (8)
  already requires witnesses to subscribe in letters.
- Section 31 rule (22) and rule (36)(c): not about witnesses.
- Section 34 penalties: the offence that bears on witness presence is s.39(c),
  which is recorded instead.

## Corpus gaps, and what the verifier should look at first

1. Rule (10) of section 31 was in force in October 2018 and was repealed by
   Act No. 6 of 2024 s.3(4). It is missing from the consolidated corpus text
   and its content is unrecoverable, yet it sat among the witness rules, so
   completeness cannot be guaranteed from the corpus. Check this first against
   a 2018 print of the Ordinance.
2. Rule (9) is indispensable, but its 2018 opening words come from the
   amending Acts (PROV-M100-017, PROV-M100-018), not the consolidated text.
   The reading adopted is that at the matter date the vetting duty attached in
   terms to the case where the notary relied on the witnesses' knowledge of
   the executant. The Notary here knows the testator, so that reading matters.
3. Prevention of Frauds s.4 and section 31 rule (14) carry
   `applicable_to_matter_date: false`: both were substituted after the matter
   date and the earlier wording is not in the corpus.
4. Witness competency as such (age, disability, relationship short of taking a
   benefit) is nowhere in the corpus; s.10 assumes it.

Validator: `M100: OK errors=0 warnings=0`.
