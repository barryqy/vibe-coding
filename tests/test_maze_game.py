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

    def test_default_maze_is_solvable(self):
        self.assertTrue(maze_game.maze_is_solvable(maze_game.DEFAULT_MAZE))
        self.assertIsInstance(maze_game.shortest_path_length(maze_game.DEFAULT_MAZE), int)

    def test_extract_maze_ignores_extra_text(self):
        text = "\n".join(["Here is a maze:", *maze_game.DEFAULT_MAZE, "done"])

        self.assertEqual(maze_game.extract_maze_lines(text), maze_game.DEFAULT_MAZE)

    def test_extract_maze_ignores_code_fence(self):
        text = "```text\n" + "\n".join(maze_game.DEFAULT_MAZE) + "\n```"

        self.assertEqual(maze_game.extract_maze_lines(text), maze_game.DEFAULT_MAZE)

    def test_extract_maze_accepts_single_block_diagram(self):
        block = "\n".join(
            row.replace("#", "█").replace(".", " ") for row in maze_game.DEFAULT_MAZE
        )

        self.assertEqual(maze_game.extract_maze_lines(block), maze_game.DEFAULT_MAZE)
        maze, maze_format = maze_game.extract_maze(block)
        self.assertEqual(maze, maze_game.DEFAULT_MAZE)
        self.assertEqual(maze_format, "block")

    def test_extract_maze_accepts_tile_diagram(self):
        tile = maze_game.render_maze(maze_game.DEFAULT_MAZE, "tiles")

        self.assertEqual(maze_game.extract_maze_lines(tile), maze_game.DEFAULT_MAZE)

    def test_extract_maze_rejects_unsolvable_maze(self):
        unsolvable = "\n".join(
            [
                "############",
                "#S##########",
                "############",
                "############",
                "############",
                "############",
                "############",
                "############",
                "############",
                "############",
                "##########E#",
                "############",
            ]
        )

        with self.assertRaises(ValueError):
            maze_game.extract_maze_lines(unsolvable)

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

    def test_lab_loader_falls_back_for_missing_model_output(self):
        maze, source = maze_game.load_lab_maze("/tmp/maze-output-that-does-not-exist.txt")

        self.assertEqual(maze, maze_game.DEFAULT_MAZE)
        self.assertEqual(source, "default-fallback")

    def test_tile_render_is_readable(self):
        rendered = maze_game.render_maze(maze_game.DEFAULT_MAZE, "tiles")
        lines = rendered.splitlines()

        self.assertTrue(all(len(line) == maze_game.MAZE_SIZE * 2 for line in lines))
        self.assertIn("██", rendered)
        self.assertIn("S ", rendered)
        self.assertIn("E ", rendered)
        self.assertNotIn("#", rendered)

    def test_amaze_render_uses_classic_terminal_walls(self):
        rendered = maze_game.render_maze(maze_game.DEFAULT_MAZE)
        lines = rendered.splitlines()

        self.assertEqual(len(lines), (maze_game.MAZE_SIZE - 2) * 2 + 1)
        self.assertTrue(all(len(line) == (maze_game.MAZE_SIZE - 2) * 4 + 1 for line in lines))
        self.assertTrue(all(line.startswith(("+", "|")) for line in lines))
        self.assertIn("+---+", rendered)
        self.assertIn("| S ", rendered)
        self.assertIn("| E ", rendered)
        self.assertNotIn("██", rendered)

    def test_raw_render_is_available_for_debugging(self):
        self.assertEqual(
            maze_game.render_maze(maze_game.DEFAULT_MAZE, "raw"),
            "\n".join(maze_game.DEFAULT_MAZE),
        )

    def test_move_player_respects_paths_and_walls(self):
        start = maze_game.find_cell(maze_game.DEFAULT_MAZE, "S")

        self.assertEqual(maze_game.move_player(maze_game.DEFAULT_MAZE, start, "d"), (2, 1))
        self.assertEqual(maze_game.move_player(maze_game.DEFAULT_MAZE, start, "right"), (2, 1))
        self.assertEqual(maze_game.move_player(maze_game.DEFAULT_MAZE, start, "a"), start)
        self.assertEqual(maze_game.move_player(maze_game.DEFAULT_MAZE, start, "up"), start)
        self.assertEqual(maze_game.move_player(maze_game.DEFAULT_MAZE, start, "nonsense"), start)

    def test_render_player_maze_marks_player(self):
        start = maze_game.find_cell(maze_game.DEFAULT_MAZE, "S")
        raw = maze_game.render_player_maze(maze_game.DEFAULT_MAZE, start, "raw")
        amaze = maze_game.render_player_maze(maze_game.DEFAULT_MAZE, start)
        tiles = maze_game.render_player_maze(maze_game.DEFAULT_MAZE, start, "tiles")

        self.assertIn("@", raw)
        self.assertNotIn("S", raw)
        self.assertIn("| @ ", amaze)
        self.assertIn("+---+", amaze)
        self.assertIn("@ ", tiles)
        self.assertIn("██", tiles)

    def test_play_loop_can_quit(self):
        output = io.StringIO()
        moves = iter(["q"])

        with redirect_stdout(output):
            maze_game.run_play_maze(
                maze_game.DEFAULT_MAZE,
                input_func=lambda _prompt: next(moves),
            )

        text = output.getvalue()
        self.assertIn("MAZE_PLAY=ready", text)
        self.assertIn("MAZE_PLAY=quit", text)
        self.assertIn("MAZE_PLAY=pass", text)

    def test_static_run_prints_stable_markers(self):
        output = io.StringIO()

        with redirect_stdout(output):
            maze_game.run_static_maze(maze_game.DEFAULT_MAZE)

        text = output.getvalue()
        self.assertIn("MAZE=ready", text)
        self.assertIn("mode=static", text)
        self.assertIn("size=12x12", text)
        self.assertIn("render=amaze", text)
        self.assertIn("+---+", text)
        self.assertIn("MAZE=pass", text)

    def test_static_run_prints_fallback_marker(self):
        output = io.StringIO()

        with redirect_stdout(output):
            maze_game.run_static_maze(maze_game.DEFAULT_MAZE, source="default-fallback")

        text = output.getvalue()
        self.assertIn("source=default-fallback", text)
        self.assertIn("warning=generated-maze-invalid", text)
        self.assertIn("MAZE=pass", text)

    def test_check_only_prints_solvable_markers(self):
        output = io.StringIO()
        block = "\n".join(
            row.replace("#", "█").replace(".", " ") for row in maze_game.DEFAULT_MAZE
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "maze.txt"
            path.write_text(block, encoding="utf-8")
            with redirect_stdout(output):
                result = maze_game.main(["--maze-file", str(path), "--check-only"])

        text = output.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("MAZE_CHECK=ready", text)
        self.assertIn("format=block", text)
        self.assertIn("solvable=yes", text)
        self.assertIn("MAZE_CHECK=pass", text)

    def test_check_only_fails_bad_diagram(self):
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "maze.txt"
            path.write_text("not a maze", encoding="utf-8")
            with redirect_stdout(output):
                result = maze_game.main(["--maze-file", str(path), "--check-only"])

        self.assertEqual(result, 1)
        self.assertIn("MAZE_CHECK=fail", output.getvalue())

    def test_repair_file_replaces_bad_diagram(self):
        output = io.StringIO()
        bad_diagram = "\n".join(
            [
                "████████████████████████",
                "██S  ██      ██      ██",
                "██  ████  ██  ██  ██  ██",
                "██      ██  ██      E",
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "maze.txt"
            path.write_text(bad_diagram, encoding="utf-8")
            with redirect_stdout(output):
                result = maze_game.main(
                    ["--maze-file", str(path), "--check-only", "--repair-file"]
                )

            repaired = path.read_text(encoding="utf-8")

        text = output.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("source=default-fallback", text)
        self.assertIn("warning=generated-maze-invalid", text)
        self.assertIn("MAZE_CHECK=pass", text)
        self.assertEqual(maze_game.extract_maze_lines(repaired), maze_game.DEFAULT_MAZE)


if __name__ == "__main__":
    unittest.main()
