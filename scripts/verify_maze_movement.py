#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dojo_app.maze_play import choose_next_position


def main() -> int:
    maze = [
        "#####",
        "#...#",
        "#.#.#",
        "#...#",
        "#####",
    ]
    open_edge = [
        "...",
        "...",
        "...",
    ]

    checks = [
        ("move-right", maze, (1, 1), "d", (1, 2)),
        ("move-down", maze, (1, 1), "s", (2, 1)),
        ("move-left", maze, (1, 2), "a", (1, 1)),
        ("move-up", maze, (2, 1), "w", (1, 1)),
        ("wall-block", maze, (1, 1), "w", (1, 1)),
        ("invalid-key", maze, (1, 1), "x", (1, 1)),
        ("top-boundary", open_edge, (0, 1), "w", (0, 1)),
        ("left-boundary", open_edge, (1, 0), "a", (1, 0)),
        ("bottom-boundary", open_edge, (2, 1), "s", (2, 1)),
        ("right-boundary", open_edge, (1, 2), "d", (1, 2)),
        ("ragged-row-boundary", ["...", ".", "..."], (0, 1), "s", (0, 1)),
    ]
    failures = []
    for name, case_maze, position, command, expected in checks:
        try:
            actual = choose_next_position(case_maze, position, command)
        except Exception as exc:
            actual = f"raised {type(exc).__name__}: {exc}"
        if actual != expected:
            failures.append((name, position, command, expected, actual))

    if not failures:
        print("MAZE_MOVEMENT_CHECK=pass")
        return 0

    print("MAZE_MOVEMENT_CHECK=fail")
    for name, position, command, expected, actual in failures:
        print(
            f"case={name} start={position} command={command!r} "
            f"expected={expected} actual={actual!r}"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
