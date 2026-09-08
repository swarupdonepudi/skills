# Starting a project

A project is for work that will take more than one conversation. If the work fits in this session, do it; do not make a project for it.

## 1. Draft the brief from what you already know

Do not interview the human field by field. You have the conversation and the codebase; draft the brief from them and ask only for what you cannot infer, usually one or two things: the name, and what done looks like. Then show the draft and ask for a yes.

The brief has: a one-or-two-sentence description; the goal; the definition of done as a short list of checkable statements (these become checkboxes, and the count of ticked boxes is the project's progress, so write them as things that are either done or not, three to nine of them); scope, in and out; the repositories touched, by workspace folder name (default: this one); constraints you already know; optionally an owner.

Present it as a compact block and end with a single question: "Shall I create this?" If they edit, update and ask again.

## 2. Create it

From the repository that holds `_projects/` (or with `--repo-root` pointing there):

```bash
python3 <skill>/scripts/projects.py new \
  --name <slug> \
  --description "..." \
  --goal "..." \
  --done "first checkable statement,second,third" \
  --scope "..." \
  --repos "repo-a,repo-b" \
  [--owner <name>]
```

`new` prints the folder it created. On a repository's first project it also creates `_projects/` and its README. If `--owner` names an owner that has no file yet, `new` creates `_projects/owners/<name>.md` from the starter and tells you; offer to fill it in with the human.

Then open the new `README.md` and put anything from the brief that the flags did not carry (constraints, nuance in scope) into its sections. The brief should read as the human approved it.

## 3. Write the initial plan

`plans/001-initial-plan.md` exists with `status: pending`. Fill it: the objective, the approach, three to seven steps in dependency order, how each will be verified, the open questions, and, as the final step, the session wrap-up (every plan ends with it; see [wrap-up.md](wrap-up.md)). Steps are meaningful units of work, not a checklist of file edits. If your host has a plan mode, write the plan there and copy it into `plans/001-initial-plan.md` when approved.

## 4. Get the plan approved, then stop

Present the plan and ask for approval. Do not begin executing in this conversation unless the human explicitly says to continue now; if they do, the approval covers the whole plan through its wrap-up step, and you run it to the commit. By default a project is created and planned in one session and worked in the next; that boundary is what makes the resume protocol reliable.

When approved, set the plan's `status: in-progress` (or leave `pending` if work starts next session) and close with:

```
Created _projects/YYYYMMDD.NN.slug/. To continue in any conversation, drag its next.md in.
```

## Choosing an owner

Most projects need no named owner; the default character (or the adopter's `owners/default.md`) applies. Name one when the repository already has named owners, or when the human wants a distinct working style for this project. Never invent a persona the human did not ask for.

## Sub-projects

If, while drafting, a piece of the work is clearly large enough to resume on its own and could run in parallel, say so and create the parent first. Sub-projects come after, with `--parent`; see [sub-projects.md](sub-projects.md).
