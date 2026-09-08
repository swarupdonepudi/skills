# Sub-projects

A sub-project is a piece of a project that is large enough to be resumed on its own, spans sessions on its own, and could run in parallel with other pieces. It lives flat beside its parent, marked `sp.` in its name, and is linked to the parent by content, not by nesting.

| The work | Use |
|---|---|
| fits in one session, or is a checklist item | a step in the parent's plan |
| spans sessions on its own, has its own done-when, could run in parallel | a sub-project |

Example: a parent "cloud-provider-expansion" adds ten providers. Each provider is a sub-project: independently executable, several sessions each, its own definition of done. Ten agents could work ten of them at once.

## Creating one

The parent must exist and be active.

```bash
python3 <skill>/scripts/projects.py new \
  --name <slug> --description "..." --goal "..." [--done ...] [--owner <name>] \
  --parent <parent-folder>
```

`new` creates `YYYYMMDD.NN.sp.<slug>/` with:

- a brief whose identity list has `- **Parent:** [<parent>](../<parent>/)` and whose `## Repositories` is inherited from the parent unless you pass `--repos`;
- a `next.md` whose rules of engagement also read the parent's brief, knowledge, and three newest changelogs, and whose `## Where things are` lists the parent's paths;
- a row in the parent's `## Sub-projects` table and a bullet in the parent's `next.md` under `## Sub-projects`.

Draft the sub-project's brief the same way as any project (see [start.md](start.md)); it is narrower than the parent's, never a copy of it. The sub-project writes to its own `plans/`, `changelogs/`, `decisions/`, and `learnings/`; it reads the parent's knowledge but never writes into it.

Add the sub-project as one item in the parent's `## Done when` ("- [ ] oracle-provider sub-project completed"). Ticking it when the sub-project completes is how a parent's progress rolls up from its children.

## Working one

Resume the sub-project by its own `next.md`. The parent's context loads with it. When a sub-project learns something the parent or its siblings need, record it in the sub-project's `learnings/` and tell the human it should be promoted to the parent; do not write into the parent from a sub-project session unless asked.

Several agents on sibling sub-projects at once is the intended use. Each commits only its own project's files and its own code changes; the stale-checkout check at resume is what keeps parallel sessions from reasoning about a tree that has moved.

## Completing, holding, shelving

`move` on a sub-project updates its row in the parent's table. `move` on a parent refuses while any sub-project is active; finish or park the children first, or `--force`. A parent is normally completed last, after its sub-projects, with a final changelog that sums them up.

## The parent line

`new` writes `- **Parent:** [<folder>](../<folder>/)` into the sub-project's brief, and `list` and `move` read it. Keep the line intact when editing a sub-project's brief by hand.
