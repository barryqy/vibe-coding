from __future__ import annotations

import argparse
import random
import re
from pathlib import Path


MAZE_SIZE = 12
ALLOWED_CELLS = {"#", ".", "S", "E"}
ROOM_VALUES = (1, 3, 5, 7, 9)
ROOMS = {(row, col) for row in ROOM_VALUES for col in ROOM_VALUES}
MOVE_DELTAS = {
    "N": (-2, 0),
    "S": (2, 0),
    "E": (0, 2),
    "W": (0, -2),
}
PLAN_LINE_RE = re.compile(r"^(SEED|ORDER)\s*[:=]\s*(.+)$", re.IGNORECASE)
BLOCK_CELLS = {"█": "#", " ": ".", "S": "S", "E": "E"}
TILE_PAIRS = {"██": "#", "  ": ".", "S ": "S", "E ": "E"}
TILE_CELLS = {
    "#": "██",
    ".": "  ",
    "S": "S ",
    "E": "E ",
    "@": "@ ",
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


def parse_maze_plan(text: str) -> tuple[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        match = PLAN_LINE_RE.match(raw.strip())
        if match:
            values[match.group(1).upper()] = match.group(2).strip()

    seed = values.get("SEED", "")
    raw_order = values.get("ORDER", "").upper()
    order_tokens = re.findall(r"\b[NSEW]{4}\b", raw_order)
    order = order_tokens[0] if order_tokens else raw_order.replace(" ", "")

    if not seed:
        raise ValueError("maze plan needs SEED")
    if len(seed) > 64:
        raise ValueError("maze plan SEED is too long")
    if len(order) != 4 or set(order) != set(MOVE_DELTAS):
        raise ValueError("maze plan ORDER must contain N, S, E, and W once")
    return seed, order


def generate_maze_from_plan(seed: str, order: str) -> list[str]:
    rng = random.Random(f"{seed}:{order}")
    rows = [["#"] * MAZE_SIZE for _ in range(MAZE_SIZE)]
    current = (1, 1)
    stack = [current]
    seen = {current}
    rows[1][1] = "."

    while stack:
        row, col = stack[-1]
        choices = []
        for direction in order:
            dr, dc = MOVE_DELTAS[direction]
            next_room = (row + dr, col + dc)
            if next_room in ROOMS and next_room not in seen:
                choices.append((direction, next_room))

        if not choices:
            stack.pop()
            continue

        direction, next_room = choices[rng.randrange(len(choices))]
        dr, dc = MOVE_DELTAS[direction]
        wall_row = row + dr // 2
        wall_col = col + dc // 2
        rows[wall_row][wall_col] = "."
        rows[next_room[0]][next_room[1]] = "."
        seen.add(next_room)
        stack.append(next_room)

    rows[1][1] = "S"
    rows[9][10] = "."
    rows[10][10] = "E"
    maze = ["".join(row) for row in rows]
    if seen != ROOMS or not trusted_maze_lines(maze):
        raise ValueError("maze plan did not produce a trusted maze")
    return maze


def load_maze_plan(path: str) -> tuple[list[str], str, str]:
    seed, order = parse_maze_plan(Path(path).read_text(encoding="utf-8"))
    return generate_maze_from_plan(seed, order), "plan", "recursive-backtracker"


def write_maze(path: str, maze: list[str]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(maze) + "\n", encoding="utf-8")


def load_maze(path: str | None = None) -> list[str]:
    if not path:
        return list(DEFAULT_MAZE)
    return extract_maze_lines(Path(path).read_text(encoding="utf-8"))


def load_lab_maze(path: str | None = None) -> tuple[list[str], str]:
    if not path:
        return list(DEFAULT_MAZE), "default"
    return load_maze(path), "generated"


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


def render_amaze(maze: list[str]) -> str:
    if len(maze) <= 2 or len(maze[0]) <= 2:
        return render_raw(maze)

    lines = []
    for y in range(1, len(maze) - 1):
        top = ""
        body = ""
        row = maze[y]
        for x in range(1, len(row) - 1):
            cell = row[x]
            north_wall = y == 1 or cell == "#" or maze[y - 1][x] == "#"
            west_wall = x == 1 or cell == "#" or row[x - 1] == "#"
            marker = cell if cell in {"S", "E", "@"} else " "
            top += "+" + ("---" if north_wall else "   ")
            body += ("|" if west_wall else " ") + f" {marker} "
        lines.append(top + "+")
        lines.append(body + "|")
    lines.append("+" + "---+" * (len(maze[0]) - 2))
    return "\n".join(lines)


def render_maze(maze: list[str], mode: str = "amaze") -> str:
    if mode == "raw":
        return render_raw(maze)
    if mode == "tiles":
        return render_tiles(maze)
    if mode == "amaze":
        return render_amaze(maze)
    raise ValueError(f"unsupported render mode: {mode}")


def run_static_maze(
    maze: list[str],
    render: str = "amaze",
    source: str = "generated",
) -> None:
    start = find_cell(maze, "S")
    exit_cell = find_cell(maze, "E")

    print("MAZE=ready")
    print("mode=static")
    print(f"source={source}")
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
    parser.add_argument("--plan-file", help="Optional file containing SEED and ORDER lines")
    parser.add_argument("--write-maze", help="Write the checked raw maze to this path")
    parser.add_argument(
        "--render",
        choices=["amaze", "tiles", "raw"],
        default="amaze",
        help="Use amaze for a +---+ board, tiles for block walls, or raw to inspect source data",
    )
    parser.add_argument("--play", action="store_true", help="Play the maze in the terminal")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate a generated maze without re-rendering it",
    )
    args = parser.parse_args(argv)

    if args.maze_file and args.plan_file:
        parser.error("use --maze-file or --plan-file, not both")

    if args.check_only:
        try:
            if args.plan_file:
                maze, source, maze_format = load_maze_plan(args.plan_file)
            else:
                maze, source, maze_format = load_checked_maze(args.maze_file)
            if args.write_maze:
                write_maze(args.write_maze, maze)
            run_maze_check(maze, source, maze_format)
        except (OSError, ValueError) as exc:
            print("MAZE_CHECK=fail")
            print(f"reason={exc}")
            return 1
        return 0

    try:
        if args.plan_file:
            maze, source, _maze_format = load_maze_plan(args.plan_file)
        else:
            maze, source = load_lab_maze(args.maze_file)
        if args.write_maze:
            write_maze(args.write_maze, maze)
    except (OSError, ValueError) as exc:
        print("MAZE=fail")
        print(f"reason={exc}")
        return 1

    if args.play:
        print("MAZE_PLAY=not-implemented")
        print("reason=OpenCode will add the playable loop in the next lab step")
        return 1

    run_static_maze(maze, args.render, source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
