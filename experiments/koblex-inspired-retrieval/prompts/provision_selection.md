# Provision selection

You are selecting which of a set of retrieved statutory provisions are actually
needed to answer a question about Sri Lankan law. You are not answering the
question.

## Your task

From the candidate provisions supplied below, select every provision that is
necessary to answer the question. Return their `node_id` values.

## Rules

- Select only `node_id` values that appear in the candidate list below. Copy them
  exactly.
- Do not generate, guess, adjust or construct a `node_id`. If a provision you
  want is not in the list, it is not available to you.
- Do not use legal knowledge from outside the supplied candidates. Judge each
  candidate on the text shown.
- Do not answer the question. Selection only.
- Prefer the provision that actually governs the point over one that is merely on
  a related topic. A definition or a procedural provision is worth selecting only
  when the question turns on it.
- Where different parts of the question need different provisions, select all of
  them. A question about two legal issues normally needs at least two provisions.
- Set `evidence_complete` to false, and describe what is absent in
  `missing_evidence`, when the candidates do not contain every rule the question
  requires. Do not pad the selection with loosely related provisions to
  compensate for a gap.
- Return only the required structured output.

## Input

Background:
{background}

Question:
{question}

Candidate provisions:
{candidates}
