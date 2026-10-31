# Standing projects

Some work never ends: a daily show, a weekly distribution loop, a standing duty to answer GitHub issues. Forced into the normal project shape, it fails in two ways. A done-when list that can never be met makes the project look stuck forever. And a resume file that never closes keeps every session in it until it is too big to load. A standing project fixes both by construction.

A standing project is a **duty kept true**. It is measured by whether each cycle was kept, never by completion. It has no done-when list, no progress percentage, and it never moves to `.completed/`.

## When to use one

| The work | Use |
|---|---|
| has a finish line, even a distant one | a project |
| is a condition that must stay true, cycle after cycle | a standing project |
| is a one-time build inside a standing duty (a new tool, a new channel) | a sub-project of the standing project |

The test: ask "when is this done?" If the honest answer is "never, there is always a next day or a next issue", it is standing. A trial with an end date ("ten episodes, then decide") is still standing: the decision at the end is a cycle's output, not completion.

## Layout

```
_projects/standing/<slug>/
  README.md              the brief: kind, cadence, duty, the loop, setup
  next.md                the state; fixed size, never grows
  playbooks/             the routine, one file per procedure
  units/YYYY-MM/<unit>/  one folder per kept cycle
  plans/  changelogs/    as in any project
  decisions/  learnings/ created on first entry
```

The slug is lowercase letters, digits, and hyphens. It has no date and no sequence number, because a duty belongs to no single day. The CLI names it `standing/<slug>`, and so do Parent lines and the command line (`move standing/<slug> ...`). The bare slug works too.

Create one with:

```bash
python3 <skill>/scripts/projects.py new --standing <slug> \
  --cadence daily|mon-sat|weekdays|weekly \
  --description "..." \
  --duty "the condition kept true" \
  [--loop "what one cycle is"] [--setup "first,second,third"] \
  [--scope "..."] [--repos "repo-a,repo-b"] [--owner <name>]
```

`new` writes the brief and `next.md` from the standing templates, creates `units/` and `playbooks/`, and writes `plans/001-initial-plan.md` to set up the duty and keep its first cycle. Then draft the brief with the human as in [start.md](start.md), with the duty in place of the goal.

## The brief

The CLI reads three lines in the identity list. Keep their form when you edit by hand:

- `- **Kind:** standing` tells a reader what this is. The folder's location is what makes the CLI treat it as standing.
- `- **Cadence:** <daily|mon-sat|weekdays|weekly>` sets when a cycle is due.
- `- **Owner:** <name>`, optional, as in any project.

Sections, in order: `## Duty` (the condition kept true, in one or two sentences, never a finish line), `## The loop` (what one cycle is: what it produces and which playbook runs it), an optional `## Setup` checklist, `## Scope`, `## Repositories`, `## Constraints`. There is no `## Done when`.

`## Setup` holds one-time work that has to exist before or beside the loop (open the channel, write the first playbook). Tick each item as it is met. It is reported as "setup 3 of 7", never as completion: when setup is done, the duty is just beginning.

## Units

Each kept cycle writes one unit folder: `units/YYYY-MM/<unit>/`. The unit name is usually the date (`2026-10-31`). It can also be an issue or episode id (`issue-412`, `ep-12`), or a date with a suffix (`2026-10-31-ep12`). The unit holds what the cycle produced and what it measured: the post text, the links, the numbers, the brief the cycle ran on.

Units are history. Each one is written only by the session that kept that cycle, so parallel sessions never write the same file and no shared file grows. The newest unit is the last kept cycle. `list` reads its date from the start of the unit name, else from the newest file inside it.

## `next.md` stays fixed size

A standing project runs forever, so its resume file must not grow. `## Current status` is replaced every session, never appended. There is no session log table: the units and the changelogs are the history. If `next.md` keeps getting longer, something in it belongs in a unit, a playbook, or a changelog.

## Cadence and overdue

| Cadence | A cycle is expected on |
|---|---|
| `daily` | every day |
| `mon-sat` | every day except Sunday |
| `weekdays` | Monday to Friday |
| `weekly` | seven days after the last unit |

Overdue days, for the daily kinds, are the expected cycle days strictly after the last unit and strictly before today. Today is never overdue yet: a unit logged yesterday is on time, and a daily unit from Monday is two days overdue on Thursday. For `weekly`, each day past the seventh is one day overdue. With no unit yet, the count starts from the project's last activity.

`list` prints each standing project first, in its own lines:

```
standing/feed-said-so   active   -   standing · mon-sat · last unit 2026-10-30 · on time · setup 5/7
  20261031.01.sp.edit-tools   active   -   1/4 25%   2026-10-31   0d
```

`list --json` gives the same as fields: `kind`, `cadence`, `last_unit`, `last_unit_date`, `overdue_days`, `setup_ticked`, `setup_total`. Never compute overdue by hand; read it there.

## States

A standing project is active, on hold, or shelved. It is never completed: `move --to completed` refuses. Pause a duty with `--to on-hold` (with `--reason` and `--resume-when`), and stop it with `--to shelved` (with `--reason`). The folder moves to `.on-hold/standing/<slug>/` or `.shelved/standing/<slug>/`, and every reference is repaired, as for any project. `move --to active` brings it back to `_projects/standing/<slug>/`.

## Resume

The standing rules of engagement live in `next.md`, between the same markers as the normal ones, and `refresh` keeps them current. They differ from the normal rules in three places:

- **Step 2** reads the brief, every playbook, the three newest units, the five newest changelogs, and the open plans. It never reads the whole history, which grows with every cycle.
- **Step 3** presents the duty, its cadence, the last unit and its date, whether the duty is on time or overdue by how many cycle days, and setup x of y if there is a setup list. It never states a completion percentage.
- **Step 4**: when a cycle is due, option A keeps it.

## Wrap-up

The standing wrap-up is the normal one from [wrap-up.md](wrap-up.md) with three changes:

1. **Log the unit** in place of ticking done-when items: write `units/YYYY-MM/<unit>/` with what was produced, the links, and the numbers. Tick any `## Setup` items that were met.
2. **Replace `## Current status`** in `next.md`: the last unit, when the next cycle is due, the active plan. Do not add a session log row.
3. **Write the changelog** with `cycle:` (the unit id, such as `"2026-10-31"`) in the frontmatter in place of `progress:`. A session that kept no cycle writes `cycle: none`.

Close with the commit hash, the unit logged, and when the next cycle is due. There is no progress line.

## Sub-projects

A one-time build inside a duty (a new editing tool, a new channel to open) is a sub-project. It is an ordinary dated folder at the top level of `_projects/`, `YYYYMMDD.NN.sp.<slug>`, with `- **Parent:** [standing/<slug>](../standing/<slug>/)` in its brief:

```bash
python3 <skill>/scripts/projects.py new --name <slug> --description "..." --goal "..." --parent standing/<slug>
```

It has its own done-when list and completes like any project. The standing parent never waits on it and never completes. Its sub-project table only shows what is being built beside the duty. A standing project cannot itself be a sub-project.

## The owner's rule

For a standing project, "done" means the duty was kept this cycle. At resume, a missed cycle is named first, plainly and without judgment. The next cycle is then made smaller, never skipped. Work on the machinery (a better playbook, a new tool) is welcome, but activity without a kept cycle is still a miss. An owner treats an overdue standing project as the most important thing in the list.
