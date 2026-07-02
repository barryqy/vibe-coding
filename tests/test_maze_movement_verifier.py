from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts import verify_maze_movement


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
        with patch.object(verify_maze_movement, "choose_next_position", correct_move):
            self.assertEqual(verify_maze_movement.main(), 0)

    def test_rejects_a_noop_implementation(self):
        with patch.object(
            verify_maze_movement,
            "choose_next_position",
            lambda maze, position, command: position,
        ):
            self.assertEqual(verify_maze_movement.main(), 1)


if __name__ == "__main__":
    unittest.main()
