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

    checks = [
        (choose_next_position(maze, (1, 1), "d"), (1, 2)),
        (choose_next_position(maze, (1, 1), "s"), (2, 1)),
        (choose_next_position(maze, (1, 1), "w"), (1, 1)),
        (choose_next_position(maze, (1, 1), "x"), (1, 1)),
    ]
    return 0 if all(actual == expected for actual, expected in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
