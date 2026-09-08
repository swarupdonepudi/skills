# Resuming a project

The resume file (`next.md`, or `next-task.md` in older projects) carries its own rules of engagement, and they govern. This page adds what the file cannot know: how to find the project when no file was given, and what changes when the project is not active.

## When a resume file is in the conversation

Follow its rules of engagement in order and completely:

0. Become the owner. Resolve the owner file (Owner line, `owners/default.md`, then this skill's `references/owner.md`), read it, and work as that person.
1. Check the checkout. For this repository and every repository named in the brief's `Repositories` section: `git fetch --quiet && git status --short --branch | head -1`. Behind or diverged means stop and tell the human. Do not read on.
2. Gather context silently: the brief, every changelog oldest to newest, every plan, decisions and learnings if present, and for a sub-project the parent's brief, knowledge, and three newest changelogs. Do not narrate what you are reading.
3. Present status as the owner: objective, changelogs read, done, open, agreed focus, and anything the human should know.
4. Offer two or three options with one recommended.
5. Wait.

"Wait" means wait. Do not create a plan, edit a file, or run a build until the human picks or directs. If the human's first message already contains direction ("resume and do the thing we agreed"), the direction counts; still present the status first, briefly, so they can catch a stale premise.

## When no file was given

"Resume the auth project", "continue where we left off", "what were we doing on X": find it.

```bash
python3 <skill>/scripts/projects.py list --json
```

Match on slug. One match: read its `resume` path and follow the file. Several plausible matches: name them and ask. None: say so and offer to start one. If the request is vague ("what should I work on"), run `list` without filters and lead with the stalest active project, as the owner would.

## When the project is not active

- **On hold.** The banner states the reason and the resume condition. Say both, then ask whether the condition is met. If yes, offer to reactivate (`move <folder> --to active`) before doing any work; if no, ask whether they want to work on it anyway, and do not move it without a yes.
- **Shelved.** Same shape: state the reason, ask whether to reactivate.
- **Completed.** Follow-up work on a finished project is common. Present the completion status, then whatever the human wants. Do not move the project back to active for follow-up; the session is recorded as a continuation (see [lifecycle.md](lifecycle.md)).

## Working after direction

Write the plan into `plans/NNN-slug.md` (`status: in-progress` once approved) and execute against it. The plan is a map: re-verify what it cites against the code before you build on it, and when the code and the record disagree, the code wins and you correct the record the same session. Verify as you go, not in a batch at the end. When something worth remembering surfaces, follow [knowledge.md](knowledge.md). End with [wrap-up.md](wrap-up.md), always.
