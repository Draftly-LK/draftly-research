# M052 research notes (status: unverified)

Matter: Paper 9 Q8. Tier A question is M052-Q01 only ("What documents would you
call for the examination of title of the Rubber Estate?"). M052-Q02 is Tier B
and was not annotated.

## Queries tried

- `acts` to scope the corpus, then `toc` on 1-1907, 2-1958, 23-1927, 38-2014,
  1-1972, 4-1902.
- `search "company agricultural land ceiling"` surfaced Land Reform Law s.3,
  s.5, s.8, s.13.
- `grep "certified extract of the folio"`, `grep "not duly stamped"`,
  `grep "certificate of incorporation" --act 7-2007`.
- `show --full` on every section quoted, plus `show 31-2022/s16 --full` and
  `show 6-2024/s3 --full` to date each rule of Notaries Ordinance s.31.

## Alternatives rejected

- Notaries Ordinance s.31 rule (17)(b)(i) (certified folio extract) and rule
  (17)(d) (certificate of incorporation) look like the perfect authority for
  this question but were inserted by Act No. 31 of 2022, after the matter date.
  Rule (14)'s corporate seal and board resolution wording was substituted by the
  same Act. All were excluded; rule (17)(b)(i) is kept as a background provision
  with `applicable_to_matter_date: false` so the trap is visible.
- Powers of Attorney Ordinance s.3 and Prevention of Frauds Ordinance s.2 carry
  post-2022 text in the corpus. Section 2 is used as supporting only; s.3 is
  background only, because compulsory registration of a power of attorney dates
  from Act No. 28 of 2022 and the corpus has no pre-2022 text.
- Registration of Title Act, No. 21 of 1998 was not used: nothing in the corpus
  shows Kalutara as a declared area, so a certificate of title cannot be assumed.
- Mortgage Act s.71 and Land Acquisition Act s.2 were read and dropped as too
  remote from a document list.

## For the verifier, first

1. The `authority_requirement: statute_only` call. Every listed document is tied
   to a corpus provision, but a lawyer may say a complete exam answer needs the
   practice items in `corpus_gaps` (thirty-year search, local-authority and
   street line certificates). If so, reclassify as
   `mixed_statute_and_case` and reserve.
2. PROV-M052-010 and PROV-M052-013: the corpus strips the headwords from both
   interpretation sections, so the definition-to-term pairing is inferred.
   Confirm "rubber estate" means not less than one hundred acres against the
   printed Act. The whole no-consent-needed line of reasoning turns on it.
3. The enriched foreign-shareholding fact (thirty per cent) is decisive; at fifty
   per cent or above the transaction would be prohibited outright, which would
   change the answer rather than extend it.

Validator: `validate_legal_map.py M052` prints OK, 0 errors, 0 warnings.
