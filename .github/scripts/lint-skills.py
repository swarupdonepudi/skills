#!/usr/bin/env python3
"""
Lint every skill under skills/ against the Agent Skills specification
(https://agentskills.io/specification) and this repository's own bar.

Standard library only, so CI needs nothing but Python. The checks:

  frontmatter   SKILL.md opens with YAML frontmatter that has `name` and
                `description`; `name` is 1-64 chars of [a-z0-9-], no leading,
                trailing or doubled hyphen, and equals the parent directory
                name; `description` is 1-1024 chars; `metadata`, when present,
                maps strings to strings; `compatibility` is <= 500 chars.
  size          the SKILL.md body stays under MAX_SKILL_LINES. The spec says
                500; this repository holds itself to 300 so the always-loaded
                instructions stay small and the detail lives in references/.
  links         every relative markdown link in SKILL.md and references/*.md
                points at a file that exists, so progressive disclosure never
                dead-ends.
  scripts       every *.py under scripts/ byte-compiles.

Exit code is non-zero when anything fails; each failure is printed on its own
line as `<skill>: <check>: <detail>`.
"""

from __future__ import annotations

import py_compile
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
MAX_SKILL_LINES = 300

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MARKDOWN_LINK = re.compile(r"\]\((?P<target>[^)\s]+)\)")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter, body). A deliberately small YAML reader: the spec
    only needs flat `key: value` pairs plus one nested `metadata:` map, and a
    dependency-free linter is worth more than full YAML here."""
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with a '---' frontmatter block")
    end = text.find("\n---", 4)
    if end == -1:
        raise ValueError("frontmatter block is not closed with '---'")
    block = text[4:end]
    body = text[end + 4:]

    data: dict = {}
    current_map: str | None = None
    for raw in block.splitlines():
        if not raw.strip():
            continue
        if raw.startswith("  ") and current_map:
            key, _, value = raw.strip().partition(":")
            data[current_map][key.strip()] = _unquote(value.strip())
            continue
        current_map = None
        key, _, value = raw.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            data[key] = {}
            current_map = key
        else:
            data[key] = _unquote(value)
    return data, body


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def check_skill(skill_dir: Path) -> list[str]:
    failures: list[str] = []
    name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{name}: frontmatter: SKILL.md is missing"]

    text = skill_md.read_text(encoding="utf-8")
    try:
        meta, body = parse_frontmatter(text)
    except ValueError as exc:
        return [f"{name}: frontmatter: {exc}"]

    declared = meta.get("name")
    if not isinstance(declared, str) or not declared:
        failures.append(f"{name}: frontmatter: `name` is required")
    else:
        if not (1 <= len(declared) <= 64) or not NAME_PATTERN.match(declared):
            failures.append(f"{name}: frontmatter: `name` '{declared}' must be 1-64 chars of [a-z0-9-] with no leading, trailing or doubled hyphen")
        if declared != name:
            failures.append(f"{name}: frontmatter: `name` '{declared}' must equal the directory name")

    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        failures.append(f"{name}: frontmatter: `description` is required")
    elif len(description) > 1024:
        failures.append(f"{name}: frontmatter: `description` is {len(description)} chars; the limit is 1024")

    compatibility = meta.get("compatibility")
    if isinstance(compatibility, str) and len(compatibility) > 500:
        failures.append(f"{name}: frontmatter: `compatibility` is {len(compatibility)} chars; the limit is 500")

    metadata = meta.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            failures.append(f"{name}: frontmatter: `metadata` must be a map")
        else:
            for key, value in metadata.items():
                if not isinstance(value, str):
                    failures.append(f"{name}: frontmatter: `metadata.{key}` must be a string")

    body_lines = len(body.strip("\n").splitlines())
    if body_lines > MAX_SKILL_LINES:
        failures.append(f"{name}: size: SKILL.md body is {body_lines} lines; the limit is {MAX_SKILL_LINES}")

    for doc in [skill_md, *sorted((skill_dir / "references").glob("*.md"))]:
        for match in MARKDOWN_LINK.finditer(doc.read_text(encoding="utf-8")):
            target = match.group("target")
            if "://" in target or target.startswith("#") or target.startswith("mailto:"):
                continue
            if "<" in target or ">" in target:
                continue  # a placeholder shown in prose, like `[<folder>](../<folder>/)`, not a link
            path_part = target.split("#", 1)[0]
            if not (doc.parent / path_part).exists():
                failures.append(f"{name}: links: {doc.relative_to(skill_dir)} -> '{target}' does not resolve")

    for script in sorted((skill_dir / "scripts").glob("*.py")):
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            failures.append(f"{name}: scripts: {script.name} does not compile: {exc.msg}")

    return failures


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"no skills/ directory at {SKILLS_DIR}", file=sys.stderr)
        return 1
    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    failures: list[str] = []
    for skill_dir in skill_dirs:
        failures.extend(check_skill(skill_dir))
    for line in failures:
        print(line)
    if failures:
        print(f"\n{len(failures)} problem(s) across {len(skill_dirs)} skill(s)")
        return 1
    print(f"ok: {len(skill_dirs)} skill(s) pass frontmatter, size, link and script checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
