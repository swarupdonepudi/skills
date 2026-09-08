# One repository or many

## Monorepo

`_projects/` lives at the root of the repository the work happens in. Projects, plans, changelogs, and code commit together. This is the simplest setup and needs nothing beyond `new`.

## A personal orchestration repository

When work spans several code repositories, `_projects/` lives in one repository of its own (a personal or team "work" repo) and the code repositories sit beside it in the same workspace. The project records are committed in the orchestration repo; code changes are committed in whichever repo they belong to, under that repo's conventions.

Two rules make this work across machines and people.

### Repositories are named, never pathed

The brief's `## Repositories` lists each repository by its workspace folder name:

```
## Repositories

- planton-platform
- stigmer
```

Never `/Users/me/scm/...` or `~/scm/...`. A machine path is true on one laptop and wrong on the next; a name is resolved by whoever opens the project, in whatever workspace they have. When you need to act in one of those repositories, find it by name among the workspace's roots and say which path you resolved it to.

### The CLI runs against the repository that holds `_projects/`

`projects.py` finds the repository root with `git rev-parse` from the current directory. In a multi-repo workspace your current directory is often a code repository, so pass the orchestration repo explicitly:

```bash
python3 <skill>/scripts/projects.py list --repo-root <path-to-orchestration-repo>
```

The resume file tells you which repository holds the project (it is the one the file lives in).

## The stale-checkout check covers every repository

Step 1 of the rules of engagement runs `git fetch` and a status check in this repository and in every repository the brief names. A project's records are only as true as the checkouts they describe; a code repo that is behind produces confidently wrong plans just as a stale `next.md` does.

## Committing in a multi-repo setup

At wrap-up, commit the project records in the orchestration repo and the code in each code repo, each under its own conventions. Name the code repositories and their commit hashes in the changelog so the history can be followed from one place.

## Teams

Several people, or several agents, working the same `_projects/` at once is normal. What keeps it safe: the stale-checkout check at resume; staging only the files you touched at wrap-up; per-session scratch files named per session and deleted at wrap-up; and sub-projects for work that genuinely runs in parallel, so two sessions do not edit one project's `next.md` at the same time.
