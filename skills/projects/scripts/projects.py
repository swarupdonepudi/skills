#!/usr/bin/env python3
"""
projects.py -- the command line behind the `projects` agent skill.

One file, four operations, no dependencies beyond Python 3.9's standard
library. The agent runs it; a person can too.

    projects.py new      --name <slug> --description ... --goal ... [--parent <folder>] [--owner <name>]
    projects.py new      --standing <slug> --cadence daily|mon-sat|weekdays|weekly --description ... --duty ...
    projects.py move     <folder> --to completed|on-hold|shelved|active [--reason ...] [--resume-when ...] [--dry-run]
    projects.py list     [--all] [--stale N] [--owner <name>] [--json]
    projects.py refresh  <folder> | --all
    projects.py selftest

Every subcommand accepts --repo-root (default: `git rev-parse --show-toplevel`
from the current directory) and --projects-dir (default: `_projects`).

Why one file rather than one script per operation: the operations share the
same ground -- finding the repo root, parsing folder names, reading the Owner
and Parent lines, rendering templates -- and splitting them would duplicate
that ground in every file. One surface, one `--help`, one place to fix a bug.

Design notes that matter when changing this file:

* The CLI owns exactly two things inside a project's files: the text between
  the marker blocks it wrote (rules of engagement, status banner) and the
  paths and links a move invalidates. Everything else in a project is the
  agent's and the human's. A folder without the marker blocks is not a
  project this skill manages; the CLI says so and stops rather than guess.
* Progress is derived, never stored: the count of ticked boxes under
  `## Done when` in the brief. `list` computes it; nothing writes it.
* A standing project is a duty that never completes. It lives at
  `<state dir>/standing/<slug>/` (no date, no sequence), its `folder` is
  `standing/<slug>`, and that is also how a Parent line and the command line
  name it. The location decides that a project is standing; the brief's
  `**Kind:** standing` line tells a human reader. It has no progress: `list`
  reports its cadence, its last unit, and how many cycle days it is overdue.
* Markdown templates are rendered with `string.Template` (`$var`), never
  `str.format`, so braces in markdown are safe.
* Link repair on a move is computed from the geometry of the tree, not from
  text patterns: a relative link is rewritten only when it stops resolving
  because of this move, and only to the place it used to point at. That makes
  the pass exact at any depth, idempotent, and reversible.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from string import Template
from typing import Dict, Iterable, List, Optional, Tuple

# --------------------------------------------------------------------------
# Constants: where things live and how they are named
# --------------------------------------------------------------------------

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_ROOT / "assets" / "templates"

DEFAULT_PROJECTS_DIR = "_projects"

# Lifecycle state -> the folder under the projects dir that holds it. The
# empty string is the active root itself.
STATES: Dict[str, str] = {
    "active": "",
    "completed": ".completed",
    "on-hold": ".on-hold",
    "shelved": ".shelved",
}
STATUS_WORDS = {"active": "Active", "completed": "Completed", "on-hold": "On hold", "shelved": "Shelved"}

RESUME_FILE = "next.md"
OWNERS_DIR = "owners"

# Standing projects live in this folder inside each state folder:
# `_projects/standing/<slug>/`, `_projects/.on-hold/standing/<slug>/`, and so
# on. Never under `.completed/`: a duty is kept, paused, or stopped, never done.
STANDING_DIR = "standing"
CADENCES = ("daily", "mon-sat", "weekdays", "weekly")

FOLDER_NAME = re.compile(r"^(?P<date>\d{8})\.(?P<seq>\d{2})\.(?P<sp>sp\.)?(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STANDING_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")

# Marker blocks this CLI owns inside README.md and the resume file.
ROE_START, ROE_END = "<!-- projects:roe:start -->", "<!-- projects:roe:end -->"
STATUS_START, STATUS_END = "<!-- projects:status:start -->", "<!-- projects:status:end -->"

# The two identity lines in the brief that the CLI reads. `new` writes them as
# list items; keep the form when editing a brief by hand.
OWNER_LINE = re.compile(r"^- \*\*Owner:\*\*\s*(?P<name>[A-Za-z0-9._-]+)", re.MULTILINE)
PARENT_LINE = re.compile(r"^- \*\*Parent:\*\*\s*\[(?P<folder>[^\]]+)\]\([^)]*\)", re.MULTILINE)
# A standing project's brief also carries its cadence. The Created line is
# read only where the folder name carries no date.
CADENCE_LINE = re.compile(r"^- \*\*Cadence:\*\*\s*(?P<cadence>[a-z-]+)", re.MULTILINE)
CREATED_LINE = re.compile(r"^- \*\*Created:\*\*\s*(?P<date>\d{4}-\d{2}-\d{2})", re.MULTILINE)
UNIT_DATE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})")

# A done-when item: `- [ ] text` or `- [x] text` under `## Done when`.
CHECKBOX = re.compile(r"^- \[(?P<mark>[ xX])\] ", re.MULTILINE)

MARKDOWN_LINK = re.compile(r"\]\((?P<target>[^)\s]+)\)")
FRONTMATTER_DATE = re.compile(r"^date:\s*[\"']?(\d{4}-\d{2}-\d{2})", re.MULTILINE)

BINARY_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".pdf", ".zip", ".gz", ".tar",
    ".bz2", ".7z", ".woff", ".woff2", ".ttf", ".eot", ".pyc", ".pyo", ".so", ".dylib", ".dll",
    ".exe", ".lock",
})
LINK_BEARING_EXTENSIONS = frozenset({".md", ".mdc"})


# --------------------------------------------------------------------------
# Small shared helpers
# --------------------------------------------------------------------------

def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def today() -> str:
    return date.today().strftime("%Y-%m-%d")


def render(template_name: str, **variables: str) -> str:
    """Render a template from assets/templates with `$var` substitution.
    Unknown variables are left in place rather than raising, so a template
    can carry `$` for the agent to fill later."""
    path = TEMPLATES_DIR / template_name
    if not path.is_file():
        fail(f"template missing: {path}")
    return Template(path.read_text(encoding="utf-8")).safe_substitute(**variables)


def read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return False
    try:
        with open(path, "rb") as handle:
            return b"\x00" not in handle.read(8192)
    except OSError:
        return False


def posix(path: Path) -> str:
    return path.as_posix()


def replace_between(text: str, start: str, end: str, replacement: str) -> Optional[str]:
    """Replace the content between two marker lines, keeping the markers.
    Returns None when either marker is missing."""
    start_idx = text.find(start)
    end_idx = text.find(end, start_idx + len(start)) if start_idx != -1 else -1
    if start_idx == -1 or end_idx == -1:
        return None
    inner = f"\n{replacement}\n" if replacement else "\n"
    return text[: start_idx + len(start)] + inner + text[end_idx:]


def bullets(items: Iterable[str], default: str, prefix: str = "- ") -> str:
    cleaned = [item.strip() for item in items if item.strip()]
    return "\n".join(f"{prefix}{item}" for item in cleaned) if cleaned else default


def section_body(text: str, heading: str) -> Optional[str]:
    """Return the body of a `## heading` section (up to the next `## `)."""
    match = re.search(rf"^## {re.escape(heading)}\s*\n(?P<body>.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group("body").strip() if match else None


def checkbox_count(text: str, heading: str) -> Tuple[int, int]:
    """(ticked, total) checkboxes under a `## heading` section."""
    body = section_body(text, heading) or ""
    marks = [m.group("mark") for m in CHECKBOX.finditer(body)]
    return sum(1 for mark in marks if mark != " "), len(marks)


def is_cycle_day(cadence: str, day: date) -> bool:
    """Whether a daily-style cadence expects a cycle on this day."""
    if cadence == "mon-sat":
        return day.weekday() != 6
    if cadence == "weekdays":
        return day.weekday() < 5
    return True


def overdue_days(cadence: str, last: date, on: date) -> int:
    """How many cycle days a standing project is overdue on `on`.

    Daily, mon-sat, and weekdays: count the days the cadence expects a cycle,
    strictly after the last unit and strictly before `on`. Today is never
    overdue yet; a unit logged yesterday is on time. Weekly: a cycle is due
    seven days after the last unit, and each day past that is one day overdue.
    An unknown cadence is treated as daily."""
    gap = (on - last).days
    if gap <= 1:
        return 0
    if cadence == "weekly":
        return max(0, gap - 7)
    return sum(1 for offset in range(1, gap) if is_cycle_day(cadence, date.fromordinal(last.toordinal() + offset)))


# --------------------------------------------------------------------------
# The workspace: a repo root and its projects directory
# --------------------------------------------------------------------------

def resolve_repo_root(explicit: Optional[str]) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not root.is_dir():
            fail(f"--repo-root is not a directory: {root}")
        return root
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return Path(result.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        fail("not inside a git repository; pass --repo-root (in a multi-repo workspace, the repo that holds the projects folder)")
        raise  # unreachable; keeps type checkers calm


@dataclass
class Project:
    """One project folder, wherever it currently lives."""

    workspace: "Workspace"
    state: str
    path: Path

    @property
    def is_standing(self) -> bool:
        """A standing project lives in a `standing/` folder inside a state folder."""
        return self.path.parent.name == STANDING_DIR and self.path.parent.parent == self.workspace.state_dir(self.state)

    @property
    def folder(self) -> str:
        """The name the CLI, Parent lines, and sub-project tables use:
        `YYYYMMDD.NN.slug` for a project, `standing/<slug>` for a standing one."""
        return f"{STANDING_DIR}/{self.path.name}" if self.is_standing else self.path.name

    @property
    def rel(self) -> str:
        """Path relative to the repo root, the form written into project files."""
        return posix(self.path.relative_to(self.workspace.repo_root))

    @property
    def parts(self) -> Optional[re.Match]:
        return FOLDER_NAME.match(self.folder)

    @property
    def is_sub_project(self) -> bool:
        parts = self.parts
        return bool(parts and parts.group("sp"))

    @property
    def slug(self) -> str:
        parts = self.parts
        return parts.group("slug") if parts else self.path.name

    @property
    def created(self) -> Optional[date]:
        parts = self.parts
        try:
            if parts:
                return datetime.strptime(parts.group("date"), "%Y%m%d").date()
            match = CREATED_LINE.search(read_text(self.readme) or "")
            return datetime.strptime(match.group("date"), "%Y-%m-%d").date() if match else None
        except ValueError:
            return None

    @property
    def readme(self) -> Path:
        return self.path / "README.md"

    @property
    def resume_file(self) -> Path:
        return self.path / RESUME_FILE

    @property
    def owner(self) -> Optional[str]:
        match = OWNER_LINE.search(read_text(self.readme) or "")
        return match.group("name") if match else None

    @property
    def parent_folder(self) -> Optional[str]:
        match = PARENT_LINE.search(read_text(self.readme) or "")
        return match.group("folder").strip() if match else None

    @property
    def progress(self) -> Optional[Tuple[int, int]]:
        """(ticked, total) done-when items. The brief is the only source. A
        standing project never completes, so it has no progress: None."""
        if self.is_standing:
            return None
        return checkbox_count(read_text(self.readme) or "", "Done when")

    @property
    def cadence(self) -> Optional[str]:
        match = CADENCE_LINE.search(read_text(self.readme) or "")
        return match.group("cadence") if match else None

    @property
    def setup(self) -> Optional[Tuple[int, int]]:
        """(ticked, total) one-time setup items of a standing project, or None
        when its brief has no `## Setup` list. Never a completion measure."""
        ticked, total = checkbox_count(read_text(self.readme) or "", "Setup")
        return (ticked, total) if total else None

    def last_unit(self) -> Tuple[Optional[str], Optional[date]]:
        """The newest unit of a standing project: (name, date).

        Units live at `units/YYYY-MM/<unit>/`. A unit's date is the date its
        name starts with (`2026-10-31`, `2026-10-31-ep12`), else the newest
        file inside it. With no units yet: (None, last activity)."""
        newest: Tuple[Optional[str], Optional[date]] = (None, None)
        units = self.path / "units"
        if units.is_dir():
            for month in units.iterdir():
                if not month.is_dir():
                    continue
                for unit in month.iterdir():
                    if not unit.is_dir():
                        continue
                    found: Optional[date] = None
                    match = UNIT_DATE.match(unit.name)
                    if match:
                        try:
                            found = datetime.strptime(match.group("date"), "%Y-%m-%d").date()
                        except ValueError:
                            found = None
                    if found is None:
                        found = _newest_mtime(unit) or date.fromtimestamp(unit.stat().st_mtime)
                    if newest[1] is None or (found, unit.name) > (newest[1], newest[0] or ""):
                        newest = (unit.name, found)
        if newest[0] is None:
            return None, self.last_activity
        return newest

    @property
    def last_activity(self) -> Optional[date]:
        """The newest changelog's date, else the newest file's mtime."""
        newest: Optional[date] = None
        changelogs = self.path / "changelogs"
        if changelogs.is_dir():
            for entry in changelogs.iterdir():
                if entry.suffix != ".md":
                    continue
                text = read_text(entry) or ""
                match = FRONTMATTER_DATE.search(text)
                if match:
                    try:
                        found = datetime.strptime(match.group(1), "%Y-%m-%d").date()
                    except ValueError:
                        continue
                    if newest is None or found > newest:
                        newest = found
        if newest:
            return newest
        return _newest_mtime(self.path) or self.created


def _newest_mtime(folder: Path) -> Optional[date]:
    latest_mtime = 0.0
    for root, _dirs, files in os.walk(folder):
        for name in files:
            try:
                latest_mtime = max(latest_mtime, (Path(root) / name).stat().st_mtime)
            except OSError:
                continue
    return date.fromtimestamp(latest_mtime) if latest_mtime else None


class Workspace:
    def __init__(self, repo_root: Path, projects_dir_name: str):
        self.repo_root = repo_root
        self.projects_dir_name = projects_dir_name
        self.projects_dir = repo_root / projects_dir_name

    def state_dir(self, state: str) -> Path:
        return self.projects_dir / STATES[state] if STATES[state] else self.projects_dir

    def projects(self, states: Iterable[str] = ("active",)) -> List[Project]:
        found: List[Project] = []
        for state in states:
            folder = self.state_dir(state)
            if not folder.is_dir():
                continue
            for entry in sorted(folder.iterdir()):
                if entry.is_dir() and FOLDER_NAME.match(entry.name):
                    found.append(Project(self, state, entry))
            standing = folder / STANDING_DIR
            if standing.is_dir():
                for entry in sorted(standing.iterdir()):
                    if entry.is_dir() and STANDING_SLUG.match(entry.name):
                        found.append(Project(self, state, entry))
        return found

    def find(self, folder: str) -> Optional[Project]:
        """Locate a project by folder name in any lifecycle state. A standing
        project is found by `standing/<slug>` or by its bare slug."""
        relative = folder
        if not FOLDER_NAME.match(folder) and not folder.startswith(f"{STANDING_DIR}/"):
            relative = f"{STANDING_DIR}/{folder}"
        for state in STATES:
            candidate = self.state_dir(state) / relative
            if candidate.is_dir():
                return Project(self, state, candidate)
        return None

    def next_sequence(self, date_prefix: str) -> int:
        """Sequence numbers are unique per day across every state, so a project
        created and archived the same day cannot collide with the next one."""
        highest = 0
        for project in self.projects(STATES.keys()):
            parts = project.parts
            if parts and parts.group("date") == date_prefix:
                highest = max(highest, int(parts.group("seq")))
        return highest + 1

    def sub_projects_of(self, folder: str, states: Iterable[str] = ("active",)) -> List[Project]:
        return [p for p in self.projects(states) if p.is_sub_project and p.parent_folder == folder]

    def ensure_projects_dir(self) -> bool:
        """Create the projects folder and its README on first use. Never
        overwrites an existing README: an adopter's own text wins."""
        created = False
        if not self.projects_dir.is_dir():
            self.projects_dir.mkdir(parents=True)
            created = True
        readme = self.projects_dir / "README.md"
        if not readme.exists():
            readme.write_text(render("projects-readme.md"), encoding="utf-8")
            created = True
        return created


# --------------------------------------------------------------------------
# Rules of engagement rendering (shared by `new` and `refresh`)
# --------------------------------------------------------------------------

PARENT_BLOCK = (
    " Then the parent project named by the `**Parent:**` line in `README.md`: its `README.md`, "
    "its `decisions/` and `learnings/` if they exist, and its three newest changelogs."
)


def render_rules_of_engagement(is_sub_project: bool, is_standing: bool = False) -> str:
    if is_standing:
        return render("standing-rules-of-engagement.md").rstrip("\n")
    return render("rules-of-engagement.md", parent_block=PARENT_BLOCK if is_sub_project else "").rstrip("\n")


def relative_link(source_dir: Path, target_dir: Path) -> str:
    """A relative markdown link from one project folder to another, ending in
    a slash: `../20260908.01.foo/` beside it, `../../standing/show/` from a
    standing project, `../standing/show/` to one."""
    return Path(os.path.relpath(target_dir, source_dir)).as_posix() + "/"


# --------------------------------------------------------------------------
# new
# --------------------------------------------------------------------------

def cmd_new(args: argparse.Namespace) -> None:
    workspace = Workspace(resolve_repo_root(args.repo_root), args.projects_dir)

    if args.standing:
        _new_standing(workspace, args)
        return
    if not args.name:
        fail("give --name <slug> for a project, or --standing <slug> for a standing project")
    if not args.goal:
        fail("--goal is required: what done looks like at the highest level")
    if args.cadence or args.duty or args.loop or args.setup:
        fail("--cadence, --duty, --loop and --setup belong to a standing project; use --standing <slug>")
    if not SLUG.match(args.name):
        fail(f"--name must be kebab-case (letters, digits, single hyphens): got '{args.name}'")
    if args.owner and not SLUG.match(args.owner):
        fail(f"--owner must be kebab-case: got '{args.owner}'")

    parent: Optional[Project] = None
    if args.parent:
        parent = workspace.find(args.parent)
        if parent is None:
            fail(f"parent project not found in any state: {args.parent}")
        if parent.state != "active":
            fail(f"parent project is {STATUS_WORDS[parent.state].lower()}; move it back to active before adding sub-projects")

    bootstrapped = workspace.ensure_projects_dir()

    date_prefix = date.today().strftime("%Y%m%d")
    sequence = workspace.next_sequence(date_prefix)
    marker = "sp." if parent else ""
    folder = f"{date_prefix}.{sequence:02d}.{marker}{args.name}"
    project_path = workspace.projects_dir / folder
    if project_path.exists():
        fail(f"already exists: {project_path}")

    project = Project(workspace, "active", project_path)
    rel = posix(project_path.relative_to(workspace.repo_root))

    # Inherit the repository list from the parent when the caller gave none;
    # a sub-project almost always works in the same repos as its parent.
    repos = [r for r in (args.repos or "").split(",") if r.strip()]
    if not repos and parent:
        inherited = section_body(read_text(parent.readme) or "", "Repositories")
        repositories = inherited or "- this repository"
    else:
        repositories = bullets(repos, "- this repository")

    identity_lines = ""
    if args.owner:
        identity_lines += f"- **Owner:** {args.owner}\n"
    if parent:
        identity_lines += f"- **Parent:** [{parent.folder}]({relative_link(project_path, parent.path)})\n"

    project_path.mkdir()
    (project_path / "plans").mkdir()
    (project_path / "changelogs").mkdir()

    project.readme.write_text(render(
        "README.md",
        slug=args.name,
        description=args.description.strip(),
        identity_lines=identity_lines,
        date=today(),
        goal=args.goal.strip(),
        done=bullets((args.done or "").split(","), "- [ ] Define with the human before approving the first plan.", prefix="- [ ] "),
        scope=args.scope.strip() if args.scope else "- Define with the human before approving the first plan.",
        repositories=repositories,
    ), encoding="utf-8")

    parent_paths = ""
    if parent:
        parent_paths = f"- Parent brief: `{parent.rel}/README.md`\n- Parent knowledge: `{parent.rel}/decisions/`, `{parent.rel}/learnings/`, `{parent.rel}/changelogs/`\n"
    (project_path / "next.md").write_text(render(
        "next.md",
        slug=args.name,
        rules_of_engagement=render_rules_of_engagement(is_sub_project=bool(parent)),
        rel=rel,
        parent_paths=parent_paths,
        date=today(),
    ), encoding="utf-8")

    (project_path / "plans" / "001-initial-plan.md").write_text(render(
        "plan.md", date=today(), number="001", title="Initial plan", objective=args.goal.strip(),
    ), encoding="utf-8")

    owner_created = _ensure_owner_file(workspace, args.owner)

    if parent:
        _register_sub_project_with_parent(parent, project, args.description.strip())

    print(f"created {rel}")
    if bootstrapped:
        print(f"  bootstrapped {workspace.projects_dir_name}/ (README written once; edit it freely)")
    print("  README.md            the brief")
    print("  next.md              the resume file; drag it into a conversation to continue")
    print("  plans/001-initial-plan.md   pending approval")
    print("  changelogs/          one entry per session, written at wrap-up")
    if parent:
        print(f"  parent {parent.folder}: sub-project table and next file updated")
    if owner_created:
        print(f"  owner file created from the starter: {posix(owner_created.relative_to(workspace.repo_root))}")


def _new_standing(workspace: Workspace, args: argparse.Namespace) -> None:
    """Create `_projects/standing/<slug>/`: a duty kept true, never completed.
    The same files as a project, from the standing templates, plus `units/`
    (one folder per kept cycle) and `playbooks/` (the routine)."""
    slug = args.standing
    if args.name:
        fail("give either --name (a project) or --standing (a standing project), not both")
    if not STANDING_SLUG.match(slug):
        fail(f"--standing must be lowercase letters, digits and hyphens, starting with a letter or digit: got '{slug}'")
    if not args.cadence:
        fail(f"--cadence is required for a standing project: one of {', '.join(CADENCES)}")
    if not args.duty:
        fail("--duty is required for a standing project: the condition kept true, in one or two sentences")
    if args.parent:
        fail("a standing project cannot be a sub-project; its own sub-projects name it with --parent standing/<slug>")
    if args.done or args.goal:
        fail("a standing project has no goal or done-when list: it never completes. State the condition kept true with --duty, and one-time work with --setup")
    if args.owner and not SLUG.match(args.owner):
        fail(f"--owner must be kebab-case: got '{args.owner}'")
    existing = workspace.find(f"{STANDING_DIR}/{slug}")
    if existing is not None:
        fail(f"a standing project with this name already exists: {existing.rel}")

    bootstrapped = workspace.ensure_projects_dir()
    project_path = workspace.projects_dir / STANDING_DIR / slug
    project_path.mkdir(parents=True)
    for name in ("plans", "changelogs", "units", "playbooks"):
        (project_path / name).mkdir()
    project = Project(workspace, "active", project_path)
    rel = project.rel

    setup_items = [item for item in (args.setup or "").split(",") if item.strip()]
    setup_section = ""
    if setup_items:
        setup_section = (
            "## Setup\n\nOne-time work before or beside the loop. Tick each item as it is met. "
            "It is reported as setup x of y, never as completion.\n\n"
            + bullets(setup_items, "", prefix="- [ ] ") + "\n\n"
        )

    project.readme.write_text(render(
        "standing-README.md",
        slug=slug,
        description=args.description.strip(),
        cadence=args.cadence,
        identity_lines=f"- **Owner:** {args.owner}\n" if args.owner else "",
        date=today(),
        duty=args.duty.strip(),
        loop=args.loop.strip() if args.loop else "- Define with the human before approving the first plan: what one cycle produces, where its unit is logged, and which playbook runs it.",
        setup_section=setup_section,
        scope=args.scope.strip() if args.scope else "- Define with the human before approving the first plan.",
        repositories=bullets([r for r in (args.repos or "").split(",") if r.strip()], "- this repository"),
    ), encoding="utf-8")

    project.resume_file.write_text(render(
        "standing-next.md",
        slug=slug,
        rules_of_engagement=render_rules_of_engagement(is_sub_project=False, is_standing=True),
        rel=rel,
        date=today(),
    ), encoding="utf-8")

    (project_path / "plans" / "001-initial-plan.md").write_text(render(
        "plan.md", date=today(), number="001", title="Initial plan",
        objective=f"Set up the duty and keep its first cycle. The duty: {args.duty.strip()}",
    ), encoding="utf-8")

    owner_created = _ensure_owner_file(workspace, args.owner)

    print(f"created {rel}")
    if bootstrapped:
        print(f"  bootstrapped {workspace.projects_dir_name}/ (README written once; edit it freely)")
    print(f"  README.md            the brief: the duty, cadence {args.cadence}, the loop")
    print("  next.md              the resume file; fixed size, drag it into a conversation to continue")
    print("  plans/001-initial-plan.md   pending approval")
    print("  playbooks/           the routine, one file per procedure")
    print("  units/YYYY-MM/<unit>/   one folder per kept cycle")
    print("  changelogs/          one entry per session, written at wrap-up")
    if owner_created:
        print(f"  owner file created from the starter: {posix(owner_created.relative_to(workspace.repo_root))}")


def _ensure_owner_file(workspace: Workspace, owner: Optional[str]) -> Optional[Path]:
    if not owner:
        return None
    owners_dir = workspace.projects_dir / OWNERS_DIR
    owner_file = owners_dir / f"{owner}.md"
    if owner_file.exists():
        return None
    owners_dir.mkdir(exist_ok=True)
    owner_file.write_text(render("owner.md", name=owner), encoding="utf-8")
    return owner_file


def _register_sub_project_with_parent(parent: Project, sub: Project, description: str) -> None:
    """Add the sub-project to the parent's brief (a table row) and to the
    parent's resume file (a bullet), creating the sections on first use."""
    readme_text = read_text(parent.readme)
    if readme_text is not None:
        row = f"| [{sub.folder}]({relative_link(parent.path, sub.path)}) | Active | {description} |"
        parent.readme.write_text(_append_table_row(readme_text, "Sub-projects", "| Sub-project | Status | Description |\n|---|---|---|", row), encoding="utf-8")

    resume_text = read_text(parent.resume_file)
    if resume_text is not None:
        entry = f"- `{sub.rel}/{RESUME_FILE}`: {description}"
        parent.resume_file.write_text(_append_to_section(resume_text, "Sub-projects", entry), encoding="utf-8")


def _append_table_row(text: str, heading: str, table_header: str, row: str) -> str:
    lines = text.rstrip("\n").split("\n")
    heading_line = f"## {heading}"
    if heading_line not in lines:
        section = ["", heading_line, "", table_header, row]
        # A brief ends with its "Resume" instructions; a new section belongs
        # before them so the resume line stays last, where a reader expects it.
        if "## Resume" in lines:
            at = lines.index("## Resume")
            lines[at:at] = section[1:] + [""]
            return "\n".join(lines) + "\n"
        return "\n".join(lines + section) + "\n"
    start = lines.index(heading_line)
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    last_row = None
    for index in range(start + 1, end):
        if lines[index].startswith("|"):
            last_row = index
    if last_row is None:
        lines[start + 1:start + 1] = ["", table_header, row]
    else:
        lines.insert(last_row + 1, row)
    return "\n".join(lines) + "\n"


def _append_to_section(text: str, heading: str, entry: str) -> str:
    lines = text.rstrip("\n").split("\n")
    heading_line = f"## {heading}"
    if heading_line not in lines:
        return "\n".join(lines) + f"\n\n{heading_line}\n\n{entry}\n"
    start = lines.index(heading_line)
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    lines.insert(end, entry)
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# move
# --------------------------------------------------------------------------

@dataclass
class Edit:
    path: Path        # where the file will be after the move
    before: str
    after: str
    note: str


def cmd_move(args: argparse.Namespace) -> None:
    workspace = Workspace(resolve_repo_root(args.repo_root), args.projects_dir)
    project = workspace.find(args.folder)
    if project is None:
        fail(f"project not found in any state: {args.folder}")
    if project.state == args.to:
        fail(f"{project.folder} is already {STATUS_WORDS[args.to].lower()}")
    if project.is_standing and args.to == "completed":
        fail(
            f"{project.folder} is a standing project: a duty is never completed. "
            "Pause it with --to on-hold, or stop it with --to shelved."
        )
    if args.to == "on-hold" and not args.resume_when:
        fail("--resume-when is required when putting a project on hold: what has to happen before it resumes?")
    if args.to in ("on-hold", "shelved") and not args.reason:
        fail(f"--reason is required when moving a project to {args.to}")

    if args.to != "active" and not args.force:
        active_subs = workspace.sub_projects_of(project.folder)
        if active_subs:
            names = "\n  ".join(p.folder for p in active_subs)
            fail(
                f"{project.folder} has active sub-projects:\n  {names}\n"
                "Move them first (or with it), or pass --force to leave them active with a parent that is no longer."
            )

    old_abs = project.path
    new_abs = workspace.state_dir(args.to) / project.folder
    if new_abs.exists():
        fail(f"target already exists: {new_abs}")
    for name in ("README.md", RESUME_FILE):
        text = read_text(old_abs / name)
        if text is None or STATUS_START not in text or STATUS_END not in text:
            fail(f"{project.folder}/{name} has no status marker block; this folder was not created by the projects skill")

    edits = _plan_move_edits(workspace, project, old_abs, new_abs, args)

    if args.to == "completed" and project.progress:
        ticked, total = project.progress
        if total and ticked < total:
            print(f"note: {total - ticked} of {total} done-when items are still unticked in README.md")

    verb = "would move" if args.dry_run else "moving"
    print(f"{verb} {posix(old_abs.relative_to(workspace.repo_root))} -> {posix(new_abs.relative_to(workspace.repo_root))}")
    for edit in edits:
        print(f"  {posix(edit.path.relative_to(workspace.repo_root))}: {edit.note}")
    if not edits:
        print("  no file changes needed")
    if args.dry_run:
        print("dry run: nothing written")
        return

    new_abs.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(old_abs), str(new_abs))
    for edit in edits:
        edit.path.write_text(edit.after, encoding="utf-8")
    # A `standing/` folder left empty by the move goes too; `new` and the next
    # move recreate it when needed.
    if project.is_standing and old_abs.parent.is_dir() and not any(old_abs.parent.iterdir()):
        old_abs.parent.rmdir()
    print(f"done: {project.folder} is now {STATUS_WORDS[args.to].lower()}")


def _plan_move_edits(workspace: Workspace, project: Project, old_abs: Path, new_abs: Path, args: argparse.Namespace) -> List[Edit]:
    """Compute every file change the move needs, against the tree as it will
    be after the move, without moving anything. The same computation serves
    --dry-run and the real run, which is what keeps dry-run honest."""

    def final_path(current: Path) -> Path:
        return new_abs / current.relative_to(old_abs) if _is_under(current, old_abs) else current

    def original_path(final: Path) -> Path:
        return old_abs / final.relative_to(new_abs) if _is_under(final, new_abs) else final

    def exists_after(final: Path) -> bool:
        if _is_under(final, new_abs):
            remainder = final.relative_to(new_abs)
            return (old_abs / remainder).exists() or final.exists()
        if _is_under(final, old_abs):
            return False
        return final.exists()

    old_rel = posix(old_abs.relative_to(workspace.repo_root))
    new_rel = posix(new_abs.relative_to(workspace.repo_root))
    # Repo-root-relative references are location independent, so a literal
    # replacement is exact -- provided the match stops at a path boundary, so
    # `_projects/foo` never rewrites `_projects/foo-bar`.
    literal = re.compile(re.escape(old_rel) + r"(?![A-Za-z0-9._-])")

    edits: List[Edit] = []
    for root, dirs, files in os.walk(workspace.projects_dir):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            current = Path(root) / name
            if not is_text_file(current):
                continue
            before = read_text(current)
            if before is None:
                continue
            final = final_path(current)
            after, literal_count = literal.subn(new_rel, before)
            link_count = 0
            if current.suffix.lower() in LINK_BEARING_EXTENSIONS:
                after, link_count = _rewrite_links(after, final, original_path(final), old_abs, new_abs, exists_after)
            notes = []
            if literal_count:
                notes.append(f"{literal_count} path reference{'s' if literal_count != 1 else ''}")
            if link_count:
                notes.append(f"{link_count} relative link{'s' if link_count != 1 else ''}")
            if after != before:
                edits.append(Edit(final, before, after, ", ".join(notes) or "updated"))

    # The banner in the moved project's brief and resume file. These files may
    # already be in `edits` from the link pass; fold the banner into that edit.
    banner = _status_banner(args)
    for name in ("README.md", RESUME_FILE):
        current = old_abs / name
        final = final_path(current)
        existing = next((e for e in edits if e.path == final), None)
        text = existing.after if existing else (read_text(current) or "")
        updated, note = _apply_banner(text, banner)
        if updated == text:
            continue
        if existing:
            existing.after = updated
            existing.note += f", {note}"
        else:
            edits.append(Edit(final, text, updated, note))

    # A sub-project's row in its parent's table.
    if project.is_sub_project and project.parent_folder:
        parent = workspace.find(project.parent_folder)
        if parent and parent.readme.is_file():
            final = final_path(parent.readme)
            existing = next((e for e in edits if e.path == final), None)
            text = existing.after if existing else (read_text(parent.readme) or "")
            updated = _update_table_status(text, project.folder, STATUS_WORDS[args.to])
            if updated != text:
                if existing:
                    existing.after = updated
                    existing.note += ", sub-project status"
                else:
                    edits.append(Edit(final, text, updated, "sub-project status"))
    return edits


def _is_under(path: Path, ancestor: Path) -> bool:
    try:
        path.relative_to(ancestor)
        return True
    except ValueError:
        return False


def _rewrite_links(text: str, final: Path, original: Path, old_abs: Path, new_abs: Path, exists_after) -> Tuple[str, int]:
    """Re-point relative markdown links that this move breaks.

    For each link: if it still resolves in the after-move tree, leave it. If it
    used to point inside the moved project, point it at the project's new
    location. If the file itself moved and the link pointed at something that
    stays where it is, recompute the relative path from the new location.
    Anything else is a link that was already broken; it is left visible."""
    count = 0

    def adjust(match: re.Match) -> str:
        nonlocal count
        target = match.group("target")
        if "://" in target or target.startswith(("/", "#", "mailto:")):
            return match.group(0)
        path_part, anchor = (target.split("#", 1) + [""])[:2]
        if not path_part:
            return match.group(0)
        final_target = Path(os.path.normpath(final.parent / path_part))
        if exists_after(final_target):
            return match.group(0)
        original_target = Path(os.path.normpath(original.parent / path_part))
        if _is_under(original_target, old_abs):
            new_target = new_abs / original_target.relative_to(old_abs)
        elif original != final and exists_after(original_target):
            new_target = original_target
        else:
            return match.group(0)
        relative = Path(os.path.relpath(new_target, final.parent)).as_posix()
        if path_part.endswith("/") and not relative.endswith("/"):
            relative += "/"
        count += 1
        return f"]({relative}{'#' + anchor if anchor else ''})"

    return MARKDOWN_LINK.sub(adjust, text), count


def _status_banner(args: argparse.Namespace) -> str:
    stamp = today()
    if args.to == "completed":
        return f"> **Status: Completed** ({stamp})"
    if args.to == "on-hold":
        reason = f" {args.reason.strip().rstrip('.')}." if args.reason else ""
        return f"> **Status: On hold** ({stamp}).{reason}\n> **Resume when:** {args.resume_when.strip()}"
    if args.to == "shelved":
        reason = f" {args.reason.strip().rstrip('.')}." if args.reason else ""
        return f"> **Status: Shelved** ({stamp}).{reason}"
    return ""


def _apply_banner(text: str, banner: str) -> Tuple[str, str]:
    replaced = replace_between(text, STATUS_START, STATUS_END, banner)
    if replaced is None:
        fail("status marker block missing; `move` checks for it before planning, so this is a bug")
    # Keep a blank line after the block so the heading that follows renders as
    # a heading; markdown treats a heading glued to a comment as prose.
    end = replaced.find(STATUS_END) + len(STATUS_END)
    if not replaced[end:].startswith("\n\n") and replaced[end:].strip():
        replaced = replaced[:end] + "\n" + replaced[end:]
    return replaced, ("banner set" if banner else "banner cleared")


def _update_table_status(text: str, folder: str, status: str) -> str:
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith("|") and folder in line:
            cells = line.split("|")
            if len(cells) >= 4:
                cells[2] = f" {status} "
                lines[index] = "|".join(cells)
    return "\n".join(lines)


# --------------------------------------------------------------------------
# list
# --------------------------------------------------------------------------

def cmd_list(args: argparse.Namespace) -> None:
    workspace = Workspace(resolve_repo_root(args.repo_root), args.projects_dir)
    if not workspace.projects_dir.is_dir():
        print(f"no {workspace.projects_dir_name}/ here yet. Start one with: projects.py new --name <slug> --description ... --goal ...")
        return

    states = list(STATES.keys()) if args.all else ["active"]
    on = date.today()
    rows = []
    for project in workspace.projects(states):
        if args.owner and (project.owner or "") != args.owner:
            continue
        row = {
            "folder": project.folder,
            "kind": "standing" if project.is_standing else "project",
            "state": project.state,
            "owner": project.owner or "",
            "parent": project.parent_folder or "",
            "created": project.created.isoformat() if project.created else "",
            "resume": posix(project.resume_file.relative_to(workspace.repo_root)),
        }
        if project.is_standing:
            # A standing project is measured by its cycles, not by completion:
            # idle days count from the last unit, and overdue from the cadence.
            unit, last = project.last_unit()
            cadence = project.cadence or ""
            setup = project.setup
            row.update({
                "cadence": cadence,
                "last_unit": unit or "",
                "last_unit_date": last.isoformat() if last else "",
                "overdue_days": overdue_days(cadence, last, on) if last else None,
                "setup_ticked": setup[0] if setup else None,
                "setup_total": setup[1] if setup else None,
                "done_ticked": None,
                "done_total": None,
                "progress_percent": None,
            })
        else:
            last = project.last_activity
            ticked, total = project.progress or (0, 0)
            row.update({
                "done_ticked": ticked,
                "done_total": total,
                "progress_percent": round(100 * ticked / total) if total else None,
            })
        idle = (on - last).days if last else None
        if args.stale is not None and (idle is None or idle < args.stale):
            continue
        row["last_activity"] = last.isoformat() if last else ""
        row["idle_days"] = idle
        rows.append(row)

    counts = {state: len(workspace.projects([state])) for state in STATES}

    if args.json:
        print(json.dumps({"projects": rows, "counts": counts}, indent=2))
        return

    if not rows:
        print("no projects match" if (args.stale is not None or args.owner) else "no active projects")
    else:
        # Standing projects first, most overdue first; then projects stalest
        # first. The owner's rule is to lead with what has waited longest.
        rows.sort(key=lambda r: (
            r["kind"] != "standing",
            -(r.get("overdue_days") or 0),
            -(r["idle_days"] if r["idle_days"] is not None else -1),
            r["folder"],
        ))
        by_parent: Dict[str, List[dict]] = {}
        top: List[dict] = []
        folders = {r["folder"] for r in rows}
        for row in rows:
            if row["parent"] and row["parent"] in folders and row["parent"] != row["folder"]:
                by_parent.setdefault(row["parent"], []).append(row)
            else:
                top.append(row)
        header = f"{'project':<52} {'state':<10} {'owner':<12} {'progress':<12} {'last activity':<14} idle"
        print(header)
        print("-" * len(header))
        printed: set = set()

        def print_tree(row: dict, depth: int) -> None:
            # Any depth: a sub-project of a sub-project nests one level more.
            if row["folder"] in printed:
                return
            printed.add(row["folder"])
            _print_row(row, indent="  " * depth)
            for child in by_parent.get(row["folder"], []):
                print_tree(child, depth + 1)

        for row in top:
            print_tree(row, 0)
        # A parent chain that loops back on itself has no top; print it flat
        # rather than lose it.
        for row in rows:
            print_tree(row, 0)
    summary = " · ".join(f"{STATUS_WORDS[s].lower()} {counts[s]}" for s in STATES)
    print(f"\n{summary}")


def _standing_summary(row: dict) -> str:
    """`standing · daily · last unit 2026-10-30 · overdue 2 d · setup 3/7`."""
    parts = ["standing", row["cadence"] or "no cadence"]
    if row["last_unit"]:
        parts.append(f"last unit {row['last_unit_date']}")
    else:
        parts.append(f"no unit yet (activity {row['last_unit_date'] or '-'})")
    overdue = row["overdue_days"]
    if overdue is not None:
        parts.append("on time" if overdue == 0 else f"overdue {overdue} d")
    if row["setup_total"]:
        parts.append(f"setup {row['setup_ticked']}/{row['setup_total']}")
    return " · ".join(parts)


def _print_row(row: dict, indent: str) -> None:
    name = f"{indent}{row['folder']}"
    if row["kind"] == "standing":
        print(f"{name:<52} {row['state']:<10} {row['owner'] or '-':<12} {_standing_summary(row)}")
        return
    idle = f"{row['idle_days']}d" if row["idle_days"] is not None else "-"
    progress = f"{row['done_ticked']}/{row['done_total']} {row['progress_percent']}%" if row["done_total"] else "-"
    print(f"{name:<52} {row['state']:<10} {row['owner'] or '-':<12} {progress:<12} {row['last_activity'] or '-':<14} {idle}")


# --------------------------------------------------------------------------
# refresh
# --------------------------------------------------------------------------

def cmd_refresh(args: argparse.Namespace) -> None:
    workspace = Workspace(resolve_repo_root(args.repo_root), args.projects_dir)
    if args.all:
        targets = workspace.projects(["active"])
    else:
        if not args.folder:
            fail("give a project folder, or --all for every active project")
        found = workspace.find(args.folder)
        if found is None:
            fail(f"project not found in any state: {args.folder}")
        targets = [found]

    changed = unchanged = 0
    for project in targets:
        text = read_text(project.resume_file)
        if text is None:
            fail(f"{project.folder} has no {RESUME_FILE}; this folder was not created by the projects skill")
        updated = replace_between(text, ROE_START, ROE_END, render_rules_of_engagement(project.is_sub_project, project.is_standing))
        if updated is None:
            fail(f"{project.folder}/{RESUME_FILE} has no rules-of-engagement marker block; this folder was not created by the projects skill")
        if updated == text:
            unchanged += 1
            continue
        project.resume_file.write_text(updated, encoding="utf-8")
        changed += 1
        print(f"  {project.folder}: rules of engagement refreshed")
    print(f"refreshed {changed}, already current {unchanged}")


# --------------------------------------------------------------------------
# selftest: the lifecycle end to end in a throwaway tree
# --------------------------------------------------------------------------

class _Capture:
    """A minimal stdout stand-in so selftest can read `list --json` output."""

    def __init__(self) -> None:
        self.text = ""

    def write(self, chunk: str) -> int:
        self.text += chunk
        return len(chunk)

    def flush(self) -> None:
        pass


def cmd_selftest(_args: argparse.Namespace) -> None:
    """Run the CLI through create, sub-project, every lifecycle transition,
    boundary-safe matching, refresh, progress, list, and the refusal to touch
    folders it did not create. This is the CI smoke test and a quick confidence
    check for anyone changing this file."""
    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            fail(f"selftest failed at check {checks}: {message}")

    def run(*argv: str) -> None:
        main(list(argv) + ["--repo-root", str(root)])

    def only(prefix: str, state: str = "active") -> Project:
        matches = [p for p in ws.projects([state]) if p.slug == prefix]
        check(len(matches) == 1, f"expected exactly one {state} project with slug {prefix}, found {len(matches)}")
        return matches[0]

    def links_resolve(project: Project) -> bool:
        for path in project.path.rglob("*.md"):
            for match in MARKDOWN_LINK.finditer(read_text(path) or ""):
                target = match.group("target").split("#", 1)[0]
                if target and "://" not in target and not (path.parent / target).exists():
                    return False
        return True

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ws = Workspace(root, DEFAULT_PROJECTS_DIR)

        run("new", "--name", "foo", "--description", "First project.", "--goal", "Prove the CLI.", "--owner", "parker")
        run("new", "--name", "foo-bar", "--description", "Shares a prefix with foo.", "--goal", "Catch prefix bugs.")
        foo, foo_bar = only("foo"), only("foo-bar")
        check(foo.parts.group("seq") == "01" and foo_bar.parts.group("seq") == "02", "sequence numbers increment")
        check((ws.projects_dir / "README.md").is_file(), "projects README bootstrapped")
        check((ws.projects_dir / OWNERS_DIR / "parker.md").is_file(), "owner file created from starter")
        check(foo.owner == "parker", "owner line read back")

        run("new", "--name", "child", "--description", "A sub-project.", "--goal", "Inherit from foo.", "--parent", foo.folder)
        child = only("child")
        check(child.is_sub_project and child.parent_folder == foo.folder, "sub-project links to parent")
        check(f"[{child.folder}]" in (read_text(foo.readme) or ""), "parent table has the sub-project row")
        check(f"{child.rel}/next.md" in (read_text(foo.resume_file) or ""), "parent resume lists the sub-project")
        check(links_resolve(child), "sub-project links resolve")

        # A note that references both projects: only foo's references may change when foo moves.
        note = child.path / "plans" / "002-note.md"
        note.write_text(
            f"See `{foo.rel}/README.md` and `{foo_bar.rel}/README.md`.\n"
            f"Links: [foo](../../{foo.folder}/README.md) and [foo-bar](../../{foo_bar.folder}/README.md).\n",
            encoding="utf-8",
        )
        check(links_resolve(child), "fixture note links resolve before any move")
        snapshot = {p: read_text(p) for p in ws.projects_dir.rglob("*") if p.is_file()}

        run("move", child.folder, "--to", "on-hold", "--reason", "Testing.", "--resume-when", "Never.", "--dry-run")
        check({p: read_text(p) for p in ws.projects_dir.rglob("*") if p.is_file()} == snapshot, "dry run changes nothing")

        # Moving foo must be refused while child is active, then succeed with the child parked.
        try:
            run("move", foo.folder, "--to", "on-hold", "--reason", "Blocked.", "--resume-when", "Unblocked.")
            check(False, "move should refuse while sub-projects are active")
        except SystemExit as exc:
            check(exc.code == 1, "refusal exits non-zero")
        run("move", child.folder, "--to", "on-hold", "--reason", "Parking.", "--resume-when", "Parent resumes.")
        run("move", foo.folder, "--to", "on-hold", "--reason", "Blocked.", "--resume-when", "Unblocked.")
        foo_held, child_held = only("foo", "on-hold"), only("child", "on-hold")
        note_text = read_text(child_held.path / "plans" / "002-note.md") or ""
        check(f"`{foo_held.rel}/README.md`" in note_text, "foo's repo-relative reference re-pointed")
        check(f"`{foo_bar.rel}/README.md`" in note_text, "foo-bar's reference untouched (boundary-safe)")
        check(links_resolve(child_held) and links_resolve(foo_held), "links resolve after both moves")
        check("Status: On hold" in (read_text(foo_held.readme) or ""), "banner written to brief")
        check("Resume when:" in (read_text(foo_held.resume_file) or ""), "banner written to resume file")
        check("| On hold |" in (read_text(foo_held.readme) or ""), "parent table row shows the child's state")

        run("move", foo.folder, "--to", "completed")
        run("move", child.folder, "--to", "completed")
        foo_done, child_done = only("foo", "completed"), only("child", "completed")
        check(links_resolve(child_done) and links_resolve(foo_done), "on-hold -> completed directly keeps links whole")
        check("Status: Completed" in (read_text(foo_done.readme) or ""), "completed banner replaces the on-hold banner")

        run("move", child.folder, "--to", "active")
        run("move", foo.folder, "--to", "active")
        restored = {p: read_text(p) for p in ws.projects_dir.rglob("*") if p.is_file()}
        differences = {p for p in snapshot if snapshot[p] != restored.get(p)}
        check(not differences, f"round trip restores every byte; differs: {sorted(str(p) for p in differences)[:3]}")

        # refresh: a hand-edited rules block goes back to the template.
        resume = only("foo").resume_file
        resume.write_text((read_text(resume) or "").replace("### Step 5: Wait", "### Step 5: Edited"), encoding="utf-8")
        run("refresh", "--all")
        check("### Step 5: Wait" in (read_text(resume) or ""), "refresh restores the rules of engagement")

        # Progress is the count of ticked done-when boxes in the brief, nothing else.
        run("new", "--name", "tracked", "--description", "Has a done-when list.", "--goal", "Prove progress.", "--done", "a,b,c,d,e")
        tracked = only("tracked")
        check(tracked.progress == (0, 5), "--done writes five unticked boxes")
        brief = read_text(tracked.readme) or ""
        tracked.readme.write_text(brief.replace("- [ ] a", "- [x] a").replace("- [ ] b", "- [X] b"), encoding="utf-8")
        check(tracked.progress == (2, 5), "two ticked boxes count as 2 of 5")
        (tracked.path / "changelogs" / "001-first.md").write_text('---\ndate: "2026-01-02"\nsession: 1\n---\n', encoding="utf-8")
        check(tracked.last_activity == date(2026, 1, 2), "last activity read from changelog frontmatter")
        stdout, sys.stdout = sys.stdout, _Capture()
        try:
            run("list", "--all", "--json")
            listing = json.loads(sys.stdout.text)
        finally:
            sys.stdout = stdout
        row = next(r for r in listing["projects"] if r["folder"] == tracked.folder)
        check(row["done_ticked"] == 2 and row["done_total"] == 5 and row["progress_percent"] == 40, "list reports 2/5 as 40%")
        run("list", "--stale", "0")

        # Standing projects: a duty kept true, never completed.
        def capture(*argv: str) -> str:
            stdout, sys.stdout = sys.stdout, _Capture()
            try:
                run(*argv)
                text = sys.stdout.text
            finally:
                sys.stdout = stdout
            return text

        def refused(*argv: str) -> bool:
            try:
                run(*argv)
            except SystemExit as exc:
                return exc.code == 1
            return False

        run("new", "--standing", "show", "--cadence", "daily", "--description", "A daily show.",
            "--duty", "An episode is out every day.", "--setup", "rig,prompter,channel")
        show = ws.find("standing/show")
        check(show is not None and show.path == ws.projects_dir / STANDING_DIR / "show", "standing project created at standing/<slug>/")
        check(show.is_standing and show.folder == "standing/show" and show.slug == "show", "standing identity: folder standing/show")
        check(ws.find("show") is not None and ws.find("show").path == show.path, "a standing project is found by its bare slug too")
        check((show.path / "units").is_dir() and (show.path / "playbooks").is_dir(), "units/ and playbooks/ created")
        brief = read_text(show.readme) or ""
        check("- **Kind:** standing" in brief and "## Duty" in brief and "## Done when" not in brief, "standing brief: kind and duty, no done-when")
        check(show.cadence == "daily" and show.progress is None and show.setup == (0, 3), "cadence read, progress None, setup 0/3")
        check(show.created == date.today(), "created read from the brief's Created line")
        check("### Step 3: Present the duty as the owner" in (read_text(show.resume_file) or ""), "standing next.md carries the standing rules")
        check(refused("new", "--standing", "nocadence", "--description", "x", "--duty", "y"), "--standing without --cadence is refused")
        check(refused("new", "--standing", "show", "--cadence", "daily", "--description", "x", "--duty", "y"), "a second standing project with the same slug is refused")
        check(refused("new", "--name", "mixed", "--description", "x", "--goal", "y", "--cadence", "daily"), "--cadence on a project is refused")

        # Cadence math: expected cycle days strictly between the last unit and today.
        mon, tue, thu = date(2026, 10, 26), date(2026, 10, 27), date(2026, 10, 29)
        check(overdue_days("daily", mon, thu) == 2 and overdue_days("daily", date(2026, 10, 28), thu) == 0, "daily: yesterday is on time, Mon to Thu is 2 overdue")
        check(overdue_days("daily", thu, thu) == 0, "daily: a unit today is on time")
        check(overdue_days("mon-sat", date(2026, 10, 24), tue) == 1, "mon-sat: Sunday is not a cycle day")
        check(overdue_days("weekdays", date(2026, 10, 23), tue) == 1, "weekdays: the weekend is not a cycle day")
        check(overdue_days("weekly", date(2026, 10, 20), tue) == 0 and overdue_days("weekly", date(2026, 10, 20), thu) == 2, "weekly: due seven days after the last unit")

        # Units: the newest unit is the last kept cycle.
        three_ago = date.fromordinal(date.today().toordinal() - 3)
        ten_ago = date.fromordinal(date.today().toordinal() - 10)
        for day in (ten_ago, three_ago):
            unit = show.path / "units" / day.strftime("%Y-%m") / day.isoformat()
            unit.mkdir(parents=True)
            (unit / "log.md").write_text(f"# {day.isoformat()}\n", encoding="utf-8")
        check(show.last_unit() == (three_ago.isoformat(), three_ago), "last unit is the newest unit folder")
        listing = json.loads(capture("list", "--json"))
        row = next(r for r in listing["projects"] if r["folder"] == "standing/show")
        check(row["kind"] == "standing" and row["cadence"] == "daily" and row["overdue_days"] == 2 and row["progress_percent"] is None,
              "list --json: standing, daily, overdue 2, no progress")
        check(row["setup_ticked"] == 0 and row["setup_total"] == 3 and row["idle_days"] == 3, "list --json: setup 0/3, idle from the last unit")

        # A standing project never completes.
        check(refused("move", "standing/show", "--to", "completed"), "move --to completed is refused for a standing project")
        check(ws.find("standing/show").state == "active", "the refused move changed nothing")

        # Sub-projects of a standing project stay dated folders at the top level, and nest at any depth.
        run("new", "--name", "edit-tools", "--description", "Tools for the edit.", "--goal", "Faster edits.", "--parent", "standing/show")
        sub_project = only("edit-tools")
        check(sub_project.parent_folder == "standing/show", "sub-project names standing/show as its parent")
        check("[standing/show](../standing/show/)" in (read_text(sub_project.readme) or ""), "the Parent line links to the standing project")
        check(f"[{sub_project.folder}](../../{sub_project.folder}/)" in (read_text(show.readme) or ""), "the standing project's table links down to the sub-project")
        run("new", "--name", "clip-cutter", "--description", "One tool.", "--goal", "Cut clips.", "--parent", sub_project.folder)
        sub_sub = only("clip-cutter")
        check(sub_sub.parent_folder == sub_project.folder, "a sub-project of a sub-project links to its parent")
        check(links_resolve(show) and links_resolve(sub_project) and links_resolve(sub_sub), "standing and sub-project links resolve")
        lines = capture("list").splitlines()
        show_line = next((i for i, line in enumerate(lines) if line.startswith("standing/show ")), -1)
        check(show_line != -1 and "standing · daily · last unit" in lines[show_line] and "overdue 2 d · setup 0/3" in lines[show_line],
              "list prints the standing line with cadence, last unit, overdue and setup")
        check(show_line == 2, "standing projects are listed first")
        check(lines[show_line + 1].startswith(f"  {sub_project.folder} "), "the sub-project nests under the standing project")
        check(lines[show_line + 2].startswith(f"    {sub_sub.folder} "), "a sub-project of a sub-project nests one level more")
        check(any(line.startswith(f"  {child.folder} ") for line in lines), "an ordinary sub-project still nests under its parent")

        # Shelving a standing project moves it to .shelved/standing/<slug>/ and repairs every link.
        before_shelve = {p: read_text(p) for p in ws.projects_dir.rglob("*") if p.is_file()}
        check(refused("move", "standing/show", "--to", "shelved", "--reason", "Pause."), "shelving is refused while sub-projects are active")
        run("move", sub_sub.folder, "--to", "on-hold", "--reason", "Parent paused.", "--resume-when", "Show resumes.")
        run("move", sub_project.folder, "--to", "on-hold", "--reason", "Parent paused.", "--resume-when", "Show resumes.")
        run("move", "standing/show", "--to", "shelved", "--reason", "Testing a pause.")
        shelved = ws.find("standing/show")
        check(shelved.state == "shelved" and shelved.path == ws.state_dir("shelved") / STANDING_DIR / "show", "shelved to .shelved/standing/show/")
        check(not (ws.projects_dir / STANDING_DIR).exists(), "the emptied standing/ folder is removed")
        check("Status: Shelved" in (read_text(shelved.readme) or ""), "shelved banner written")
        held_sub = ws.find(sub_project.folder)
        check(links_resolve(shelved) and links_resolve(held_sub) and links_resolve(ws.find(sub_sub.folder)), "links resolve after shelving")
        check(f"`{shelved.rel}/README.md`" in (read_text(held_sub.resume_file) or ""), "the sub-project's parent paths point at the shelved folder")
        listing = json.loads(capture("list", "--all", "--json"))
        check(any(r["folder"] == "standing/show" and r["state"] == "shelved" for r in listing["projects"]), "list --all shows the shelved standing project")
        run("move", "standing/show", "--to", "active")
        run("move", sub_project.folder, "--to", "active")
        run("move", sub_sub.folder, "--to", "active")
        after_restore = {p: read_text(p) for p in ws.projects_dir.rglob("*") if p.is_file()}
        differences = {p for p in before_shelve if before_shelve[p] != after_restore.get(p)}
        check(not differences, f"standing round trip restores every byte; differs: {sorted(str(p) for p in differences)[:3]}")

        # refresh writes the standing rules into standing projects and the normal rules into the rest.
        show = ws.find("standing/show")
        show.resume_file.write_text((read_text(show.resume_file) or "").replace("### Step 3: Present the duty as the owner", "### Step 3: Edited"), encoding="utf-8")
        run("refresh", "--all")
        standing_next, normal_next = read_text(show.resume_file) or "", read_text(only("foo").resume_file) or ""
        check("### Step 3: Present the duty as the owner" in standing_next and "Present status as the owner" not in standing_next, "refresh restores the standing rules")
        check("Present status as the owner" in normal_next and "Present the duty" not in normal_next, "refresh keeps the normal rules in a normal project")

        # A folder without the marker blocks is not ours: the CLI stops instead of guessing.
        stranger = ws.projects_dir / "20250101.01.stranger"
        stranger.mkdir()
        (stranger / "README.md").write_text("# stranger\n", encoding="utf-8")
        (stranger / RESUME_FILE).write_text("# Next: stranger\n\nno markers here\n", encoding="utf-8")
        for argv in (("refresh", "20250101.01.stranger"), ("move", "20250101.01.stranger", "--to", "shelved", "--reason", "x")):
            try:
                run(*argv)
                check(False, f"{argv[0]} should stop on a folder without marker blocks")
            except SystemExit as exc:
                check(exc.code == 1, f"{argv[0]} stops with a clear error on a marker-less folder")
        check((stranger / RESUME_FILE).read_text(encoding="utf-8").endswith("no markers here\n"), "marker-less files are never touched")

    print(f"selftest ok: {checks} checks passed")


# --------------------------------------------------------------------------
# argument parsing
# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="projects.py",
        description="Create, move, list and refresh projects managed by the `projects` agent skill.",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo-root", help="repository that holds the projects folder (default: git rev-parse --show-toplevel)")
    common.add_argument("--projects-dir", default=DEFAULT_PROJECTS_DIR, help=f"projects folder name (default: {DEFAULT_PROJECTS_DIR})")

    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", parents=[common], help="create a project, a sub-project (--parent), or a standing project (--standing)")
    new.add_argument("--name", help="kebab-case slug; the date and sequence prefix are added")
    new.add_argument("--standing", metavar="SLUG", help="create a standing project at standing/<slug>/: a duty that never completes")
    new.add_argument("--description", required=True, help="one or two sentences")
    new.add_argument("--goal", help="what done looks like at the highest level (required for a project)")
    new.add_argument("--done", help="comma-separated definition-of-done items")
    new.add_argument("--cadence", choices=list(CADENCES), help="standing only: how often a cycle is due")
    new.add_argument("--duty", help="standing only: the condition kept true, in one or two sentences")
    new.add_argument("--loop", help="standing only: what one cycle is")
    new.add_argument("--setup", help="standing only: comma-separated one-time setup items")
    new.add_argument("--scope", help="what is in and out, free text or bullets")
    new.add_argument("--repos", help="comma-separated workspace folder names of the repositories touched (default: this repository)")
    new.add_argument("--owner", help="named owner; creates owners/<name>.md from the starter if missing")
    new.add_argument("--parent", help="parent project folder (or standing/<slug>); makes this a sub-project")
    new.set_defaults(func=cmd_new)

    move = sub.add_parser("move", parents=[common], help="move a project between lifecycle states and repair every reference (a standing project never completes)")
    move.add_argument("folder", help="project folder name, or standing/<slug> (not a path)")
    move.add_argument("--to", required=True, choices=list(STATES.keys()))
    move.add_argument("--reason", help="why (required for on-hold and shelved)")
    move.add_argument("--resume-when", help="what has to happen before it resumes (required for on-hold)")
    move.add_argument("--force", action="store_true", help="proceed even if active sub-projects exist")
    move.add_argument("--dry-run", action="store_true", help="show every change without writing")
    move.set_defaults(func=cmd_move)

    listing = sub.add_parser("list", parents=[common], help="the portfolio: active projects, stalest first")
    listing.add_argument("--all", action="store_true", help="include completed, on-hold and shelved")
    listing.add_argument("--stale", type=int, metavar="DAYS", help="only projects idle for at least DAYS")
    listing.add_argument("--owner", help="only projects with this owner")
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(func=cmd_list)

    refresh = sub.add_parser("refresh", parents=[common], help="re-sync the rules of engagement block from the skill's template")
    refresh.add_argument("folder", nargs="?", help="project folder name, or standing/<slug>")
    refresh.add_argument("--all", action="store_true", help="every active project")
    refresh.set_defaults(func=cmd_refresh)

    selftest = sub.add_parser("selftest", parents=[common], help="run the lifecycle end to end in a temporary tree")
    selftest.set_defaults(func=cmd_selftest)
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    for name in ("folder", "parent"):
        value = getattr(args, name, None)
        if value and not _is_folder_name(value):
            fail(f"give the bare folder name (or standing/<slug>), not a path: '{value}'")
    args.func(args)


def _is_folder_name(value: str) -> bool:
    """A project folder name as the CLI accepts it: `YYYYMMDD.NN[.sp].slug`,
    `standing/<slug>`, or a standing project's bare slug. Never a path."""
    if value.startswith(f"{STANDING_DIR}/"):
        return bool(STANDING_SLUG.match(value[len(STANDING_DIR) + 1:]))
    return "/" not in value and not value.startswith(".")


if __name__ == "__main__":
    main()
