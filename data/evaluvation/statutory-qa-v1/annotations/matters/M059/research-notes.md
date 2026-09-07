# M059 research notes (statutory-qa-v1)

Status: `unverified`. One Tier A question (M059-Q01, `keep`, 2 marks).
Matter reference date 2021-10.

## Queries tried

- `acts` to confirm the Mortgage Act is in the corpus as `6-1949` (126 sections).
- `toc 6-1949 | grep 47` located `6-1949/s47A`; a `grep "47A|47\(A\)" --act 6-1949`
  over section bodies returned no match, so the section is reachable only by
  its heading/TOC, not by a body reference to its own number.
- `show --full` on `6-1949/s47A`, `6-1949/s46`, `6-1949/s47`, `2-1889/s218`.
- `edges 6-1949/s47A` and `edges 6-1949/s46` for the cross-reference chain.
- `defs 6-1949` to check whether "lending institution" is defined in s.2. It is
  not; the definition is internal to s.47A(7), which is why that subsection is
  recorded as a separate provision entry rather than pulled from s.2.

## Alternatives rejected

- Mortgage Act s.2 definitions ("mortgage", "hypothecary action"). The corpus
  graph links s.47A and s.46 to s.2, but the answer does not turn on either
  defined term, so they were left out rather than padded in as background.
- Mortgage Act s.69 (instruments attested by an officer of a lending
  institution). Relevant only through s.47A(5), and nothing in the facts says
  the bond will be attested by a bank officer rather than a notary.
- Companies Act ss.437 and 439, which also cross-reference s.46, are about
  companies and do not touch an individual mortgagor.
- No stamp-duty provision was recorded even though s.47A(4) exempts the further
  instrument; the question asks why the Bank wants the declaration, not what it
  costs.

## Corpus gaps

- National Savings Bank Act No. 30 of 1971 is not in the corpus; the Bank's
  status rests on the express naming in s.47A(7)(d).
- Mortgage (Amendment) Act No. 3 of 1990 is not a separate corpus document.
  Its insertion of s.47A and substitution of s.46 is visible only as
  `amendment_events` on the consolidated sections.
- Nothing in the corpus confirms whether the Rs.150,000 threshold in s.47A(1)
  has ever been revised. No later amendment event is recorded, but absence of a
  document is not proof.

## For the verifier

1. Check the threshold point first: the whole answer assumes Rs.150,000 was
   still the figure in October 2021.
2. The s.47A(1) excerpt reproduces printed oddities ("subject To",
   "subsection(2)"); this is corpus text, not a transcription slip here.
3. Hop count is recorded as 3 (s.46 -> s.47A(1) -> s.47A(7) gateway). A verifier
   who treats the "lending institution" definition as part of the same hop would
   land on 2.
