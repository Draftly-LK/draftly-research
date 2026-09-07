# M085 research notes (statutory-qa-v1, unverified)

Paper 13, q7(iii), October 2019. One Tier A question, `enrich`: calculate the
stamp duty on a deed of transfer of a Rajagiriya property worth Rs. 3 million.

## Queries

`acts` surfaced three stamp-duty enactments (43-1982, 12-2006, 6-1990).
`search "stamp duty immovable property transfer rate" -k 20` ranked 6-1990/s37
first. `toc` on all three, then `show --full` on 6-1990 ss.37-40, 43(a), 48,
51, 76, 77, 106 and 12-2006 ss.3, 4, 13. `grep "per centum" --act 6-1990`
returned one hit, the 10% penalty in s.12, not a duty rate. `defs 6-1990`
listed 28 terms. `check` confirmed all eight excerpts verbatim.

## Why the provincial statute governs

12-2006 s.4 gives a closed list of "specified instruments" and a deed
transferring immovable property is not on it; s.13 carves "any instrument
relating to the transfer of immovable property" out of the 2006 Act's
displacement of the 1982 Act. 6-1990 s.37(a) charges duty on instruments
transferring immovable property situated in the Western Province, and
Rajagiriya is in the Colombo District. Both 12-2006 sections are kept as
`background` so the verifier can see the elimination.

## Rejected

43-1982 ss.15, 20, 21 (parallel wording, but that Act does not charge this
instrument and fixes no rate either); 6-1990 s.43(a) and s.50 (no facts engage
them); 6-1990 s.40 (payment mechanics, not the amount).

## Corpus gaps, and why the question is blocked

1. No rate. s.37 charges "at the prescribed rate" and s.77(1)(a) leaves it to
   Gazetted regulations; no rate order is in the corpus, so the arithmetic
   cannot be completed without quoting a percentage from memory.
2. 6-1990 carries `in_force_from_year` 1990 and empty `amendment_events`
   throughout, and no amending provincial statute is in the corpus.
3. Extraction damage: s.37 is word-scrambled ("a transfer of situated in the
   immovable property Western Province"), s.39(2) likewise, and s.106 has lost
   most defined-term headwords; only `value` retains its.

## For the verifier, in order

Add a 2019 Western Province rate order and this becomes `proposed_gold` with a
figure. Then check the garbled s.37 excerpt against the source PDF, and whether
s.48(1) with the s.106 `value` definition is the whole valuation rule at 2019.
Validator prints OK, 0 errors, 0 warnings. All of this is `status=unverified`.
