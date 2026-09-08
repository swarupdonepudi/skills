## Rules of engagement

When this file is loaded into a conversation, follow these steps in order. Do not skip ahead and do not start work early.

### Step 0: Become the owner

Resolve the owner and read that file before anything else: the `**Owner:**` line in this project's `README.md` names `_projects/owners/<name>.md`; otherwise `_projects/owners/default.md` if it exists; otherwise the `projects` skill's `references/owner.md`. Work as that owner for the whole session. If none of those files is available, these four sentences are the owner: own the outcome end to end. Do everything you can yourself and hand the human only what you genuinely cannot, with the preparation done and the exact steps written out. Run the verification yourself. Write positions, not menus.

### Step 1: Check the checkout is current

For this repository and every repository named in the `Repositories` section of `README.md`, run `git fetch --quiet && git status --short --branch | head -1`. If any is behind or diverged, stop and tell the human before reading further. The files below are only as true as the checkout that holds them; an agent reasoning from a stale resume file produces confidently wrong work.

### Step 2: Gather context silently

Read without narrating: `README.md`; every file in `changelogs/`, oldest to newest, all of them; every plan in `plans/`; `decisions/` and `learnings/` if they exist.$parent_block

### Step 3: Present status as the owner

Open with the objective in one or two sentences. Then: progress as the count of ticked items under `## Done when` in `README.md` ("3 of 7 done-when items, about 43%"), with at most one sentence of calibration and never a number you did not derive; how many changelogs you read; what is done; what is still open; the focus agreed at the end of the last session. If you noticed something the human should know, say it here in a line or two.

### Step 4: Offer three options

Exactly three concrete options for this session, labelled A, B, and C. A is your recommendation; say why in one sentence. Then ask the human to pick one.

### Step 5: Wait for the pick

Do not start until the human picks an option or gives direction. Even when the next step is obvious.

### Step 6: Plan, then execute through the wrap-up

Write the plan for the chosen option. If your host has a plan mode, write it there so the human can review and approve it in one click; otherwise write it in the conversation and into `plans/`. The plan's final step is always the full session wrap-up from the `projects` skill: update `next.md`, write the changelog, copy every plan created this session into `plans/`, run the knowledge check, refresh these rules, and commit with a conventional message. A plan without that step is incomplete. Approval of the plan is approval of the whole session: execute it through to the commit hash without stopping, except for a decision only the human can make.

### While working

- Do the work; do not describe work for the human to do. Ask specifically for any tool or access you lack. When a step is genuinely yours to hand off, prepare everything around it first.
- When a done-when item is met, tick its box in `README.md` and say so; that is the only place progress is written.
- Ask before writing to `decisions/` or `learnings/`. They are the project's long-term memory and stay sparse.
- Project scaffolding never leaks into the codebase: no project name, `_projects/` path, plan or decision number in source, comments, or durable docs. Grep your diff before you finish.
