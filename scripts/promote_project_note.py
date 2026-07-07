#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dojo_app.lab_output import print_color


REQUIRED_HEADINGS = (
    "# Vibe Coding Dojo",
    "## Summary",
    "## Current Files",
    "## Boundaries",
    "## Verification",
)
REQUIRED_FACTS = (
    "dojo_app/maze_game.py",
    "dojo_app/maze_play.py",
)
VERIFICATION_COMMANDS = (
    "python3 scripts/check_repo.py",
    "python3 scripts/verify_maze_movement.py",
    "python3 -m dojo_app.maze_game",
)


def clean_note(text: str) -> str:
    return text.strip() + "\n"


def normalize_frontmatter(text: str) -> str:
    lines = text.strip().splitlines()
    body = lines

    if lines and lines[0] == "---":
        try:
            closing = lines.index("---", 1)
        except ValueError:
            closing = -1
        if closing > 0:
            body = lines[closing + 1 :]

    body_text = "\n".join(body).strip()
    return f"---\ntype: project\nstatus: active\n---\n\n{body_text}\n"


def note_problems(text: str) -> list[str]:
    lines = text.splitlines()
    problems = []

    if lines[:4] != ["---", "type: project", "status: active", "---"]:
        problems.append("project frontmatter")

    for heading in REQUIRED_HEADINGS:
        if heading not in lines:
            problems.append(heading)

    for fact in REQUIRED_FACTS:
        if fact not in text:
            problems.append(fact)

    if not any(command in text for command in VERIFICATION_COMMANDS):
        problems.append("a repo verification command")

    if "```" in text:
        problems.append("code fences")
    return problems


def select_note(draft: str, fallback: str) -> tuple[str, str]:
    normalized_draft = normalize_frontmatter(draft)
    if not note_problems(normalized_draft):
        return clean_note(normalized_draft), "codex-draft"

    normalized_fallback = normalize_frontmatter(fallback)
    fallback_problems = note_problems(normalized_fallback)
    if fallback_problems:
        missing = ", ".join(fallback_problems)
        raise ValueError(f"checked project note is invalid: {missing}")
    return clean_note(normalized_fallback), "checked-repo-note"


def checked_repo_note(target: Path) -> str:
    repo_root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    relative = target.resolve().relative_to(Path(repo_root).resolve())
    return subprocess.run(
        ["git", "show", f"HEAD:{relative.as_posix()}"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and save a Codex project-note draft.")
    parser.add_argument("draft", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()

    try:
        draft = args.draft.read_text(encoding="utf-8")
        fallback = checked_repo_note(args.target)
        note, source = select_note(draft, fallback)
        args.target.write_text(note, encoding="utf-8")
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        print_color(f"PROJECT_NOTE=failed: {exc}", "red")
        return 1

    if source == "codex-draft":
        print_color("PROJECT_NOTE=refreshed", "green")
    else:
        print_color("PROJECT_NOTE=restored-known-good", "yellow")
        print_color("Codex missed the shared schema, so the checked project note was restored.", "yellow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
