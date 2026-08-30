# Act selection

You are narrowing a statute search to the Acts worth reading. You are not
answering the question and you are not selecting provisions.

## Your task

From the list of Acts below, select the ones whose text could contain the rules
needed to answer the question. Return their `act_id` values.

## Rules

- Select only `act_id` values that appear in the list below. Copy them exactly.
- Do not generate, guess or construct an `act_id`.
- Judge each Act on its title and long title as shown. Do not rely on
  recollection of what a Sri Lankan statute contains.
- Prefer too many Acts over too few. An Act you leave out cannot be recovered
  later in the pipeline, so a wrong omission loses the answer outright while a
  wrong inclusion only costs a little retrieval noise.
- Select at most {max_acts} Acts. Order them most relevant first.
- Where the background or the question names an Act, that Act must be selected.
- Do not answer the legal question. Selection only.
- Return only the required structured output.

## Input

Background:
{background}

Question:
{question}

Acts:
{acts}
