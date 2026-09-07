# M057 research notes (status=unverified)

One Tier A question (M057-Q01, `keep`, 2 marks): liabilities of a notary who
attested a four-year lease without the yearly certificate. Matter date 2021-10.

Background labels: `BG-1` = Kamal Ratnayake, a notary practising in Galle,
attested the four-year lease of Sudath Gunawardana's commercial building;
`BG-2` = he had no yearly certificate from the Registrar of the High Court for
the current year when he did so.

## Queries tried

- `acts`, then `toc 1-1907`; `grep "certificate" --act 1-1907`, which surfaced
  s.3, s.23, s.27, s.28, s.29, s.30, s.31.
- `show --full` on s.13, s.21, s.27, s.28, s.30, s.33, s.35, s.43, `7-1840/s2`.
- `edges` on s.27 and s.30, then `show 13-2013/s2`, `show 31-2022/s14`,
  `toc 12-2005` to date the amendments.
- `check` confirmed all six excerpts verbatim.

## Alternatives rejected

- **s.13** (practising without a warrant): background only. He holds a warrant;
  what is missing is the annual practising certificate, so s.30 is the offence.
  Worth a look, since answers to this question sometimes reach for s.13.
- **s.28** and **s.29**: not engaged. He never applied, and the Registrar never
  refused. s.28 was also substituted by Act No. 6 of 2024, after the matter date.
- **s.33** and **s.34**: both concern the form rules in s.31, not a want of
  certificate.
- **Validity of the lease** was left out of the gold answer. The Ordinance
  nowhere avoids a deed for want of a certificate, but reasoning from that
  silence to a valid lease would need judicial authority, and the question asks
  about liabilities only.

## For the verifier

1. s.27(2) reads "April" in the corpus because of Act No. 31 of 2022 s.14; at
   2021-10 it read "March". Nothing in the answer turns on the month.
2. s.21 and `7-1840/s2` are consolidated texts carrying post-2021 amendments,
   which is why both are supporting rather than indispensable.
3. Validation prints OK with no warnings.
