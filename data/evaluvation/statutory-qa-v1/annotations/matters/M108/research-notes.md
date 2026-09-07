# M108 research notes

Status: `unverified`. Proposed gold map for one Tier A question (M108-Q01).
M108-Q02 is Tier B and was not annotated.

## Queries tried

- `acts` to find the condominium and registration statutes in the corpus.
- `search "declaration registration condominium property"` — surfaced the
  registration machinery (ss.3A-8B) rather than the ownership rules; useful
  only for ruling those sections out.
- `toc 11-1973`, `toc 23-1927`, then `show --full` on 11-1973 ss.2, 4, 9, 10,
  11, 16, 17, 20, 23, 25, 26 and 23-1927 ss.3, 6, 7, 8, 26, 36, 39.
- `defs 11-1973` for the defined terms, and `check` on all thirteen excerpts.

## Alternatives rejected

- **11-1973 s.4** (a Condominium Plan is deemed an instrument affecting land
  for the Registration of Documents Ordinance). Tempting because the question
  names that Ordinance, but s.4 is about plans, not about a stranger's deed.
- **7-1840 s.2** (Prevention of Frauds, notarial execution). The corpus text
  is the consolidated version carrying 2022 and 2024 amendments, so it is not
  the April 2018 text; and a declaration is not a sale, transfer or mortgage,
  so s.2 may not reach it at all. Left out rather than guessed at.
- **11-1973 s.17** (transfer of land into the common elements) and **s.20**
  (unity of seisin). Read in full; neither bears on a claim by a non-owner.
- **23-1927 s.39** — see corpus gaps; the conclusion alludes to a District
  Court challenge but the map does not lean on s.39 as a provision.

## For the verifier, in order

1. **11-1973 s.26 excerpt.** The corpus body of the interpretation section has
   lost its defined-term lead-ins, so every definition reads as a bare
   `means ...` clause. PROV-M108-011 quotes what is, on position and content,
   the definition of "common elements". Confirm against the source before
   treating it as settled.
2. **The two-part conclusion.** The map says Gihan can have the deed drawn and
   may even get it registered, but takes nothing by it. That rests on
   23-1927 s.36 listing grounds of refusal that do not include bad title, plus
   s.7(4). If the examiner wanted a flat "no", the split answer is the point
   to argue about.
3. **Two provisions on 11-1973 s.9.** PROV-M108-001 and -002 share a
   `section_id` and differ by subsection. The validator allows it; flagging in
   case the convention elsewhere is one provision per section.
4. **Enrichment.** Four added facts, three decisive. The decisive one is
   FACT-M108-Q01-001: the question never says the Condominium Plan was
   registered, and nothing in the answer works until it is.

Validator: `OK errors=0 warnings=0`.
