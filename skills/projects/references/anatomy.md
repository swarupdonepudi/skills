# Anatomy

## The projects folder

```
_projects/
  README.md                        written once by `new`; an adopter may edit it freely
  00000000.00.standing.slug/       active standing project: a duty that never completes, sorted first
  YYYYMMDD.NN.slug/                active project
  YYYYMMDD.NN.sp.slug/             active sub-project (flat, linked by content)
  .completed/YYYYMMDD.NN.slug/     finished; still resumable
  .on-hold/YYYYMMDD.NN.slug/       paused; the banner says why and what resumes it
  .on-hold/00000000.00.standing.slug/   a paused standing project (likewise under .shelved/)
  .shelved/YYYYMMDD.NN.slug/       deferred indefinitely
  owners/<name>.md                 owner characters (optional)
```

The folder name defaults to `_projects` (the underscore sorts it first and marks it as not-source). `--projects-dir` on every CLI command changes it.

## Naming

`YYYYMMDD.NN.slug` or `YYYYMMDD.NN.sp.slug`.

- `YYYYMMDD` is the creation date, so folders sort chronologically.
- `NN` is a per-day sequence. The CLI computes it across every lifecycle folder, so a project created and archived on the same day cannot collide with the next.
- `sp.` marks a sub-project. Sub-projects share the day's sequence with ordinary projects.
- `slug` is kebab-case: lowercase letters, digits, single hyphens.

A standing project is `00000000.00.standing.<slug>`: a duty belongs to no single day, so its date is all zeros, which sorts it above every dated project, and `standing.` names what it is. The slug is kebab-case. Its layout, with `units/` and `playbooks/`, is in [standing.md](standing.md).

## Inside a project

```
YYYYMMDD.NN.slug/
  README.md              the brief
  next.md                the state
  plans/001-initial-plan.md
  changelogs/            001-slug.md, 002-slug.md, ... one per session
  clock.md               the work clock: one row per sitting
  decisions/             created on first entry
  learnings/             created on first entry
```

### `README.md`, the brief

Written by `new` and sharpened by the agent as the project is understood. Sections, in order: a status marker block (empty while active), the description, an identity list (`- **Owner:**`, `- **Parent:**` for sub-projects, `- **Created:**`), `## Goal`, `## Done when`, `## Scope`, `## Repositories`, `## Constraints`, `## Sub-projects` (added when the first sub-project is created), `## Resume`.

Two lines are read by the CLI and must keep their form:

- `- **Owner:** <name>` names `_projects/owners/<name>.md`.
- `- **Parent:** [<folder>](../<folder>/)` links a sub-project to its parent.

`## Done when` is a checkbox list (`- [ ] item`, ticked to `- [x]` as items are met). Progress is the count of ticked items over the total, derived by `list` and stated by the agent at both ends of a session; it is written nowhere else. Three to nine items, each either done or not.

`## Repositories` lists the repositories the project touches by their workspace folder name, one per line, or `- this repository`. The rules of engagement check each one at resume.

### `next.md`, the state

Sections, in order:

- The rules of engagement between `<!-- projects:roe:start -->` and `<!-- projects:roe:end -->`. The text is rendered from this skill's template and `refresh` re-syncs it; edit the template, not the copies.
- The status banner between `<!-- projects:status:start -->` and `<!-- projects:status:end -->`. Empty while active; `move` fills and clears it.
- `## Where things are`: repo-relative paths to the project's files (and the parent's, for a sub-project). `move` keeps them current.
- `## Current status`: phase, active plan, last session.
- `## Next session`: what was agreed as the focus.
- `## Open questions`: what needs the human.
- `## Session log`: a table with one row per session, linking to the changelog. Never a narrative.

Keep `next.md` short. If it passes about 150 lines, something in it belongs in a changelog, a plan, or a decision.

### `plans/`

`NNN-slug.md` with frontmatter `status: pending | in-progress | completed | abandoned`, `created`, `completed`. `plans/001-initial-plan.md` is created by `new` and approved before work begins. There is no registry file; the frontmatter is the registry.

### `changelogs/`

`NNN-slug.md`, numbered by session, frontmatter `date`, `session`, `progress` (ticked done-when items at that moment, `"3/7"`), `tags`, `summary`; body `## What was done`, `## Decisions made`, `## What is pending`. See [wrap-up.md](wrap-up.md) for sizing.

### `clock.md`, the time

Written empty by `new` (and by `refresh` when it is missing). One table, one row per sitting:

```
| Start | End | Minutes | Active | Changelog | Note |
|-------|-----|---------|--------|-----------|------|
| 2026-11-13 06:55+05:30 | 23:42+05:30 | 1007 | 170 | 001 | idle 07:10-20:50 |
```

- **Start** is the session's first message, **End** its wrap-up, both with their UTC offset. An End on a later day carries its date.
- **Minutes** is what the sitting took. `clock add` computes it once; nothing recomputes a stored value, so a hand-written row may hold net time.
- **Active**, when set, is the time actually worked (the session sat idle). Totals count Active when it is set, else Minutes.
- **Changelog** is the number of the changelog the sitting fed. Several sittings may share one; a changelog may have no row.
- A `~` before a number marks an estimate. A row from before times were kept may carry Minutes alone, with its date in Note.

`clock start` prints the start stamp and writes nothing; `clock add` appends the row at wrap-up; `clock` and `list` derive the totals, which are written nowhere. A session counts in the one project whose changelog it writes; a sub-project's time does not roll up into its parent.

### `decisions/` and `learnings/`

Created on first entry, never empty. `decisions/NNN-slug.md`: context, decision, alternatives, consequences. `learnings/NNN-slug.md` with `kind: guideline | wrong-assumption | dont-do`: lesson, evidence, rule going forward. See [knowledge.md](knowledge.md) for the bar.

## Paths

Paths inside `_projects/` are written relative to the repository root (`_projects/20260908.01.slug/plans/`), which is location-independent and exactly what `move` rewrites. Links between projects are relative markdown links (`../<folder>/`), which `move` recomputes from the tree. Other repositories are named, never pathed; see [multi-repo.md](multi-repo.md).

## Marker blocks

The two marker pairs above are the only text the CLI rewrites inside a file it did not just create; beyond them it only appends rows to `clock.md`. A folder whose `README.md` or `next.md` lacks them was not created by this skill; `move` and `refresh` say so and stop rather than guess.

## Templates

Everything `new` writes comes from `assets/templates/`: `README.md`, `next.md`, `rules-of-engagement.md`, `plan.md`, `clock.md`, `projects-readme.md`, `owner.md`, and for a standing project `standing-README.md`, `standing-next.md`, and `standing-rules-of-engagement.md`. The agent uses `changelog.md`, `decision.md`, and `learning.md` as the shape for what it writes by hand; the `$placeholders` in them are for the agent to fill.
