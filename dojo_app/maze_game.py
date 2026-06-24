from __future__ import annotations

import argparse
from pathlib import Path


MAZE_SIZE = 12
ALLOWED_CELLS = {"#", ".", "S", "E"}
TILE_CELLS = {
    "#": "██",
    ".": "  ",
    "S": "S ",
    "E": "E ",
}
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
    possible_rows = []
    for raw in text.splitlines():
        line = raw.strip()
        if len(line) == MAZE_SIZE and not (set(line) - ALLOWED_CELLS):
            possible_rows.append(line)

    for index in range(0, len(possible_rows) - MAZE_SIZE + 1):
        rows = possible_rows[index : index + MAZE_SIZE]
        if valid_maze_lines(rows):
            return rows

    raise ValueError("expected a 12x12 maze with one S and one E")


def load_maze(path: str | None = None) -> list[str]:
    if not path:
        return list(DEFAULT_MAZE)
    return extract_maze_lines(Path(path).read_text(encoding="utf-8"))


def load_lab_maze(path: str | None = None) -> tuple[list[str], str]:
    if not path:
        return list(DEFAULT_MAZE), "default"

    try:
        return load_maze(path), "generated"
    except ValueError:
        return list(DEFAULT_MAZE), "default-fallback"


def find_cell(maze: list[str], marker: str) -> tuple[int, int]:
    for y, row in enumerate(maze):
        x = row.find(marker)
        if x >= 0:
            return x, y
    raise ValueError(f"missing {marker}")


def render_raw(maze: list[str]) -> str:
    return "\n".join(maze)


def render_tiles(maze: list[str]) -> str:
    lines = []
    for row in maze:
        lines.append("".join(TILE_CELLS[cell] for cell in row))
    return "\n".join(lines)


def render_maze(maze: list[str], mode: str = "tiles") -> str:
    if mode == "raw":
        return render_raw(maze)
    return render_tiles(maze)


def run_static_maze(
    maze: list[str],
    render: str = "tiles",
    source: str = "generated",
) -> None:
    start = find_cell(maze, "S")
    exit_cell = find_cell(maze, "E")

    print("MAZE=ready")
    print("mode=static")
    print(f"source={source}")
    if source == "default-fallback":
        print("warning=generated-maze-invalid")
    print("size=12x12")
    print(f"start={start[0]},{start[1]}")
    print(f"exit={exit_cell[0]},{exit_cell[1]}")
    print(f"render={render}")
    print(render_maze(maze, render))
    print("MAZE=pass")
    print("NEXT: install OpenCode")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print a tiny terminal maze.")
    parser.add_argument("--maze-file", help="Optional file containing a 12x12 maze")
    parser.add_argument(
        "--render",
        choices=["tiles", "raw"],
        default="tiles",
        help="Use tiles for a readable board, or raw to inspect the source maze",
    )
    args = parser.parse_args(argv)

    maze, source = load_lab_maze(args.maze_file)
    run_static_maze(maze, args.render, source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
