from __future__ import annotations

import io
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import verify_maze_movement


ROOT = Path(__file__).resolve().parents[1]


def correct_move(maze, position, command):
    deltas = {"w": (-1, 0), "s": (1, 0), "a": (0, -1), "d": (0, 1)}
    if command not in deltas:
        return position
    row = position[0] + deltas[command][0]
    col = position[1] + deltas[command][1]
    if row < 0 or row >= len(maze) or col < 0 or col >= len(maze[row]):
        return position
    return position if maze[row][col] == "#" else (row, col)


class MazeMovementVerifierTests(unittest.TestCase):
    def test_accepts_expected_movement(self):
        output = io.StringIO()
        with (
            patch.object(verify_maze_movement, "choose_next_position", correct_move),
            redirect_stdout(output),
        ):
            result = verify_maze_movement.main()

        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue(), "MAZE_MOVEMENT_CHECK=pass\n")

    def test_rejects_a_noop_implementation(self):
        output = io.StringIO()
        with (
            patch.object(
                verify_maze_movement,
                "choose_next_position",
                lambda maze, position, command: position,
            ),
            redirect_stdout(output),
        ):
            result = verify_maze_movement.main()

        self.assertEqual(result, 1)
        self.assertIn("MAZE_MOVEMENT_CHECK=fail", output.getvalue())
        self.assertIn(
            "case=move-right start=(1, 1) command='d' expected=(1, 2) actual=(1, 1)",
            output.getvalue(),
        )
        self.assertIn("case=move-down", output.getvalue())

    def test_requires_all_four_movement_directions(self):
        def only_down_and_right(maze, position, command):
            if command not in {"s", "d"}:
                return position
            return correct_move(maze, position, command)

        output = io.StringIO()
        with (
            patch.object(
                verify_maze_movement,
                "choose_next_position",
                only_down_and_right,
            ),
            redirect_stdout(output),
        ):
            result = verify_maze_movement.main()

        self.assertEqual(result, 1)
        self.assertIn("case=move-left", output.getvalue())
        self.assertIn("case=move-up", output.getvalue())

    def test_reports_boundary_exceptions_as_diagnostics(self):
        def no_bounds_check(maze, position, command):
            deltas = {"w": (-1, 0), "s": (1, 0), "a": (0, -1), "d": (0, 1)}
            if command not in deltas:
                return position
            row = position[0] + deltas[command][0]
            col = position[1] + deltas[command][1]
            return position if maze[row][col] == "#" else (row, col)

        output = io.StringIO()
        with (
            patch.object(
                verify_maze_movement,
                "choose_next_position",
                no_bounds_check,
            ),
            redirect_stdout(output),
        ):
            result = verify_maze_movement.main()

        self.assertEqual(result, 1)
        self.assertIn("case=bottom-boundary", output.getvalue())
        self.assertIn("raised IndexError", output.getvalue())

    def test_runs_directly_from_the_repo_root(self):
        result = subprocess.run(
            [sys.executable, "scripts/verify_maze_movement.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertIn(result.returncode, {0, 1})
        self.assertNotIn("ModuleNotFoundError", result.stderr)


if __name__ == "__main__":
    unittest.main()
