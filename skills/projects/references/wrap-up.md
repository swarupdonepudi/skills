# Wrapping up a session

Every session ends here, including short or exploratory ones, and it is the final step of every plan. The wrap-up is what makes the next session's resume instant, and the commit at the end is what makes the session's work real.

Order matters: records first, then the commit, then the closing summary.

## 1. Tick the done-when items that were met

In the brief's `## Done when`, change `- [ ]` to `- [x]` for each item this session completed, with the human's confirmation if there is any doubt. This is the only place progress is written; everything else derives from it. Do not tick an item that is "mostly" done.

## 2. Update `next.md`

- `## Current status`: phase, the active plan and its state, last session date.
- `## Next session`: what was agreed as the next focus, the recommended option if there is one, and any blocker. If nothing was agreed, propose it and confirm with the human before writing it.
- `## Open questions`: what still needs the human.
- `## Session log`: add one row: session number, date, a link to the changelog you are about to write, and a one-line summary.

Do not paste a narrative of the session into `next.md`. That is what the changelog is for.

## 3. Write the changelog

Session number = number of existing files in `changelogs/` + 1, zero-padded to three digits (if that number is already taken by a concurrent session, take the next). File: `changelogs/NNN-slug.md`, slug three to five words. Shape per `assets/templates/changelog.md`: frontmatter `date`, `session`, `progress` (the ticked count as of now, `"3/7"`), `tags`, `summary`; body `## What was done`, `## Decisions made` ("No significant decisions this session." when true; never omit the heading), `## What is pending`.

Size to substance: a quick fix is 30 to 80 lines; a feature session 80 to 150; a milestone or a hard debugging session up to 250. Never more; if the session produced more than that, the excess belongs in `decisions/` or `learnings/`, not in the changelog.

State completeness honestly. When the project tracks coverage of a countable set (every endpoint, every module), derive "done" from the authoritative list cross-checked against the changelogs, never from a running summary that accumulates session over session.

Continuation sessions on a completed project write their changelog as usual and say "continuation session on a completed project" in the summary.

## 4. Copy every plan created this session

This step is mandatory, not conditional. Every plan written during the session ends up in the project's `plans/` folder, numbered and with `status:` frontmatter:

- **Cursor** writes plan-mode plans to `~/.cursor/plans/*.plan.md`. Copy each plan from this session into `plans/NNN-slug.md`. Keep the body; add or normalize the frontmatter (`status`, `created`, `completed`).
- **Other hosts** keep plans in their own location; copy from there the same way.
- **No host plan mode:** the plan you wrote directly into `plans/` is already there; make sure its frontmatter is current.

Then set every touched plan's `status:` to `in-progress`, `completed` (with `completed:` date), or `abandoned` (with one line on why, in the body). A session's plan is part of its record; a changelog that says "executed the plan" with no plan in `plans/` is a record that cannot be checked.

## 5. Run the knowledge check

Ask yourself what this session taught that clears the bar in [knowledge.md](knowledge.md), then propose, do not write:

- A lesson about the project (a pattern to follow, a premise that proved false, an approach that failed): `learnings/`.
- A choice at a fork with real alternatives: `decisions/`.
- A lesson about how you should work here (a verification step you kept forgetting, a communication preference the human stated): the owner file, `_projects/owners/<name>.md` or `owners/default.md`.
- Doctrine that must outlive the project (a repository rule, an organization law, a vocabulary decision): its durable home outside `_projects/`, this session, with the project keeping only a pointer. Doctrine that lives only in a project file is archived with the project.

Say what you propose and where, in one line each, and write only what the human approves. Routine work produces nothing here, and that is the common case.

## 6. Refresh the rules of engagement

```bash
python3 <skill>/scripts/projects.py refresh <folder>
```

This re-syncs the rules block in `next.md` with this skill's current template. It reports "already current" most of the time; that is fine.

## 7. Commit

Commit the session's code changes together with its records: `next.md`, the brief (if boxes were ticked), the changelog, the plans, and any knowledge entries. Follow the repository's own branching, pushing, and review conventions; do not push, branch, or merge on your own initiative if the repository does not already work that way.

The message is a conventional commit. The type is the nature of the work (`feat`, `fix`, `refactor`, `docs`, `chore`); the scope is the project slug; the body names the session and what landed:

```
feat(billing-api-migration): move the invoice endpoints to v2

Session 4. Invoice list, detail, and export now call v2 with the new
pagination contract; tests cover the cursor edge cases. Records: changelog
004, plan 003 completed, done-when 3 of 7.
```

Three gates, from hard experience:

- Stage the files you touched, by name. Never `git add -A` on a branch other sessions share.
- Before committing, confirm the staged set contains `next.md`, the new changelog, and every plan from this session. A commit that carries the code but not the records leaves the project lying to the next session.
- After committing, read the commit back (`git show --stat`) against your own list of touched files. "Records written" does not mean "work persisted" until you have seen the hash.

Delete any session-scoped scratch file you created (a progress tracker, a scratch note) before committing; do not delete another session's.

## 8. Close

End with three lines: the commit hash; progress as ticked done-when items ("now 4 of 7, about 57%") with one sentence of calibration if needed; what the next session should do. Add any hand-off the human owes, with exact steps. Do not reorganize or polish project files during wrap-up; capture state, do not tidy it.
