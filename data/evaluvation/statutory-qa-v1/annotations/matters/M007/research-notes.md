# M007 research notes (status=unverified)

Paper 1, Q5(iii), April 2026. One Tier A question, M007-Q01, `enrich`.
Proposed gold, `statute_only`, 6 provisions, hop count 3. Validator: OK, no
warnings.

## Queries tried

- `acts`; `toc 1-1907`; `show 1-1907/s31 --full` (25,684 chars) to read every
  rule; `show` on 1-1907/s32, s33, s34, s43 and 7-1840/s2; `toc 7-1840`.
- `grep "invalid" --act 1-1907` returns only s.33, confirming the Ordinance
  nowhere else speaks to the standing of an instrument.
- `edges 1-1907/s33` gives one link, `cross_references` to s.31. The route
  from the s.33 proviso out to the Prevention of Frauds Ordinance is not in
  the graph; it was found by reading the proviso.
- `check` on all six excerpts; all verbatim.

## Alternatives rejected

- s.32 disapplies certain rules for powers of attorney used abroad, foreign
  property and stock transfers; none fits a Colombo transfer.
- Prevention of Frauds Ordinance s.2(2)(a) (2024) requires the transferee to
  sign and give a thumb impression, with a proviso for a corporate transferee.
  A second decisive defect could have been built on it, but one clean breach
  of the presence requirement suits a 3-mark answer.
- s.31 rule (13), notary not to attest a deed to which he is a party: Saman is
  the transferee's legal officer, not a party.
- s.31 rule (22) is background only; the added facts put the attestation at
  his own Colombo office, inside his zone, closing the point.

## Corpus gaps

- "Matter of form" is undefined in s.33 and the corpus holds no case law. The
  enrichment sidesteps this by making the decisive defect an express failure
  of the s.2(1)(a) condition, which the s.33 proviso reaches on its own words.
- Nothing covers a third party who buys on the faith of a defective deed.

## For the verifier, in order

1. Whether `statute_only` holds. The form limb rests on rule (17)(c), which
   plainly touches only the face of the deed; if labelling any section 31
   default a matter of form needs judicial authority, drop to
   `mixed_statute_and_case`.
2. Whether the s.2(1)(a) consequence is better put as "not in force or
   availing in law" than "invalid". The draft uses the statutory words.
3. FACT-M007-Q01-003 and -004 are the two decisive additions; the rest of the
   enriched background is neutral.
4. PROV-M007-004's excerpt starts mid-sentence at "shall be in force or avail
   in law unless"; that is how the corpus body reads, and it keeps the excerpt
   inside the length limit.
