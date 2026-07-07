from __future__ import annotations

import sys
import termios
import tty
from collections.abc import Callable
from pathlib import Path

from dojo_app.lab_output import format_status, print_status

MazeRenderer = Callable[[list[str], str], str]
Position = tuple[int, int]
MOVE_DELTAS: dict[str, Position] = {
    "w": (-1, 0),
    "s": (1, 0),
    "a": (0, -1),
    "d": (0, 1),
}
ROOT = Path(__file__).resolve().parents[1]
MAZE_SOLVED_MARKER = ROOT / ".lab-state" / "dojo" / "maze-solved"
SAVE_CURSOR = "\033[s"
RESTORE_CURSOR = "\033[u"
ERASE_LINE = "\033[2K"


def choose_next_position(maze: list[str], position: Position, command: str) -> Position:
    # OpenCode exercise: replace this placeholder body with MOVE_DELTAS boundary rules.
    return position


def find_start(maze: list[str]) -> Position:
    for row_index, row in enumerate(maze):
        col_index = row.find("S")
        if col_index != -1:
            return row_index, col_index
    return 1, 1


def maze_with_player(maze: list[str], position: Position) -> list[str]:
    player_row, player_col = position
    display = []
    for row_index, row in enumerate(maze):
        if row_index == player_row:
            display.append(row[:player_col] + "@" + row[player_col + 1 :])
        else:
            display.append(row)
    return display


def live_terminal() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def enable_single_key_input():
    try:
        stdin_fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(stdin_fd)
        tty.setcbreak(stdin_fd)
        return old_settings
    except (AttributeError, OSError, termios.error, ValueError):
        return None


def restore_input_mode(old_settings) -> None:
    if old_settings is None:
        return
    try:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
    except (AttributeError, OSError, termios.error, ValueError):
        return


def read_command(single_key: bool) -> str:
    if not single_key:
        return input("move> ").strip().lower()

    sys.stdout.write("move> ")
    sys.stdout.flush()
    command = sys.stdin.read(1)
    print()
    return command.strip().lower()


def draw_frame(
    maze: list[str],
    player: Position,
    render_maze: MazeRenderer,
    render: str,
    redraw: bool,
    show_header: bool,
    status: str = "",
    first_frame: bool = False,
) -> None:
    if not redraw:
        if show_header:
            print_status("MAZE_PLAY=ready")
            print("controls=w/a/s/d, q to quit")
        if status:
            print_status(status)
        print(render_maze(maze_with_player(maze, player), render))
        return

    target = sys.stdout
    lines = [
        format_status("MAZE_PLAY=ready", target),
        "controls=w/a/s/d, q to quit",
        format_status(status, target) if status else "",
        *render_maze(maze_with_player(maze, player), render).splitlines(),
    ]

    if first_frame:
        target.write("\r\n" * (len(lines) + 1))
        target.write(f"\033[{len(lines) + 1}A{SAVE_CURSOR}")
    else:
        target.write(RESTORE_CURSOR)

    for line in lines:
        target.write(f"{ERASE_LINE}\r{line}\r\n")
    target.write(f"{ERASE_LINE}\r")
    target.flush()


def record_maze_win() -> None:
    MAZE_SOLVED_MARKER.parent.mkdir(parents=True, exist_ok=True)
    MAZE_SOLVED_MARKER.write_text("MAZE_PLAY=win\n", encoding="utf-8")


def run_play_maze(maze: list[str], render_maze: MazeRenderer, render: str = "amaze") -> int:
    player = find_start(maze)
    redraw = live_terminal()
    old_settings = enable_single_key_input() if redraw else None
    single_key = old_settings is not None
    first_frame = True
    status = ""

    try:
        while True:
            draw_frame(
                maze,
                player,
                render_maze,
                render,
                redraw,
                first_frame or redraw,
                status,
                first_frame,
            )
            first_frame = False
            status = ""

            try:
                command = read_command(single_key)
            except EOFError:
                print_status("MAZE_PLAY=quit")
                return 0

            if not command:
                status = "move=ignored"
                continue
            if command == "q":
                print_status("MAZE_PLAY=quit")
                return 0
            if command not in MOVE_DELTAS:
                status = "move=ignored"
                continue

            try:
                player = choose_next_position(maze, player, command)
            except NotImplementedError:
                print_status("MAZE_PLAY=not-implemented")
                print("reason=OpenCode will replace choose_next_position in dojo_app/maze_play.py")
                return 1

            row, col = player
            if maze[row][col] == "E":
                draw_frame(maze, player, render_maze, render, redraw, redraw)
                record_maze_win()
                print_status("MAZE_PLAY=win")
                return 0
    finally:
        restore_input_mode(old_settings)
