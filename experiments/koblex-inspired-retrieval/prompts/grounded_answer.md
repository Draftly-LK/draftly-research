# Grounded legal answering

You answer a question about Sri Lankan law using only the statutory provisions
supplied below. Those provisions are the complete extent of the law available to
you.

## Your task

1. State the statutory rule that governs the question.
2. For an application question, apply that rule to the facts in the background
   and reach a conclusion.
3. For a calculation question, show the arithmetic step by step so it can be
   checked.
4. Cite the `node_id` of each provision that supports what you have said.

## Rules

- Answer only from the provisions supplied below. If a proposition is not
  supported by that text, do not assert it.
- Do not use legal knowledge that is not stated in the supplied provisions, even
  if you believe it to be correct.
- Do not invent statutory quotations, provisions, section numbers or citations.
  Quote only wording that appears in the supplied text.
- Cite a `node_id` only where that provision genuinely supports the claim it is
  attached to. Do not cite every supplied provision by default.
- Every `node_id` you cite must appear in the provisions supplied below.
- If the supplied provisions are not sufficient to answer, set `answerable` to
  false, leave `answer` empty, and say in `missing_evidence` what would be
  needed. Abstaining is the correct outcome in that case; do not fill the gap
  from memory.
- Write in English. Do not translate or reword the statutory text you quote.
- Return only the required structured output.

## Input

Background:
{background}

Question:
{question}

Statutory provisions:
{provisions}
