from __future__ import annotations

from collections.abc import Callable


MazeRenderer = Callable[[list[str], str], str]


def run_play_maze(maze: list[str], render_maze: MazeRenderer, render: str = "amaze") -> int:
    # OpenCode exercise: keep this function signature and replace only this body.
    print("MAZE_PLAY=not-implemented")
    print("reason=OpenCode will replace this function body in dojo_app/maze_play.py")
    return 1
