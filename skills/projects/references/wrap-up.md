# Wrapping up a session

Every session ends here, including short or exploratory ones. The wrap-up is what makes the next session's resume instant, and the commit at the end is what makes the session's work real.

Order matters: records first, then the commit, then the closing summary.

## 1. Update `next.md`

- `## Current status`: phase, the active plan and its state, last session date.
- `## Next session`: what was agreed as the next focus, the recommended option if there is one, and any blocker. If nothing was agreed, propose it and confirm with the human before writing it.
- `## Open questions`: what still needs the human.
- `## Session log`: add one row: session number, date, a link to the changelog you are about to write, and a one-line summary.

Do not paste a narrative of the session into `next.md`. That is what the changelog is for.

## 2. Write the changelog

Session number = number of existing files in `changelogs/` + 1, zero-padded to three digits (if that number is already taken by a concurrent session, take the next). File: `changelogs/NNN-slug.md`, slug three to five words. Shape per `assets/templates/changelog.md`: frontmatter `date`, `session`, `tags`, `summary`; body `## What was done`, `## Decisions made` ("No significant decisions this session." when true; never omit the heading), `## What is pending`.

Size to substance: a quick fix is 30 to 80 lines; a feature session 80 to 150; a milestone or a hard debugging session up to 250. Never more; if the session produced more than that, the excess belongs in `decisions/` or `learnings/`, not in the changelog.

State completeness honestly. When the project tracks coverage of a countable set (every endpoint, every module), derive "done" from the authoritative list cross-checked against the changelogs, never from a running summary that accumulates session over session.

Continuation sessions on a completed project write their changelog as usual and say "continuation session on a completed project" in the summary.

## 3. Set plan statuses

Every plan touched this session has the right `status:` in its frontmatter: `in-progress`, `completed` (with `completed:` date), or `abandoned` (with one line on why, in the body). If your host wrote a plan file for this session outside the project (some hosts keep plans in their own folder), copy it into `plans/` with a numbered name; otherwise the plan you followed is already there because you wrote it there before executing.

## 4. Run the knowledge check

Ask yourself what this session taught that clears the bar in [knowledge.md](knowledge.md), then propose, do not write:

- A lesson about the project (a pattern to follow, a premise that proved false, an approach that failed): `learnings/`.
- A choice at a fork with real alternatives: `decisions/`.
- A lesson about how you should work here (a verification step you kept forgetting, a communication preference the human stated): the owner file, `_projects/owners/<name>.md` or `owners/default.md`.
- Doctrine that must outlive the project (a repository rule, an organization law, a vocabulary decision): its durable home outside `_projects/`, this session, with the project keeping only a pointer. Doctrine that lives only in a project file is archived with the project.

Say what you propose and where, in one line each, and write only what the human approves. Routine work produces nothing here, and that is the common case.

## 5. Refresh the rules of engagement

```bash
python3 <skill>/scripts/projects.py refresh <folder>
```

This re-syncs the rules block in `next.md` with this skill's current template. It reports "already current" most of the time; that is fine.

## 6. Commit the records

Commit `next.md`, the changelog, the plans, and any knowledge entries, along with the session's code changes if the repository's convention is to commit them together. Follow the repository's own branching, pushing, and review conventions; do not push, branch, or merge on your own initiative if the repository does not already work that way.

Three habits from hard experience:

- Stage the files you touched, by name. Never `git add -A` on a branch other sessions share.
- Before committing, confirm the staged set contains `next.md` and the new changelog. A commit that carries the code but not the records leaves the project lying to the next session.
- After committing, read the commit back (`git show --stat`) against your own list of touched files. "Records written" does not mean "work persisted" until you have seen the hash.

Delete any session-scoped scratch file you created (a progress tracker, a scratch note) before committing; do not delete another session's.

## 7. Close

End with the commit hash, one line on what the next session should do, and any hand-off the human owes (with exact steps). Do not reorganize or polish project files during wrap-up; capture state, do not tidy it.
