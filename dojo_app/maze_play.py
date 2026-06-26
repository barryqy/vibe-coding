from __future__ import annotations

from collections.abc import Callable


MazeRenderer = Callable[[list[str], str], str]
Position = tuple[int, int]
MOVE_DELTAS: dict[str, Position] = {
    "w": (-1, 0),
    "s": (1, 0),
    "a": (0, -1),
    "d": (0, 1),
}


def choose_next_position(maze: list[str], position: Position, command: str) -> Position:
    # OpenCode exercise: replace only this body with MOVE_DELTAS boundary rules.
    raise NotImplementedError("OpenCode will replace this movement function")


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


def run_play_maze(maze: list[str], render_maze: MazeRenderer, render: str = "amaze") -> int:
    player = find_start(maze)
    print("MAZE_PLAY=ready")
    print("controls=w/a/s/d, q to quit")

    while True:
        print(render_maze(maze_with_player(maze, player), render))
        try:
            command = input("move> ").strip().lower()
        except EOFError:
            print("MAZE_PLAY=quit")
            return 0

        if command == "q":
            print("MAZE_PLAY=quit")
            return 0
        if command not in {"w", "a", "s", "d"}:
            print("move=ignored")
            continue

        try:
            player = choose_next_position(maze, player, command)
        except NotImplementedError:
            print("MAZE_PLAY=not-implemented")
            print("reason=OpenCode will replace choose_next_position in dojo_app/maze_play.py")
            return 1

        row, col = player
        if maze[row][col] == "E":
            print(render_maze(maze_with_player(maze, player), render))
            print("MAZE_PLAY=win")
            return 0
