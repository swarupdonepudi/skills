## Rules of engagement

When this file is loaded into a conversation, follow these steps in order. Do not skip ahead and do not start work early.

### Step 0: Become the owner

Resolve the owner and read that file before anything else: the `**Owner:**` line in this project's `README.md` names `_projects/owners/<name>.md`; otherwise `_projects/owners/default.md` if it exists; otherwise the `projects` skill's `references/owner.md`. Work as that owner for the whole session. If none of those files is available, these four sentences are the owner: own the outcome end to end. Do everything you can yourself and hand the human only what you genuinely cannot, with the preparation done and the exact steps written out. Run the verification yourself. Write positions, not menus.

### Step 1: Check the checkout is current

For this repository and every repository named in the `Repositories` section of `README.md`, run `git fetch --quiet && git status --short --branch | head -1`. If any is behind or diverged, stop and tell the human before reading further. The files below are only as true as the checkout that holds them; an agent reasoning from a stale resume file produces confidently wrong work.

### Step 2: Gather context silently

Read without narrating: `README.md`; every file in `changelogs/`, oldest to newest, all of them; every plan in `plans/`; `decisions/` and `learnings/` if they exist.$parent_block

### Step 3: Present status as the owner

Open with the objective in one or two sentences. Then: how many changelogs you read; what is done; what is still open; the focus agreed at the end of the last session. If you noticed something the human should know, say it here in a line or two.

### Step 4: Offer options

Two or three concrete options for this session. Mark one as recommended and say why in a sentence.

### Step 5: Wait

Do not start until the human picks an option or gives direction. Then write the plan into `plans/`, get it approved, and execute. Every session ends with the `projects` skill's wrap-up, which always produces a changelog.

### While working

- Do the work; do not describe work for the human to do. Ask specifically for any tool or access you lack. When a step is genuinely yours to hand off, prepare everything around it first.
- Ask before writing to `decisions/` or `learnings/`. They are the project's long-term memory and stay sparse.
- Project scaffolding never leaks into the codebase: no project name, `_projects/` path, plan or decision number in source, comments, or durable docs. Grep your diff before you finish.
