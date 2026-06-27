from __future__ import annotations

import io
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from dojo_app import tictactoe_game
from dojo_app import tictactoe_play


class TicTacToeGameTests(unittest.TestCase):
    def test_parse_scenario_accepts_simple_board(self):
        scenario = tictactoe_game.parse_scenario(
            """
            MODE: human-vs-computer
            NEXT: X
            BOARD:
            . . .
            . . .
            . . .
            """
        )

        self.assertEqual(scenario.mode, "human-vs-computer")
        self.assertEqual(scenario.next_player, "X")
        self.assertEqual(scenario.board, tuple("........."))

    def test_parse_scenario_accepts_pipe_board(self):
        scenario = tictactoe_game.parse_scenario(
            """
            MODE: human-vs-human
            NEXT: O
            BOARD:
            X | O | X
            . | O | .
            . | . | X
            """
        )

        self.assertEqual(scenario.mode, "human-vs-human")
        self.assertEqual(scenario.next_player, "O")
        self.assertEqual(scenario.board.count("X"), 3)
        self.assertEqual(scenario.board.count("O"), 2)

    def test_parse_scenario_accepts_model_explanation(self):
        scenario = tictactoe_game.parse_scenario(
            """
            Access to project context is restricted.

            1. Game Mode: Human vs. Computer.
            2. Since the game has just started, `NEXT` is `X`.
            3. Board Layout:
            ```
            BOARD:
            . . .
            . . .
            . . .
            ```
            """
        )

        self.assertEqual(scenario.mode, "human-vs-computer")
        self.assertEqual(scenario.next_player, "X")
        self.assertEqual(scenario.board, tuple("........."))

    def test_rejects_impossible_turn_count(self):
        with self.assertRaises(ValueError):
            tictactoe_game.parse_scenario(
                """
                MODE: human-vs-computer
                NEXT: X
                BOARD:
                O O .
                . . .
                . . .
                """
            )

    def test_render_board_shows_numbers_for_empty_cells(self):
        board = tuple("X..O.....")
        rendered = tictactoe_game.render_board(board)

        self.assertIn(" X | 2 | 3 ", rendered)
        self.assertIn(" O | 5 | 6 ", rendered)

    def test_check_only_prints_stable_markers(self):
        output = io.StringIO()
        scenario = tictactoe_game.parse_scenario(tictactoe_game.DEFAULT_SCENARIO_TEXT)

        with redirect_stdout(output):
            tictactoe_game.run_scenario_check(scenario)

        text = output.getvalue()
        self.assertIn("TICTACTOE_CHECK=ready", text)
        self.assertIn("mode=human-vs-computer", text)
        self.assertIn("TICTACTOE_CHECK=pass", text)

    def test_cli_check_only_reads_file(self):
        output = io.StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.txt"
            path.write_text(tictactoe_game.DEFAULT_SCENARIO_TEXT, encoding="utf-8")
            with redirect_stdout(output):
                result = tictactoe_game.main(["--scenario-file", str(path), "--check-only"])

        self.assertEqual(result, 0)
        self.assertIn("TICTACTOE_CHECK=pass", output.getvalue())

    def test_cli_write_clean_normalizes_model_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.txt"
            path.write_text(
                """
                Game Mode: Human vs. Computer.
                NEXT is X.
                BOARD:
                . . .
                . . .
                . . .
                """,
                encoding="utf-8",
            )
            result = tictactoe_game.main(["--scenario-file", str(path), "--write-clean", str(path), "--check-only"])

            text = path.read_text(encoding="utf-8")

        self.assertEqual(result, 0)
        self.assertEqual(text, tictactoe_game.DEFAULT_SCENARIO_TEXT)

    def test_static_run_prints_board(self):
        output = io.StringIO()
        scenario = tictactoe_game.parse_scenario(tictactoe_game.DEFAULT_SCENARIO_TEXT)

        with redirect_stdout(output):
            tictactoe_game.run_static_scenario(scenario)

        text = output.getvalue()
        self.assertIn("Tic-tac-toe starting board", text)
        self.assertIn("Game mode: human vs computer", text)
        self.assertIn(" 1 | 2 | 3 ", text)
        self.assertIn("Scenario is ready for play mode.", text)

    def test_play_starter_is_visible_placeholder(self):
        output = io.StringIO()
        scenario = tictactoe_game.parse_scenario(tictactoe_game.DEFAULT_SCENARIO_TEXT)

        with redirect_stdout(output):
            result = tictactoe_play.run_tictactoe(scenario)

        self.assertEqual(result, 1)
        self.assertIn("TICTACTOE_PLAY=not-implemented", output.getvalue())

    def test_play_interface_check_confirms_runner(self):
        output = io.StringIO()

        with redirect_stdout(output):
            result = tictactoe_game.main(["--check-play-interface"])

        self.assertEqual(result, 0)
        self.assertIn("function=run_tictactoe", output.getvalue())
        self.assertIn("TICTACTOE_PLAY_IMPORT=pass", output.getvalue())

    def test_play_missing_runner_prints_clear_failure(self):
        output = io.StringIO()
        fake_module = types.ModuleType("dojo_app.tictactoe_play")

        with patch.dict(sys.modules, {"dojo_app.tictactoe_play": fake_module}):
            with redirect_stdout(output):
                result = tictactoe_game.main(["--play"])

        self.assertEqual(result, 1)
        text = output.getvalue()
        self.assertIn("TICTACTOE_PLAY=fail", text)
        self.assertIn("must define run_tictactoe", text)


if __name__ == "__main__":
    unittest.main()
