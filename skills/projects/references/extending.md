# Extending the framework

The default is deliberately small. These are patterns that grew in heavy use (hundreds of projects, several concurrent agents, more than one operator) and were left out of the default because they carry cost that only pays off at that scale. Each is two or three sentences: enough to recognize the need and build it in your own repository. None of them requires changing this skill; all of them live in `_projects/owners/`, in your repository's own rules, or in extra files inside a project.

## A workforce of named owners

Several named owners, each with a file in `_projects/owners/`, each responsible for a slice of the portfolio (product, infrastructure, support, content). `list --owner <name>` becomes each owner's to-do list. The next step, if you want it, is an owner "hello" session: the owner scans its projects, leads with the stalest, and proposes the day's work before being asked. Keep owner files short; a character is a page, not a manual.

## Owner memory

If an owner needs to remember things across projects (efficiency pointers, where things live), give it a folder instead of a file: `_projects/owners/<name>/owner.md` plus `notes.md`. Hold the bar high; most of what looks like memory belongs in the repository's own `AGENTS.md` or rules, where every agent reads it. The `**Owner:**` line keeps naming `<name>`; the CLI's starter creates a file, so create the folder by hand.

## A project-level inbox

When several projects run at once and one learns something another needs, an `_inbox/` folder inside the receiving project holds short dated notes from the sender; the receiver reads and clears it at resume. It keeps cross-project communication out of chat and out of the sender's changelog.

## Quick notes for small work

Some teams want a lighter record for one-or-two-session efforts than a project. The cleanest answer is not a second framework but a project with an empty `done-when` filled in at creation and a wrap-up that takes two minutes; the six-file model is already light. If you still want a tier, a single `notes.md` in a dated folder under `_projects/.quick/` is enough.

## Proof and deferred verification

For work where claims must be measured before they are made (performance, capacity, reliability), a `proof/` folder inside the project holds the raw measurements, and a `deferred-verification.yaml` lists every live check the session could not run: one entry per provable behavior, with where it should eventually be proven and what it depends on. The project is not complete while that ledger has open entries.

## A percent-complete line

Long projects benefit from a stated completion percentage at both ends of every session, derived from a weighted checklist of milestones in the brief, never from feel. Put the checklist in the brief and the percentage in `next.md`'s status.

## Commit locks for a shared branch

When several agents commit to one branch concurrently, a lock file at the repository root (`_locks/git-commit.lock.md`, with an expiry) is acquired before `git add` and deleted after the push. The git index is shared: two sessions staging at once means whichever commits first sweeps both sets of files into one commit. Pair it with the wrap-up habits already in this skill (stage by name, verify the commit).

## Worktrees and pull requests

Repositories that work through branches and pull requests record the branch and PR in `next.md` under a `## Worktree` section, so a later session continues the same branch instead of opening a second PR for the same project. Merging is its own explicit act, never part of wrap-up.

## An operator protocol

When more than one person drives the same agents, a short file that identifies the operator at session start (`whoami`, hostname) and adapts the communication style to them keeps a project readable for both. It belongs in the owner file or a repository rule, not in each project.

## A regenerable kick-off prompt

Some projects keep an `inline-prompt.md`: a single paragraph that re-ignites the project's current priorities and rules, regenerated at wrap-up when the rules changed. It is a convenience for hosts where dragging a file is awkward; `next.md` remains the source of truth.

## Everything else

The rule of thumb for any extension: if it needs a new file in every project, it is probably a section in `next.md` or the brief; if it needs a new behavior from the agent, it is probably a paragraph in the owner file; if it needs a new command, it is probably a small script in your repository beside the CLI, not a change to the CLI.
