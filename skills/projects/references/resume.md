# Resuming a project

The resume file, `next.md`, carries its own rules of engagement, and they govern. This page adds what the file cannot know: how to find the project when no file was given, what changes when the project is not active, and how a session runs from the pick to the commit.

## When `next.md` is in the conversation

Follow its rules of engagement in order and completely:

0. **Become the owner.** Resolve the owner file (Owner line, `owners/default.md`, then this skill's `references/owner.md`), read it, and work as that person.
1. **Check the checkout.** For this repository and every repository named in the brief's `Repositories` section: `git fetch --quiet && git status --short --branch | head -1`. Behind or diverged means stop and tell the human. Do not read on.
2. **Gather context silently:** the brief, every changelog oldest to newest, every plan, decisions and learnings if present, and for a sub-project the parent's brief, knowledge, and three newest changelogs. Do not narrate what you are reading.
3. **Present status as the owner:** objective; progress as ticked done-when items in the brief ("3 of 7, about 43%") with at most one sentence of calibration; changelogs read; done; open; agreed focus; anything the human should know.
4. **Offer exactly three options,** A, B, C. A is your recommendation with a one-line reason. Ask the human to pick one.
5. **Wait for the pick.** Do not create a plan, edit a file, or run a build until the human picks or directs. If the human's first message already contains direction ("resume and do the thing we agreed"), the direction counts as the pick; still present the status first, briefly, so they can catch a stale premise.
6. **Plan, then execute through the wrap-up.** See below.

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

## From the pick to the commit

Once the human has picked:

1. **Write the plan.** If your host has a plan mode, use it: the human reviews and approves with one click, and the wrap-up copies the plan file into `plans/`. Otherwise write the plan in the conversation and directly into `plans/NNN-slug.md` with `status: pending`. Either way the plan has the objective, the steps in order, how each is verified, and open questions.
2. **Make the wrap-up the plan's final step.** The last step of every plan reads, in substance: "Wrap up the session per the `projects` skill: update `next.md`, tick met done-when items, write the changelog, copy the plans, run the knowledge check, refresh, commit." A plan without that step is incomplete; add it before presenting.
3. **Get approval.** Approval of the plan is approval of the whole session.
4. **Execute to the commit hash.** Do not stop between steps for confirmation the plan already gave you; stop only for a decision only the human can make (an external-world judgment, a surprise that changes architecture or scope). Verify as you go, not in a batch at the end. When a done-when item is met, tick it in the brief and say so. When something worth remembering surfaces, follow [knowledge.md](knowledge.md).
5. **Finish with the wrap-up,** exactly as in [wrap-up.md](wrap-up.md), and close with the commit hash and the progress line.

The plan is a map, not a script: re-verify what it cites against the code before you build on it, and when the code and the record disagree, the code wins and you correct the record the same session.
