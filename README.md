# Skills

[![skills.sh](https://skills.sh/b/swarupdonepudi/skills)](https://skills.sh/swarupdonepudi/skills)
[![validate](https://github.com/swarupdonepudi/skills/actions/workflows/validate.yml/badge.svg)](https://github.com/swarupdonepudi/skills/actions/workflows/validate.yml)

Agent skills by [Swarup Donepudi](https://github.com/swarupdonepudi), in the [Agent Skills](https://agentskills.io) format, for Cursor, Claude Code, Codex, Gemini CLI, and any other host that reads a `SKILL.md`. Read the docs at [swarupdonepudi.github.io/skills](https://swarupdonepudi.github.io/skills/).

## What is here

| Skill | What it does |
| --- | --- |
| [`skills/projects`](skills/projects/SKILL.md) | Persistent memory for work that spans more than one agent session. Each project is a folder that carries its brief, a one-file resume, plans, one changelog per session, decisions, and learnings, plus an owner character the agent becomes at resume. The list of active folders is your honest to-do list. |

## Install

One command; the [skills CLI](https://github.com/vercel-labs/skills) detects your agents and asks whether to install for this project or globally:

```bash
npx skills add swarupdonepudi/skills
```

Target one agent, or every agent on the machine:

```bash
npx skills add swarupdonepudi/skills --agent cursor
npx skills add swarupdonepudi/skills --agent claude-code --global
npx skills add swarupdonepudi/skills --agent '*' -y
```

Claude Code marketplace:

```
/plugin marketplace add swarupdonepudi/skills
/plugin install projects@swarupdonepudi
```

Manual, for any host: clone this repository and copy or symlink `skills/projects` into your agent's skills directory (`~/.cursor/skills/`, `~/.claude/skills/`, `~/.codex/skills/`, or `.agents/skills/` inside a project). `SKILL.md` must sit directly inside the skill folder.

## Sixty seconds with `projects`

Tell your agent about work that will take more than one sitting:

> Let's start a project to migrate the billing service to the new API.

It drafts the brief from the conversation, asks only for what it cannot infer, creates `_projects/YYYYMMDD.01.billing-api-migration/`, writes the first plan, and waits for your approval. Work for as long as you like. When you are done for the day:

> Wrap up.

It ticks the done-when items you met, updates the project's state, writes the session's changelog, copies the plan, and commits with a proper message. Tomorrow, in a fresh conversation, drag the project's `next.md` in. The agent becomes the project's owner, checks the checkout is current, reads every changelog silently, tells you where things stand ("3 of 7 done, about 43%"), offers three options with one recommended, and waits for your pick. Then it plans, and the plan's last step is always the wrap-up, so you can approve and walk away; when you come back the work is committed. No re-explaining.

When the work is done:

> Complete this project.

The folder moves to `_projects/.completed/`, every reference is repaired, and your active list is one shorter. Pause with "put this on hold", defer with "shelve this", and ask "what's on my plate" to see the portfolio, stalest first.

## Shaping how the agent works

Every project has an owner: the operating character the agent becomes at resume. The skill ships a strong default (own the outcome end to end, do everything you can yourself and hand the human only what you genuinely cannot, run the verification yourself, write positions not menus, never speculate). To adjust it for your repository, write `_projects/owners/default.md`; to give a project its own owner, name one in its brief. Owner files live in your repository, so `npx skills update` never overwrites them.

## Where it comes from

`projects` grew out of the project framework that has carried some 350 pieces of multi-session work to completion across [Planton](https://planton.ai) and [Stigmer](https://stigmer.ai), run daily by people and agents in monorepos and in personal repositories that steer work across many code repositories. The skill is that framework rebuilt from first principles for the Agent Skills format: the same benefits, a leaner shape, and nothing copied into your repository except `_projects/` itself.

## Contributing

Issues and pull requests are welcome. Every skill is linted against the specification and the `projects` CLI runs its own lifecycle self-test on every change (`python3 skills/projects/scripts/projects.py selftest`). The spec's own validator, `skills-ref validate ./skills/projects`, is a fine second opinion. The documentation site under `site/` renders `skills/` on every push to `main` and fails on any broken link; edit the skill, never the site, to change the docs.

## License

[MIT](LICENSE).
