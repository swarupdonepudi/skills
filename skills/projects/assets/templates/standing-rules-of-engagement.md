## Rules of engagement

This is a standing project: a duty kept true, never completed. When this file is loaded into a conversation, follow these steps in order. Do not skip ahead and do not start work early.

### Step 0: Become the owner

Resolve the owner and read that file before anything else: the `**Owner:**` line in this project's `README.md` names `_projects/owners/<name>.md`; otherwise `_projects/owners/default.md` if it exists; otherwise the `projects` skill's `references/owner.md`. Work as that owner for the whole session. If none of those files is available, these four sentences are the owner: own the outcome end to end. Do everything you can yourself and hand the human only what you genuinely cannot, with the preparation done and the exact steps written out. Run the verification yourself. Write positions, not menus. For a standing project, "done" means the duty was kept this cycle.

### Step 1: Check the checkout is current

For this repository and every repository named in the `Repositories` section of `README.md`, run `git fetch --quiet && git status --short --branch | head -1`. If any is behind or diverged, stop and tell the human before reading further. The files below are only as true as the checkout that holds them; an agent reasoning from a stale resume file produces confidently wrong work.

### Step 2: Gather context silently

Read without narrating: `README.md` (the duty, the loop, the setup); every file in `playbooks/`; the three newest units in `units/`; the five newest changelogs in `changelogs/`; every plan in `plans/` whose status is pending or in-progress; `decisions/` and `learnings/` if they exist. Do not read the whole history. It grows with every cycle, and the newest cycles are what matter.

### Step 3: Present the duty as the owner

Open with the duty in one sentence and its cadence. Then: the last unit and its date; whether the duty is on time or overdue, and by how many cycle days; setup as "setup 3 of 7" if the brief has a `## Setup` list; the focus agreed at the end of the last session. Take the overdue count from the `projects` skill's `list --json`, never from a guess. It counts the days the cadence expected a cycle, strictly after the last unit and before today, so today is never overdue yet. If a cycle was missed, name it first, plainly and without judgment. A standing project has no completion percentage; never state one. If you noticed something the human should know, say it here in a line or two.

### Step 4: Offer three options

Exactly three concrete options for this session, labelled A, B, and C. A is your recommendation; say why in one sentence. When a cycle is due or overdue, A keeps it. After a miss, make that cycle smaller rather than skip it. Then ask the human to pick one.

### Step 5: Wait for the pick

Do not start until the human picks an option or gives direction. Even when the next step is obvious.

### Step 6: Plan, then execute through the wrap-up

Write the plan for the chosen option. If your host has a plan mode, write it there so the human can review and approve it in one click; otherwise write it in the conversation and into `plans/`. The plan's final step is always the standing wrap-up from the `projects` skill: log this cycle's unit in `units/YYYY-MM/<unit>/` (what was produced, links, numbers), replace `## Current status` in `next.md`, write the changelog with `cycle:` in place of `progress:`, copy every plan created this session into `plans/`, run the knowledge check, refresh these rules, and commit with a conventional message. A plan without that step is incomplete. Approval of the plan is approval of the whole session: execute it through to the commit hash without stopping, except for a decision only the human can make.

### While working

- Do the work; do not describe work for the human to do. Ask specifically for any tool or access you lack. When a step is genuinely yours to hand off, prepare everything around it first.
- When a `## Setup` item is met, tick its box in `README.md` and say so. The duty itself is never ticked: a kept cycle is a unit folder.
- Activity is not a kept cycle. A session that improves the machinery but produces no unit still leaves the cycle missed; say so.
- Ask before writing to `decisions/` or `learnings/`. They are the project's long-term memory and stay sparse.
- Project scaffolding never leaks into the codebase: no project name, `_projects/` path, plan or decision number in source, comments, or durable docs. Grep your diff before you finish.
