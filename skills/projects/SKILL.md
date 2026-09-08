---
name: projects
description: Persistent memory for work that spans more than one agent session. Each project is a folder under _projects/ that carries its brief (README.md), a one-file resume (next.md), plans, one changelog per session, decisions, and learnings, plus an owner character the agent becomes at resume. Use when the user starts work that will take several sessions or asks to start or create a project; resumes or continues a project; drags a next.md from a _projects/ folder into the conversation; says wrap up or end the session; asks to complete, pause, hold, shelve, or reactivate a project; spawns a sub-project; or asks what is on their plate or which projects are stale. Not for the ordinary word "project" (a codebase, a Next.js project, a build target).
license: MIT
metadata:
  author: swarupdonepudi
  version: "1.0.0"
---

# Projects

Work that takes more than one conversation loses its context between conversations: decisions get buried, the same dead ends are tried twice, and every session opens with ten minutes of re-explaining. This skill fixes that with a folder per project that carries everything the next session needs, and a resume file that loads it all in one drag. The list of active project folders becomes the honest to-do list.

You are the mechanism. The CLI does the mechanical parts (folders, moves, link repair); you do the judgment (what the brief says, what the plan is, what the changelog records, when to stop and ask).

## The shape

```
_projects/
  YYYYMMDD.NN.slug/          active project
  YYYYMMDD.NN.sp.slug/       active sub-project, flat beside its parent, linked by content
  .completed/  .on-hold/  .shelved/     lifecycle folders, created on first use
  owners/                    how the agent works here (optional)
  README.md                  written once on first use
```

Inside a project, six files, each with one job, nothing written twice:

| File | Job | Written by |
|---|---|---|
| `README.md` | The **brief**: goal, done-when checklist (progress is its ticked count), scope, repositories, owner, sub-project table, lifecycle banner | `new`, then the agent as the brief sharpens and items are met |
| `next.md` | The **state**: rules of engagement, current status, active plan, next-session focus, open questions, one-line session log | `new`; the agent at wrap-up |
| `plans/NNN-slug.md` | The **intent**: the plan executed against, `status:` in frontmatter | The agent, before executing |
| `changelogs/NNN-slug.md` | The **history**: what was done, decided, and left pending. One per session, mandatory | The agent at wrap-up |
| `decisions/NNN-slug.md` | The **rationale** for a fork in the road. Created lazily, ask first | The agent, with permission |
| `learnings/NNN-slug.md` | The **lessons**: `kind: guideline`, `wrong-assumption`, or `dont-do`. Created lazily, ask first | The agent, with permission |

Names: `YYYYMMDD.NN` is the creation date and a per-day sequence (unique across every lifecycle folder); `sp.` marks a sub-project. Full anatomy, marker blocks, and the Owner and Parent lines: [references/anatomy.md](references/anatomy.md).

## The owner

Every project has an owner: the operating character you become at resume (Step 0 of the rules of engagement). Resolution order: the `**Owner:**` line in the brief names `_projects/owners/<name>.md`; else `_projects/owners/default.md` if it exists; else this skill's [references/owner.md](references/owner.md). Owner files layer on the default unless their frontmatter says `extends: none`.

An adopter shapes how you work on their projects by writing `_projects/owners/default.md` in their repo, never by editing this skill (updates overwrite it). The default character in one line: own the outcome end to end, do everything you can yourself and hand the human only what you genuinely cannot, run the verification yourself, drive to completion, write positions not menus, never speculate.

## Operations

| The user | You | Read |
|---|---|---|
| Starts work that will span sessions; "start a project" | Draft the brief from the conversation, confirm it, run `new`, write `plans/001`, get it approved, stop | [references/start.md](references/start.md) |
| Drags `next.md` in; "resume X"; "continue the project" | Follow the file's rules of engagement exactly: become the owner, check the checkout, read silently, present status with progress, offer three options, wait for the pick, plan (host plan mode if there is one) with the wrap-up as the last step, execute to the commit | [references/resume.md](references/resume.md) |
| "wrap up"; the plan's final step; the work for today is done | Tick met done-when items, update `next.md`, write the changelog, copy every plan from this session, run the knowledge check, run `refresh`, commit with a conventional message | [references/wrap-up.md](references/wrap-up.md) |
| "complete", "pause", "put on hold", "shelve", "reactivate" | Confirm the reason (and resume condition for hold), run `move`, report | [references/lifecycle.md](references/lifecycle.md) |
| A piece of the project is big enough to run on its own | Propose a sub-project; run `new --parent` | [references/sub-projects.md](references/sub-projects.md) |
| Something worth remembering surfaces mid-session | Ask before writing to `decisions/` or `learnings/` | [references/knowledge.md](references/knowledge.md) |
| "what's on my plate"; "which projects are stale" | Run `list`, lead with the stalest | [references/lifecycle.md](references/lifecycle.md) |
| Code lives in other repositories | Name them in the brief; never write machine paths | [references/multi-repo.md](references/multi-repo.md) |

Why the framework is shaped this way: [references/why.md](references/why.md). Patterns adopters have grown on top of it (a workforce of named owners, quick notes, proof ledgers, commit locks): [references/extending.md](references/extending.md).

## The CLI

`scripts/projects.py` next to this file. Python 3.9 or newer, standard library only. Run it with `python3` (`python` on Windows) from the repository that holds `_projects/`, or pass `--repo-root` (in a multi-repo workspace, that is the repository holding `_projects/`, not the code repository you are editing).

```bash
projects.py new --name <slug> --description "..." --goal "..." [--done "a,b,c"] [--scope "..."] [--repos "repo-a,repo-b"] [--owner <name>] [--parent <folder>]
projects.py move <folder> --to completed|on-hold|shelved|active [--reason "..."] [--resume-when "..."] [--dry-run] [--force]
projects.py list [--all] [--stale DAYS] [--owner <name>] [--json]
projects.py refresh <folder> | --all
projects.py selftest
```

- `new` bootstraps `_projects/` (with a README, written once) on first use, picks the next sequence number, renders the brief, `next.md`, and `plans/001-initial-plan.md`, creates `owners/<name>.md` from a starter when `--owner` names a new owner, and registers a sub-project with its parent.
- `move` works between any two states. It moves the folder, sets or clears the status banner in the brief and `next.md`, updates the sub-project's row in its parent, and repairs every reference in `_projects/`: repo-relative paths by boundary-safe literal replacement, relative links by recomputing where they pointed. It refuses to archive a project with active sub-projects unless `--force`. `--dry-run` prints every change and writes nothing. Requires `--reason` for on-hold and shelved, `--resume-when` for on-hold.
- `list` shows active projects stalest first with owner, progress (ticked done-when items over total), last activity (newest changelog), and idle days; `--all` adds the lifecycle folders; `--json` for you.
- `refresh` re-syncs the rules of engagement block in `next.md` from this skill's template, so every project runs the current protocol. Wrap-up runs it on the current project.

The CLI rewrites only what it owns: the text inside its marker blocks and the paths a move invalidates. A folder without the marker blocks was not created by this skill; `move` and `refresh` say so and stop.

## Rules that never bend

- **Never start work on resume.** Read, present status with progress, offer exactly three options, wait for the pick. Even when the next step is obvious.
- **Every plan ends with the wrap-up.** Plan in the host's plan mode when it has one; the last step is always the full wrap-up and a conventional commit. Approving the plan approves the session; run it to the commit hash.
- **Every session ends with a changelog, and every plan is kept.** Short sessions get short changelogs; no session gets none. Every plan created this session is copied into `plans/`.
- **Progress is derived, never stored.** It is the count of ticked items under `## Done when` in the brief. Tick a box when an item is met; state the count at both ends of the session; never write a percentage anywhere else.
- **Plan before executing.** Get the plan approved, then act. A plan is a map: re-verify what it cites against the code before building on it.
- **`next.md` is state, changelogs are history.** Never paste a session narrative into `next.md`; one line in the session log, the detail in the changelog.
- **Knowledge folders are sparse.** Ask before writing to `decisions/` or `learnings/`. The bar: high impact, still true in a month, non-obvious, reusable.
- **Project scaffolding never leaks.** No project name, `_projects/` path, plan or decision number in source code, comments, or durable documentation. Grep the diff before finishing.
- **Repositories are named, never pathed.** The brief names other repositories by their workspace folder name; you resolve them. Machine paths break the moment the project is opened on another laptop.
- **Do the work.** Do not hand the human instructions for things you can do. When a step is genuinely theirs, prepare everything around it and give exact steps.
