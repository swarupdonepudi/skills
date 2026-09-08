# Projects

This folder is the memory of every piece of work here that spans more than one agent session. Each project is a folder that carries its own brief, a one-file resume, plans, session changelogs, decisions, and learnings. The list of active folders is the honest to-do list.

## Resume any project

Drag its `next.md` into a conversation. The agent becomes the project's owner, checks the checkout is current, reads the project silently, presents status, offers options, and waits for direction.

## Layout

```
_projects/
  YYYYMMDD.NN.slug/          active project
  YYYYMMDD.NN.sp.slug/       active sub-project (flat beside its parent, linked by content)
  .completed/                finished, still resumable
  .on-hold/                  paused with a written resume condition
  .shelved/                  deferred indefinitely
  owners/                    how the agent works on projects here (optional; see below)
```

Inside a project: `README.md` is the brief, `next.md` is the current state, `plans/` holds intent, `changelogs/` holds history (one per session), `decisions/` holds rationale, `learnings/` holds lessons. Each file has one job and nothing is written twice.

## Owners

Every project has an owner: the operating character the agent becomes at resume. The `projects` skill ships a default. To shape how the agent works in this repository, write `owners/default.md`; to give a project a named owner, add `**Owner:** <name>` to its brief and write `owners/<name>.md`. Owner files layer on the default unless their frontmatter says `extends: none`.

## Tooling

This folder is managed by the `projects` agent skill. Install it for your coding agent with `npx skills add swarupdonepudi/skills`, then say "start a project", "resume", "wrap up", "complete this project", or "what's on my plate". The skill's CLI (`projects.py new | move | list | refresh`) does the mechanical parts.
