# Lifecycle

Four states, one command, every move reversible.

| State | Folder | Meaning |
|---|---|---|
| active | `_projects/` | in progress; the to-do list |
| completed | `_projects/.completed/` | objectives met; still resumable for follow-up |
| on-hold | `_projects/.on-hold/` | paused with a written reason and resume condition |
| shelved | `_projects/.shelved/` | deferred indefinitely; may never resume |

```bash
python3 <skill>/scripts/projects.py move <folder> --to completed
python3 <skill>/scripts/projects.py move <folder> --to on-hold --reason "..." --resume-when "..."
python3 <skill>/scripts/projects.py move <folder> --to shelved --reason "..."
python3 <skill>/scripts/projects.py move <folder> --to active
```

Add `--dry-run` to see every change first. `move` does the whole job: relocates the folder, sets or clears the status banner in the brief and `next.md`, updates the row in the parent's sub-project table, and repairs every reference under `_projects/` in both directions. Nothing is left for you to edit.

## Completing

Before moving, walk the brief's `## Done when` with the human: every item ticked, or an honest note in the final changelog about what was not. `move --to completed` prints a reminder when boxes are still unticked; it does not refuse, because closing with known gaps is sometimes the right call, but it is the human's call. Add a final changelog if this session did work. Then `move --to completed`. If the project has active sub-projects, `move` refuses: complete or park them first, or pass `--force` when the human wants the parent closed regardless.

Completion is a human decision. Recommend it when the brief's done-when is met; never close a project to make the list shorter.

## Putting on hold

Ask two things and pass them through: why (`--reason`) and what has to happen before it resumes (`--resume-when`). Both end up in the banner so the next person to open the project sees them first. If the project has active sub-projects, `move` refuses; offer to hold them too, or `--force`.

Holding and shelving are the human's call. As the owner your posture is that the work needs to get done; you do not recommend shelving.

## Shelving

Same as hold with only `--reason`. Shelved means no plan to return.

## Reactivating

`move <folder> --to active` from any state. The banner is cleared, references are repaired, and a sub-project's parent row reads Active again. Then drag `next.md` in and resume normally. When the resume file of a held project is dragged in directly, follow [resume.md](resume.md): state the resume condition, ask whether it is met, and move only on a yes.

## Continuation sessions on completed projects

Follow-up work surfaces often after completion (a bug found in use, a gap seen in review). Do not move the project back. Work it where it lives, write the changelog with "continuation session on a completed project" in its summary, update `next.md`'s status to "Completed (continuation YYYY-MM-DD)" and its session log, and commit. If the follow-up grows into real work with its own plan, that is a new project that names this one in its brief.

## The portfolio

"What's on my plate", "what's stale", "where do things stand":

```bash
python3 <skill>/scripts/projects.py list            # active, stalest first
python3 <skill>/scripts/projects.py list --stale 7  # idle a week or more
python3 <skill>/scripts/projects.py list --all      # every state
```

The table shows each project's owner, progress (ticked done-when items over total, as a percentage), last activity, and days idle. Lead with the stalest active project and what stands between it and done. An owner treats a project idle for a week as the most important thing in the list.

## Moving between archived states

`move` works between any two states directly; a held project can be completed or shelved without a stop in active. Sub-project checks apply whenever the target is not active.

## Folders the CLI will not touch

`move` and `refresh` work only on folders whose `README.md` and `next.md` carry the marker blocks `new` writes. A folder without them was not created by this skill; the CLI says so and stops rather than guess at its layout.
