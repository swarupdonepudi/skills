# Why the framework is shaped this way

## The problem

Coding agents are excellent inside one conversation and amnesiac between them. Work that spans days stalls in a specific way: decisions get buried in a transcript nobody reopens; the next session re-derives context for ten minutes and still misses the constraint that mattered; an approach that failed last week is proposed again with confidence; and nobody can see, at a glance, what is in flight and what is done.

The fix is not a bigger context window. It is a place where the project's memory lives outside any conversation, in a shape the next session can load in seconds and trust.

## The eight ideas

1. **One file resumes a project.** `next.md` holds the current state and the rules for how a session opens. Drag it in and the agent knows where things stand. The rules are physically in the file, so it works in any agent, with or without this skill installed.
2. **Every session has the same shape.** Check the checkout is current, read everything silently, present status with progress, offer exactly three options with one recommended, wait for the pick, plan, then execute through the wrap-up and a commit. The human decides direction at the start; the agent carries the session to a committed end. Approving the plan is approving the session, so the human can approve and walk away.
3. **Every session ends with a changelog.** It is the project's history and the next session reads all of it. This is the single mechanism that makes context loss impossible; everything else builds on it. Progress rides along: the count of ticked done-when items in the brief, derived by the CLI, spoken at both ends of the session, snapshotted in each changelog, never stored anywhere else.
4. **The active list is the to-do list.** Finished work moves to `.completed/`, blocked work to `.on-hold/` with a written resume condition, deferred work to `.shelved/`. Every move is reversible and repairs every reference, so archiving costs nothing and the active list stays honest.
5. **Knowledge is sparse and permission-gated.** `decisions/` and `learnings/` hold only what is high impact, still true in a month, non-obvious, and reusable, and the agent asks before writing. Folders that fill with noise stop being read.
6. **Sub-projects are flat siblings.** A piece of work large enough to resume on its own gets its own folder beside the parent, marked `sp.`, linked by content. Work can run in parallel and inherit the parent's knowledge without directory nesting.
7. **Do first, plan before executing, never leak.** The agent does the work rather than describing it, writes and gets a plan approved before acting, and keeps every trace of project scaffolding out of the codebase.
8. **Every project has an owner.** The agent becomes a fixed operating character at resume, accountable for driving the project to done. Adopters shape that character in their own repository.

## Why each file has one job

The framework's earlier versions grew duplicate homes for the same information: a resume file that repeated every session's summary and grew to hundreds of lines, a plan registry that duplicated the filesystem and drifted, task folders beside plan folders. Each duplicate was one more thing that could lie.

The six-file model gives every fact one home: the brief in `README.md`, the state in `next.md`, the history in `changelogs/`, the intent in `plans/`, the rationale in `decisions/`, the lessons in `learnings/`. When you are about to write something, ask which of the six it is; if it is already written somewhere, link to it.

## Why the CLI is small

Folders, moves, link repair, and sequence numbers are mechanical and fragile: they should be done identically every time, by a script that can be tested. Everything else, the brief, the plan, the changelog, the decision to write a learning, is judgment and belongs to the agent. The CLI stays at four operations so that line stays visible.

## Where it comes from

This framework carried 350 or so projects to completion across two companies before it became a skill, run daily by people and agents in monorepos and in personal orchestration repos that steer work across many code repositories. The ideas above are the ones that survived that use; the ones that did not are noted in [extending.md](extending.md) for adopters who want them.
