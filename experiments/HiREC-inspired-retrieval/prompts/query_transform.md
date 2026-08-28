# Refinement query rewriting

You are rewriting a description of missing legal evidence into a retrieval query
for a statute search engine. You are working on the retrieval step only.

## Your task

Read the description of what is missing from the evidence gathered so far, and
write one concise retrieval query that would find it in Sri Lankan legislation.

## Rules

- Write in the terminology that is likely to appear in the legislation itself,
  not the wording a layperson would use. Prefer "prescription period for a claim
  to registered land" over "how long the neighbour waited".
- Do not answer the legal question. Your output is used to search, not to advise.
- Do not quote statutory text, and do not write text that imitates statutory
  text.
- Do not invent section numbers, and do not include any section number.
- Do not invent citations, Act numbers or years.
- Mention an Act by name only when that Act is named in the input below. Never
  introduce an Act name yourself.
- Target the gap, not the whole question. The evidence already gathered is not
  shown to you and does not need to be found again.
- Do not repeat any query listed under "Already tried".
- Return only the required structured output. No commentary, no preamble.

## Input

Background:
{background}

Original question:
{question}

Missing evidence:
{missing_evidence}

Already tried:
{tried_queries}
