# M009 research notes (statutory-qa-v1, unverified)

One Tier A question, M009-Q01 (Paper 1, Q6(iii), 4 marks): is registration
under the Registration of Title Act mandatory, and within how many days must an
instrument be forwarded for registration.

## Queries tried

- `acts` to locate the Act (21-1998, 75 sections), then `toc 21-1998`.
- `show --full` on 21-1998 ss.5, 10, 28, 37, 38, 39, 40, 41, 43, 44, 45, 49, 57,
  64, 75.
- `edges 21-1998/s45` (cross-reference to s.44, definition link to s.75).
- `grep "working days" --act 21-1998` and `grep "thirty days"` corpus-wide.
- `search "instrument forwarded registration days notary"` to surface the
  competing deeds-system rule, Notaries Ordinance s.31(30A).

## Alternatives rejected

- Notaries Ordinance s.31(30A) (thirty days, sixty outside the zone) as the
  operative rule: it belongs to the deeds system, and s.28 closes the Land
  Registers to parcels on the Title Register. Kept as a supporting contrast,
  because a wrong answer to this question will usually be "thirty days".
- Registration of Documents Ordinance s.26 (who may present): same reason.
- RTA s.57 (Prescription Ordinance disapplied) and s.31: relevant to Kamal's
  prescriptive occupation and to first registration, not to this question.
- Registration of Documents (Amendment) Acts: none touch the RTA.

## Corpus gaps

1. **s.45(1)(a) is textually damaged.** The body reads "shall be forwarded by
   the Attestor working days of such attestation" — the numeral is missing. The
   same gap is in the source JSON (LankaLaw edition), so it is a transcription
   defect, not an amendment. The only in-corpus number is the section heading,
   "Attestor to forward instruments attested within seven days." Because the
   question asks for the number of days, the question is recorded as
   `blocked_missing_authority` rather than `proposed_gold`.
2. s.75 lost its defined-term labels; "instrument" is matched to the first
   "means ..." clause by the order of the corpus `defined_terms` list.
3. The "prescribed penalty" under s.45(1)(b) lives in regulations under s.67,
   which are not in the corpus.

## For the verifier, first

Confirm the missing numeral in s.45(1)(a) against a Government Printer edition.
If it is "seven working days", the block clears and everything else in the map
stands as drafted. Second, confirm the s.75 definition mapping. Third, check
that Notaries (Amendment) Act No. 6 of 2024 did not alter s.31(30A). The
enrichment turns on one decisive assumption — that the Homagama parcel was
already on the Title Register when the gift was made — which the original facts
leave open; without it the Act's transaction provisions would not apply at all.
