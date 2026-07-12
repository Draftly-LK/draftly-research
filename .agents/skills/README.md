# Skills Registry

The menu of skills available in this project, for every agent that works here
(Claude Code, Codex, Cursor, Copilot, …). Read this before starting a task to
see whether a skill already covers it.

## How to read this

- **[portable]** — a `SKILL.md` in the [agentskills.io](https://agentskills.io)
  format lives in this repo. Any compatible agent (Claude Code, Codex, Cursor,
  Copilot, OpenHands, …) can load and follow it.
- **[Claude-only]** — a built-in / plugin skill of Claude Code. It is *not* in
  this repo and cannot be run by other agents. Listed so everyone knows it
  exists; if you are not Claude Code, treat its capability as unavailable.

## Project skills (in this repo)

| Skill | Availability | Path | Use when |
| --- | --- | --- | --- |
| `avoid-ai-writing` | **[portable]** | `.agents/skills/avoid-ai-writing/SKILL.md` | Auditing/rewriting prose to remove AI-isms. Apply to READMEs, reports, proposals, emails, docs. |
| `legal-source-lookup` | **[portable]** | `.agents/skills/legal-source-lookup/SKILL.md` | Answering a Sri Lankan conveyancing question from the `data/legal-sources/` corpus, with exact citations. |

## Claude Code built-in skills (not portable)

These run only under Claude Code. Other agents: unavailable.

| Skill | Availability | Use when |
| --- | --- | --- |
| `deep-research` | [Claude-only] | Multi-source, fact-checked research report on a topic. |
| `dataviz` | [Claude-only] | Any chart, graph, dashboard, or data visualization. |
| `pptx` | [Claude-only] | Any `.pptx` slide deck — create, read, edit. |
| `framer` / `framer-code-components` | [Claude-only] | Framer site / code-component work. |
| `verify` | [Claude-only] | Exercise a code change end-to-end to confirm it works. |
| `code-review` | [Claude-only] | Review the current diff for bugs / cleanups. |
| `simplify` | [Claude-only] | Apply reuse/simplification/efficiency cleanups to a diff. |
| `security-review` | [Claude-only] | Security review of pending changes on the branch. |
| `review` | [Claude-only] | Review a GitHub pull request. |
| `run` | [Claude-only] | Launch and drive this project's app. |
| `fewer-permission-prompts` | [Claude-only] | Tune the Claude allowlist to reduce prompts. |
| `update-config` | [Claude-only] | Configure the Claude Code harness (settings.json, hooks). |
| `keybindings-help` | [Claude-only] | Customize Claude Code keyboard shortcuts. |
| `claude-api` | [Claude-only] | Reference for the Claude API / Anthropic SDK. |
| `init` | [Claude-only] | Initialize a `CLAUDE.md` for a codebase. |
| `loop` | [Claude-only] | Run a prompt/command on a recurring interval. |

## Adding a portable skill

1. Create `.agents/skills/<name>/SKILL.md` in the agentskills.io format
   (YAML frontmatter with `name`, `description`, `compatibility`; body is the
   instructions).
2. Add a row to the **Project skills** table above.
3. If it should be discoverable to every agent, mention it in `AGENTS.md`.
