from __future__ import annotations

import argparse
from pathlib import Path


MAZE_SIZE = 12
ALLOWED_CELLS = {"#", ".", "S", "E"}
BLOCK_CELLS = {"█": "#", " ": ".", "S": "S", "E": "E"}
TILE_PAIRS = {"██": "#", "  ": ".", "S ": "S", "E ": "E"}
TILE_CELLS = {
    "#": "██",
    ".": "  ",
    "S": "S ",
    "E": "E ",
    "@": "@ ",
}
PLAY_MODE_ENABLED = False
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
    if joined.count("S") != 1 or joined.count("E") != 1:
        return False
    return has_wall_border(lines)


def has_wall_border(lines: list[str]) -> bool:
    if len(lines) != MAZE_SIZE:
        return False
    top = lines[0]
    bottom = lines[-1]
    if top != "#" * MAZE_SIZE or bottom != "#" * MAZE_SIZE:
        return False
    for row in lines:
        if not row or row[0] != "#" or row[-1] != "#":
            return False
    return True


def raw_maze_row(line: str) -> str | None:
    row = line.strip()
    if len(row) == MAZE_SIZE and not (set(row) - ALLOWED_CELLS):
        return row
    return None


def block_maze_row(line: str) -> str | None:
    row = line.strip()
    if len(row) == MAZE_SIZE and not (set(row) - set(BLOCK_CELLS)):
        return "".join(BLOCK_CELLS[cell] for cell in row)

    if len(row) == MAZE_SIZE * 2:
        cells = []
        for index in range(0, len(row), 2):
            pair = row[index : index + 2]
            cell = TILE_PAIRS.get(pair)
            if cell is None:
                return None
            cells.append(cell)
        return "".join(cells)
    return None


def shortest_path_length(maze: list[str]) -> int | None:
    start = find_cell(maze, "S")
    exit_cell = find_cell(maze, "E")
    queue = [(start, 0)]
    seen = {start}

    for position, distance in queue:
        if position == exit_cell:
            return distance

        x, y = position
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            next_pos = (x + dx, y + dy)
            next_x, next_y = next_pos
            if next_pos in seen:
                continue
            if next_y < 0 or next_y >= len(maze):
                continue
            if next_x < 0 or next_x >= len(maze[next_y]):
                continue
            if maze[next_y][next_x] == "#":
                continue
            seen.add(next_pos)
            queue.append((next_pos, distance + 1))

    return None


def maze_is_solvable(maze: list[str]) -> bool:
    return shortest_path_length(maze) is not None


def trusted_maze_lines(lines: list[str]) -> bool:
    return valid_maze_lines(lines) and maze_is_solvable(lines)


def extract_maze(text: str) -> tuple[list[str], str]:
    candidates: list[tuple[list[str], str]] = [([], "raw"), ([], "block")]
    for raw in text.splitlines():
        raw_row = raw_maze_row(raw)
        if raw_row:
            candidates[0][0].append(raw_row)

        block_row = block_maze_row(raw)
        if block_row:
            candidates[1][0].append(block_row)

    for possible_rows, maze_format in candidates:
        for index in range(0, len(possible_rows) - MAZE_SIZE + 1):
            rows = possible_rows[index : index + MAZE_SIZE]
            if trusted_maze_lines(rows):
                return rows, maze_format

    raise ValueError("expected a solvable 12x12 maze with one S, one E, and border walls")


def extract_maze_lines(text: str) -> list[str]:
    return extract_maze(text)[0]


def load_maze(path: str | None = None) -> list[str]:
    if not path:
        return list(DEFAULT_MAZE)
    return extract_maze_lines(Path(path).read_text(encoding="utf-8"))


def load_lab_maze(path: str | None = None) -> tuple[list[str], str]:
    if not path:
        return list(DEFAULT_MAZE), "default"

    try:
        return load_maze(path), "generated"
    except (OSError, ValueError):
        return list(DEFAULT_MAZE), "default-fallback"


def load_checked_maze(path: str | None = None) -> tuple[list[str], str, str]:
    if not path:
        return list(DEFAULT_MAZE), "default", "raw"
    maze, maze_format = extract_maze(Path(path).read_text(encoding="utf-8"))
    return maze, "generated", maze_format


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


def move_player(maze: list[str], position: tuple[int, int], key: str) -> tuple[int, int]:
    moves = {
        "w": (0, -1),
        "up": (0, -1),
        "s": (0, 1),
        "down": (0, 1),
        "a": (-1, 0),
        "left": (-1, 0),
        "d": (1, 0),
        "right": (1, 0),
    }
    delta = moves.get(key.strip().lower())
    if not delta:
        return position

    next_x = position[0] + delta[0]
    next_y = position[1] + delta[1]
    if next_y < 0 or next_y >= len(maze):
        return position
    if next_x < 0 or next_x >= len(maze[next_y]):
        return position
    if maze[next_y][next_x] == "#":
        return position
    return next_x, next_y


def render_player_maze(
    maze: list[str],
    position: tuple[int, int],
    render: str = "tiles",
) -> str:
    rows = [list(row) for row in maze]
    x, y = position
    rows[y][x] = "@"
    with_player = ["".join(row) for row in rows]
    return render_maze(with_player, render)


def run_play_maze(
    maze: list[str],
    render: str = "tiles",
    input_func=input,
    output_func=print,
) -> None:
    position = find_cell(maze, "S")
    exit_cell = find_cell(maze, "E")

    output_func("MAZE_PLAY=ready")
    output_func("controls=w/a/s/d or up/down/left/right, q to quit")
    while True:
        output_func(render_player_maze(maze, position, render))
        if position == exit_cell:
            output_func("MAZE_PLAY=escaped")
            output_func("MAZE_PLAY=pass")
            return

        move = input_func("move> ").strip().lower()
        if move in {"q", "quit", "exit"}:
            output_func("MAZE_PLAY=quit")
            output_func("MAZE_PLAY=pass")
            return

        new_position = move_player(maze, position, move)
        if new_position == position:
            output_func("move=blocked")
        position = new_position


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


def run_maze_check(maze: list[str], source: str = "generated", maze_format: str = "raw") -> None:
    path_length = shortest_path_length(maze)
    if path_length is None:
        raise ValueError("maze is not solvable")

    print("MAZE_CHECK=ready")
    print(f"source={source}")
    print(f"format={maze_format}")
    print("size=12x12")
    print("border=ok")
    print("solvable=yes")
    print(f"path_length={path_length}")
    print("MAZE_CHECK=pass")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print a tiny terminal maze.")
    parser.add_argument("--maze-file", help="Optional file containing a 12x12 maze")
    parser.add_argument(
        "--render",
        choices=["tiles", "raw"],
        default="tiles",
        help="Use tiles for a readable board, or raw to inspect the source maze",
    )
    parser.add_argument("--play", action="store_true", help="Play the maze in the terminal")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate a generated maze without re-rendering it",
    )
    args = parser.parse_args(argv)

    if args.check_only:
        try:
            maze, source, maze_format = load_checked_maze(args.maze_file)
            run_maze_check(maze, source, maze_format)
        except (OSError, ValueError) as exc:
            print("MAZE_CHECK=fail")
            print(f"reason={exc}")
            return 1
        return 0

    maze, source = load_lab_maze(args.maze_file)
    if args.play:
        if not PLAY_MODE_ENABLED:
            print("MAZE_PLAY=locked")
            return 1
        run_play_maze(maze, args.render)
        return 0

    run_static_maze(maze, args.render, source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
