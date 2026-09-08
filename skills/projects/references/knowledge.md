# Knowledge: decisions and learnings

`decisions/` and `learnings/` are the project's long-term memory. Their value comes from being sparse: a folder with five entries that each changed how someone worked is read every session; a folder with fifty is skimmed once and ignored. So the rule is strict.

## Ask first, always

Never write to `decisions/` or `learnings/` without the human's yes. Propose the entry in one line ("Worth a learning: the migration must run in three phases because of the zero-downtime constraint. Write it?") and write only on approval. This holds even when the lesson seems obviously important; the human's judgment about what deserves permanence is part of what keeps the folders trustworthy.

`plans/`, `changelogs/`, and `next.md` you write freely; they are working records, not memory.

## The bar

An entry earns its place only when all of these are true:

- **Impact**: it affects the whole project or a major part of it.
- **Permanence**: it will still matter in a month.
- **Non-obvious**: a competent person would not assume it.
- **Reusable**: someone who was not in the session benefits.
- **Costly to forget**: forgetting it would cause rework or a wrong turn.

Not knowledge: "the build passed", "fixed a typo", "the templates use `$` placeholders", anything a reader can see by looking at the code.

Possibly knowledge, ask: "the API rate-limits above 100 requests a second and fails silently", "we chose JWT over sessions because the desktop app cannot hold a cookie", "do not run the migration with the old CLI; it corrupts the index".

## Decisions

A decision is a fork in the road that had real alternatives. `decisions/NNN-slug.md` per `assets/templates/decision.md`: the context (what was open and why it mattered), the decision in one or two sentences, the alternatives considered, and the consequences (what it makes easier, harder, and what would make us revisit). Number sequentially within the project.

## Learnings

A learning is something the project now knows that it did not. `learnings/NNN-slug.md` per `assets/templates/learning.md`, with `kind:` in the frontmatter:

- `guideline`: a pattern to apply consistently from now on.
- `wrong-assumption`: a premise that proved false and caused rework. Record what was believed, what is true, and how it was discovered.
- `dont-do`: an approach that failed and must not be retried. Record what was tried, what happened, and what to do instead.

Each entry: the lesson in plain words, the evidence (the command, the failure, the file), and the rule going forward.

## Three homes, not one

When a lesson clears the bar, place it where it will be read:

- About this project: `learnings/` or `decisions/`.
- About how the agent should work in this repository (a verification step, a communication preference, a repeated mistake): the owner file, `_projects/owners/<name>.md` or `owners/default.md`. Ask first, as with any knowledge.
- Doctrine that must outlive the project (a repository rule, a naming law, an architectural boundary): its durable home outside `_projects/`, this session. The project keeps a pointer. When the project is archived, doctrine that lives only inside it is archived with it, which is a leak in waiting.

## The wrap-up knowledge check

At every wrap-up, ask what the session taught that clears the bar, and propose entries by destination. Routine sessions produce nothing, and that is the expected outcome. The check exists so that the rare high-signal lesson is caught the day it happens, not rediscovered a month later.
