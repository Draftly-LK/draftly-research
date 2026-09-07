# M076 research notes (status=unverified)

Paper 12 Q7, April 2020. One Tier A question, M076-Q01, `keep`: draft the
testimonium clause of an indenture of lease from Dinuk de Silva to OMEGA
(Private) Ltd.

## Queries

- `grep "witness whereof"` returns no match anywhere in the corpus. That
  negative is the key finding: the testimonium formula is not in the statutes.
- `search "attestation of deed signature of parties witnesses notary"` led to
  Notaries Ordinance s.31 and Prevention of Frauds Ordinance s.2.
- `show --full` on 1-1907/s31, 31-2022/s16, 6-2024/s3, 7-1840/s2, 30-2022/s2 to
  reconstruct the April 2020 text.
- `search "company common seal execution of documents" --act 7-2007` returned
  s.446, s.474, s.26; the right provision is s.19, reached via s.428's
  reference to "paragraph (a) of subsection (1) of section 19".
- `defs 1-1907` gives only three terms (s.43): no definition of "deed" or
  "notary" to rely on. `check` confirmed all eight excerpts verbatim.

## Temporal work

Rules (8), (12), (18), (21) and (24) of s.31 are untouched by the 2011, 2022
and 2024 amending Acts. Rule (14) (corporate seal, board resolution) and rule
(15A) (thumb impressions) were inserted or substituted in 2022, so they are
excluded even though rule (14) looks apt for a corporate lessee. Rule (26)'s
"Form F 1" is a 2024 change; the quoted words predate it. Prevention of Frauds
s.2 paragraphs (a) and (b) are 2022/2024 text; only the unamended opening
words are quoted.

## Rejected

Notaries Ordinance s.31(20) and Form E govern the attestation, a different
clause after the signatures, so they are background only. Companies Act s.446
(receiver's seal) and s.26 (authentication) do not concern execution by the
company. Stamp duty rate schedules are not extracted and stamp duty is recited
in the attestation. The partition statutes belong to other sub-questions.

## For the verifier, first

1. The classification. Marked `mixed_statute_and_case` and `reserved` because
   the marks turn on precedent wording no statute supplies. If the benchmark
   treats drafting questions with statutory content requirements as
   `statute_only`, this must be flipped.
2. Whether "two others of the same tenor and date" is properly traced to
   s.31(24) and s.31(26), or is pure practice with no statutory anchor.
3. The lease term is never stated, so Prevention of Frauds s.2's one-month
   exclusion is not formally ruled out. No enrichment, the question is `keep`.
4. The drafted wording, against a recognised conveyancing precedent.

The validator prints OK with zero errors and zero warnings.
