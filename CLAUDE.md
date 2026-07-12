# Claude Instructions

## Writing Style

When editing or generating project-facing prose, read and follow:

```text
.agents/skills/avoid-ai-writing/SKILL.md
```

Use that skill to audit and rewrite text so it sounds direct, specific, and human.
Apply it to README updates, report/proposal sections, project descriptions, emails,
and public-facing documentation.

Keep technical notes clear and grounded in the actual project files. Do not invent
evidence, links, case details, legal claims, or implementation status.

## Markdown Quality

Whenever creating or editing Markdown files, run a markdown lint check before finishing.

Use:

```text
npx markdownlint-cli2
```

The project config ignores vendored/reference Markdown such as `contxt.md` and
`.agents/**`, and disables line-length noise for URLs and readable prose.

If `npx` cannot install or run the linter, do a manual markdownlint-style check
for heading spacing, list spacing, line structure, and fenced code blocks. Mention
the limitation in the final response.

## Data Privacy

The `data/raw/` folder contains private legal documents. Do not publish raw files,
copy sensitive details into public docs, or use real names/NICs/addresses in demo
material unless the team has explicitly approved an anonymized version.
