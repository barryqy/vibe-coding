from __future__ import annotations

import argparse
from pathlib import Path


MAZE_SIZE = 12
ALLOWED_CELLS = {"#", ".", "S", "E"}
DEFAULT_MAZE = [
    "############",
    "#S.........#",
    "##########.#",
    "#..........#",
    "#.##########",
    "#..........#",
    "##########.#",
    "#..........#",
    "#.##########",
    "#..........#",
    "##########E#",
    "############",
]


def valid_maze_lines(lines: list[str]) -> bool:
    if len(lines) != MAZE_SIZE:
        return False
    if any(len(line) != MAZE_SIZE for line in lines):
        return False
    if any(set(line) - ALLOWED_CELLS for line in lines):
        return False
    joined = "".join(lines)
    return joined.count("S") == 1 and joined.count("E") == 1


def extract_maze_lines(text: str) -> list[str]:
    rows = []
    for raw in text.splitlines():
        line = raw.strip()
        if len(line) == MAZE_SIZE and not (set(line) - ALLOWED_CELLS):
            rows.append(line)
        if len(rows) == MAZE_SIZE:
            break
    if not valid_maze_lines(rows):
        raise ValueError("expected a 12x12 maze with one S and one E")
    return rows


def load_maze(path: str | None = None) -> list[str]:
    if not path:
        return list(DEFAULT_MAZE)
    return extract_maze_lines(Path(path).read_text(encoding="utf-8"))


def find_cell(maze: list[str], marker: str) -> tuple[int, int]:
    for y, row in enumerate(maze):
        x = row.find(marker)
        if x >= 0:
            return x, y
    raise ValueError(f"missing {marker}")


def render_maze(maze: list[str]) -> str:
    return "\n".join(maze)


def run_static_maze(maze: list[str]) -> None:
    start = find_cell(maze, "S")
    exit_cell = find_cell(maze, "E")

    print("MAZE=ready")
    print("mode=static")
    print("size=12x12")
    print(f"start={start[0]},{start[1]}")
    print(f"exit={exit_cell[0]},{exit_cell[1]}")
    print(render_maze(maze))
    print("MAZE=pass")
    print("NEXT: python3 scripts/check_repo.py")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print a tiny terminal maze.")
    parser.add_argument("--maze-file", help="Optional file containing a 12x12 maze")
    args = parser.parse_args(argv)

    run_static_maze(load_maze(args.maze_file))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
