from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from dojo_app import maze_game


class MazeGameTests(unittest.TestCase):
    def test_default_maze_is_12_by_12(self):
        self.assertTrue(maze_game.valid_maze_lines(maze_game.DEFAULT_MAZE))

    def test_extract_maze_ignores_extra_text(self):
        text = "\n".join(["Here is a maze:", *maze_game.DEFAULT_MAZE, "done"])

        self.assertEqual(maze_game.extract_maze_lines(text), maze_game.DEFAULT_MAZE)

    def test_extract_maze_ignores_code_fence(self):
        text = "```text\n" + "\n".join(maze_game.DEFAULT_MAZE) + "\n```"

        self.assertEqual(maze_game.extract_maze_lines(text), maze_game.DEFAULT_MAZE)

    def test_find_start_and_exit(self):
        self.assertEqual(maze_game.find_cell(maze_game.DEFAULT_MAZE, "S"), (1, 1))
        self.assertEqual(maze_game.find_cell(maze_game.DEFAULT_MAZE, "E"), (10, 10))

    def test_load_maze_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "maze.txt"
            path.write_text("\n".join(maze_game.DEFAULT_MAZE), encoding="utf-8")

            self.assertEqual(maze_game.load_maze(str(path)), maze_game.DEFAULT_MAZE)

    def test_lab_loader_falls_back_for_bad_model_output(self):
        bad_model_text = "\n".join(
            [
                "#### ######",
                "#S..#.....#",
                "#..###.####",
                "#.....#..E#",
                "#.######.##",
                "#..#....###",
                "######.#..#",
                "#...###.###",
                "#.###...#..",
                "##..###....",
                "###### ####",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "maze.txt"
            path.write_text(bad_model_text, encoding="utf-8")

            maze, source = maze_game.load_lab_maze(str(path))

        self.assertEqual(maze, maze_game.DEFAULT_MAZE)
        self.assertEqual(source, "default-fallback")

    def test_tile_render_is_readable(self):
        rendered = maze_game.render_maze(maze_game.DEFAULT_MAZE)

        self.assertIn("██", rendered)
        self.assertIn("S ", rendered)
        self.assertIn("E ", rendered)
        self.assertNotIn("#", rendered)

    def test_raw_render_is_available_for_debugging(self):
        self.assertEqual(
            maze_game.render_maze(maze_game.DEFAULT_MAZE, "raw"),
            "\n".join(maze_game.DEFAULT_MAZE),
        )

    def test_static_run_prints_stable_markers(self):
        output = io.StringIO()

        with redirect_stdout(output):
            maze_game.run_static_maze(maze_game.DEFAULT_MAZE)

        text = output.getvalue()
        self.assertIn("MAZE=ready", text)
        self.assertIn("mode=static", text)
        self.assertIn("size=12x12", text)
        self.assertIn("render=tiles", text)
        self.assertIn("██", text)
        self.assertIn("MAZE=pass", text)
        self.assertIn("NEXT: install OpenCode", text)

    def test_static_run_prints_fallback_marker(self):
        output = io.StringIO()

        with redirect_stdout(output):
            maze_game.run_static_maze(maze_game.DEFAULT_MAZE, source="default-fallback")

        text = output.getvalue()
        self.assertIn("source=default-fallback", text)
        self.assertIn("warning=generated-maze-invalid", text)
        self.assertIn("MAZE=pass", text)


if __name__ == "__main__":
    unittest.main()
