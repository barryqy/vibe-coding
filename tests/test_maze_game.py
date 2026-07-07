from __future__ import annotations

import io
import inspect
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from dojo_app import maze_game
from dojo_app import maze_play


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

    def test_lab_loader_rejects_bad_model_output(self):
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

            with self.assertRaises(ValueError):
                maze_game.load_lab_maze(str(path))

    def test_lab_loader_rejects_missing_model_output(self):
        with self.assertRaises(OSError):
            maze_game.load_lab_maze("/tmp/maze-output-that-does-not-exist.txt")

    def test_maze_plan_generates_trusted_maze(self):
        seed, order = maze_game.parse_maze_plan("SEED: lab-42\nORDER: NESW\n")
        maze = maze_game.generate_maze_from_plan(seed, order)

        self.assertTrue(maze_game.trusted_maze_lines(maze))
        self.assertEqual(maze_game.find_cell(maze, "S"), (1, 1))
        self.assertEqual(maze_game.find_cell(maze, "E"), (10, 10))

    def test_maze_plan_changes_with_seed(self):
        first = maze_game.generate_maze_from_plan("lab-42", "NESW")
        second = maze_game.generate_maze_from_plan("lab-43", "NESW")

        self.assertNotEqual(first, second)
        self.assertTrue(maze_game.trusted_maze_lines(second))

    def test_maze_plan_rejects_bad_order(self):
        with self.assertRaises(ValueError):
            maze_game.parse_maze_plan("SEED: lab-42\nORDER: NNNN\n")

    def test_maze_plan_accepts_order_with_punctuation(self):
        seed, order = maze_game.parse_maze_plan("SEED: lab-42\nORDER: SWEN.\n")

        self.assertEqual(seed, "lab-42")
        self.assertEqual(order, "SWEN")

    def test_plan_cli_writes_checked_maze(self):
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "maze-plan.txt"
            maze_path = Path(tmp) / "maze.txt"
            plan_path.write_text("SEED: lab-42\nORDER: NESW\n", encoding="utf-8")
            with redirect_stdout(output):
                result = maze_game.main(
                    [
                        "--plan-file",
                        str(plan_path),
                        "--write-maze",
                        str(maze_path),
                        "--check-only",
                    ]
                )

            written_maze = maze_path.read_text(encoding="utf-8")

        self.assertEqual(result, 0)
        self.assertIn("source=plan", output.getvalue())
        self.assertIn("format=recursive-backtracker", output.getvalue())
        self.assertTrue(maze_game.trusted_maze_lines(maze_game.extract_maze_lines(written_maze)))

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

    def test_static_cli_fails_bad_diagram(self):
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
                result = maze_game.main(["--maze-file", str(path)])

        text = output.getvalue()
        self.assertEqual(result, 1)
        self.assertIn("MAZE=fail", text)
        self.assertIn("expected a solvable 12x12 maze", text)

    def test_play_module_has_stable_agent_boundary(self):
        signature = inspect.signature(maze_play.run_play_maze)

        self.assertEqual(
            list(signature.parameters),
            ["maze", "render_maze", "render"],
        )

    def test_play_module_exposes_simple_movement_map(self):
        self.assertEqual(
            maze_play.MOVE_DELTAS,
            {
                "w": (-1, 0),
                "s": (1, 0),
                "a": (0, -1),
                "d": (0, 1),
            },
        )

    def test_play_redraw_preserves_existing_terminal_output(self):
        output = io.StringIO()
        output.write("LAST_COMMAND_OUTPUT\n")

        with redirect_stdout(output):
            maze_play.draw_frame(
                ["#####", "#S.E#", "#####"],
                (1, 1),
                lambda _maze, _render: "board",
                "amaze",
                redraw=True,
                show_header=True,
                first_frame=True,
            )
            maze_play.draw_frame(
                ["#####", "#S.E#", "#####"],
                (1, 2),
                lambda _maze, _render: "board",
                "amaze",
                redraw=True,
                show_header=True,
            )

        text = output.getvalue()
        self.assertTrue(text.startswith("LAST_COMMAND_OUTPUT\n"))
        self.assertNotIn("\033[H", text)
        self.assertNotIn("\033[2J", text)
        self.assertIn(maze_play.SAVE_CURSOR, text)
        self.assertIn(maze_play.RESTORE_CURSOR, text)

    def test_play_mode_does_not_clear_when_piped(self):
        output = io.StringIO()

        with (
            mock.patch("sys.stdin", io.StringIO("q\n")),
            mock.patch.object(maze_play, "capture_maze_escape") as capture,
            redirect_stdout(output),
        ):
            result = maze_play.run_play_maze(maze_game.DEFAULT_MAZE, maze_game.render_maze)

        text = output.getvalue()
        self.assertEqual(result, 0)
        capture.assert_not_called()
        self.assertIn("MAZE_PLAY=ready", text)
        self.assertIn("MAZE_PLAY=quit", text)
        self.assertNotIn("\033[H\033[2J", text)

    def test_play_mode_captures_flag_after_win(self):
        maze = ["#####", "#SE##", "#####"]

        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "maze-solved"
            with (
                mock.patch("sys.stdin", io.StringIO("d\n")),
                mock.patch.object(maze_play, "choose_next_position", return_value=(1, 2)),
                mock.patch.object(maze_play, "MAZE_SOLVED_MARKER", marker),
                mock.patch.object(maze_play, "capture_maze_escape", return_value=0) as capture,
                redirect_stdout(io.StringIO()),
            ):
                result = maze_play.run_play_maze(maze, lambda _maze, _render: "board")

            self.assertEqual(result, 0)
            capture.assert_called_once_with()
            self.assertEqual(marker.read_text(encoding="utf-8"), "MAZE_PLAY=win\n")


if __name__ == "__main__":
    unittest.main()
