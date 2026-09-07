# M083 research notes (statutory-qa-v1, status=unverified)

Matter: Paper 13 Q6(i), exam session October 2019. One Tier A question, marked
`enrich`, so enrichment was applied.

## Queries run

`acts`; `toc 1-1907`; `grep "secre|divulg|disclos" --act 1-1907`;
`show 1-1907/s31 --provisions` and `--full`; `show 1-1907/s34 --full`;
`show 1-1907/s43 --full`; `toc 31-2022`; `show 31-2022/s16 --full`;
`grep "rule \(1\)|rule \(24\)|divulge"` over 6-2024, 47-2011, 20-1976, 13-2013,
12-2005, 24-1973; `grep "codicil"` over the amendment Acts;
`search "secrecy of will notary disclose during lifetime of testator"`;
`grep "will" --act 23-1927`; `check` on all four excerpts.

## Alternatives rejected

- Wills Ordinance 21-1844 and Prevention of Frauds Ordinance 7-1840 ss.4 and 7:
  they govern how a will is executed and attested, not what a notary may say
  about one afterwards. Nothing there bears on disclosure.
- Registration of Documents Ordinance 23-1927 (ss.10, 26, 30, 35): a will
  enters the register only through probate or letters of administration, so it
  says nothing about the position while the testator is alive.
- The secrecy provisions in 53-1938 s61, 17-1979 s74 and 6-1990 s32 surfaced in
  the corpus-wide search. They bind bank and authority officers, not notaries.
- Rule (20)(h)(ii) of s.31 (deed register entry for a will, with the testator's
  name) was considered and left out: it is the notary's own record, not a
  disclosure rule, and including it would blur the point made by rule (24).

## Corpus gaps

Set out in full in `legal-map.json`. The one that matters: s.34 exists in the
corpus only in the text substituted by the Notaries (Amendment) Act No. 31 of
2022, later than the October 2019 matter date, so it is recorded as supporting
with `applicable_to_matter_date: false` and the answer does not rely on the
fine figure. Rule (1) of s.31 is untouched by every amendment Act in the
corpus, so the indispensable provision is safe at the matter date. The
Ordinance also leaves "employer", "secret" and "required to do so by law"
undefined; s.43 defines only three unrelated terms.

## For the verifier, in order

1. Whether "his employer" in rule (1) is properly read as the testator who
   instructed the notary. Nothing in the corpus defines it, and the whole
   answer turns on it.
2. Whether the duty covers the bare fact of attestation and not only the
   contents (claim CL-M083-Q01-008). This is inferential; rule (24) is offered
   as support, not as a direct statement.
3. The five added facts. Three are labelled `synthetic_decisive` because each
   closes off a route to lawful disclosure; check that none of them decides the
   question by assumption rather than by closing a statutory exception.
