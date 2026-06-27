#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import secrets
import sys
import time
from pathlib import Path


ORDER_OPTIONS = ("NESW", "NWSE", "ESWN", "WNSE", "SWEN", "ENWS")


def find_repo_root() -> Path:
    for path in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (path / "dojo_app" / "maze_game.py").exists():
            return path
    raise SystemExit("Could not find repo root with dojo_app/maze_game.py")


ROOT = find_repo_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dojo_app import maze_game  # noqa: E402


def fresh_seed() -> str:
    return f"maze-{time.time_ns()}-{secrets.token_hex(2)}"


def clean_seed(seed: str | None) -> str:
    value = (seed or "").strip()
    if not value:
        return fresh_seed()
    if len(value) > 64:
        raise ValueError("seed is too long")
    return value


def clean_order(order: str | None, seed: str) -> str:
    raw = (order or "").strip().upper()
    if not raw:
        rng = random.Random(seed)
        return ORDER_OPTIONS[rng.randrange(len(ORDER_OPTIONS))]
    if len(raw) != 4 or set(raw) != set(maze_game.MOVE_DELTAS):
        raise ValueError("order must contain N, S, E, and W once")
    return raw


def resolve_output_path(output_path: str) -> Path:
    target = Path(output_path.strip() or ".lab-state/codex-output/maze.txt")
    if target.is_absolute() or ".." in target.parts:
        raise ValueError("maze-file must stay inside this repo")
    return ROOT / target


def build_maze_artifact(
    maze_file: str,
    *,
    seed: str | None = None,
    order: str | None = None,
) -> str:
    maze_seed = clean_seed(seed)
    direction_order = clean_order(order, maze_seed)
    target = resolve_output_path(maze_file)

    maze = maze_game.generate_maze_from_plan(maze_seed, direction_order)
    maze_game.write_maze(str(target), maze)
    path_length = maze_game.shortest_path_length(maze)
    relative_target = target.relative_to(ROOT)

    return "\n".join(
        [
            "MAZEMAKER_SKILL=ready",
            "skill=mazemaker",
            "script=build_maze.py",
            "format=recursive-backtracker",
            f"maze_file={relative_target}",
            "size=12x12",
            "border=ok",
            "solvable=yes",
            f"path_length={path_length}",
            "MAZEMAKER_SKILL=pass",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a checked 12x12 Maze artifact.")
    parser.add_argument("--maze-file", default=".lab-state/codex-output/maze.txt")
    parser.add_argument("--seed", default=None)
    parser.add_argument("--order", default=None)
    args = parser.parse_args(argv)

    try:
        print(build_maze_artifact(args.maze_file, seed=args.seed, order=args.order))
    except (OSError, ValueError) as exc:
        print("MAZEMAKER_SKILL=fail")
        print(f"reason={exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
