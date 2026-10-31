# projects

Persistent memory for work that spans more than one agent session. Each project is a folder under `_projects/` that carries its brief, a one-file resume (`next.md`), plans, one changelog per session, decisions, and learnings, so a fresh conversation picks up exactly where the last one stopped.

This page is for people browsing the skill folder. Agents never read it: they load [`SKILL.md`](SKILL.md) and follow its links. The same material, rendered, lives at [swarupdonepudi.github.io/skills/projects](https://swarupdonepudi.github.io/skills/projects/).

## What is in this folder

| Path | Job |
| --- | --- |
| [`SKILL.md`](SKILL.md) | The instructions the agent loads. Its frontmatter `description` decides when the skill triggers; its body is the operations table and the rules that never bend. |
| [`references/`](references/) | Detail the agent reads on demand: one file per operation ([start](references/start.md), [resume](references/resume.md), [wrap-up](references/wrap-up.md), [lifecycle](references/lifecycle.md), [sub-projects](references/sub-projects.md), [standing projects](references/standing.md), [knowledge](references/knowledge.md), [multi-repo](references/multi-repo.md)), plus the [anatomy](references/anatomy.md) of a project, the default [owner](references/owner.md), patterns for [extending](references/extending.md) it, and [why](references/why.md) it is shaped this way. |
| [`scripts/projects.py`](scripts/projects.py) | The CLI that does the mechanical parts: `new`, `move`, `list`, `refresh`, `selftest`. Python 3.9 or newer, standard library only. |
| [`assets/templates/`](assets/templates/) | The files the CLI writes into `_projects/`, exactly as they ship. |

A note on names: inside a project, `README.md` is the project's brief. This file is only about the skill folder.

## Where to start reading

1. [`references/why.md`](references/why.md) for the problem and the reasoning behind every part of the shape.
2. [`SKILL.md`](SKILL.md) for what the agent does and when.
3. [`references/anatomy.md`](references/anatomy.md) for the folder and file layout in full.

## Install

```bash
npx skills add swarupdonepudi/skills
```

The Claude Code marketplace, per-agent targets, and manual installs are in the repository's [Install section](../../README.md#install).

## Try it

Say these to your agent, one per sitting:

- "Let's start a project to migrate the billing service to the new API." The agent drafts the brief, creates the folder, writes the first plan, and waits for approval.
- "Wrap up." It ticks met done-when items, updates `next.md`, writes the session's changelog, and commits.
- "Complete this project." The folder moves to `_projects/.completed/` and every reference is repaired.
- "Set up a standing project for my daily show." Work that never ends gets `_projects/standing/<slug>/`: a duty and a cadence instead of a done-when list, one unit folder per kept cycle, and a `list` line that says whether today's cycle is on time or overdue.

To resume, drag the project's `next.md` into a fresh conversation. The full walkthrough is in [Sixty seconds with `projects`](../../README.md#sixty-seconds-with-projects).

## Working on the skill

From the repository root:

```bash
python3 skills/projects/scripts/projects.py selftest   # runs the lifecycle end to end in a temporary tree
python3 .github/scripts/lint-skills.py                 # frontmatter, size, links, scripts
```

`SKILL.md` stays under 300 lines; detail belongs in `references/`. The documentation site under `site/` is generated from this folder on every build, so change the docs here, never in `site/`.
