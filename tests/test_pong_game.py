from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from dojo_app import pong_game


class PongGameTests(unittest.TestCase):
    def test_frame_has_paddles_ball_score_and_lesson(self):
        frame = pong_game.draw_frame(pong_game.GameState(), 1, "stay")

        self.assertIn("+--------------------------------+", frame)
        self.assertIn("o", frame)
        self.assertIn("you=0 cpu=0", frame)
        self.assertIn("no-secrets-in-games", frame)

    def test_human_move_changes_paddle_position(self):
        state = pong_game.GameState(human_y=3)
        moved = pong_game.next_state(state, "w")

        self.assertEqual(moved.human_y, 2)

    def test_cpu_tracks_ball(self):
        state = pong_game.GameState(cpu_y=3, ball_y=8)
        moved = pong_game.next_state(state, "stay")

        self.assertEqual(moved.cpu_y, 4)

    def test_parse_moves_defaults_to_stay(self):
        self.assertEqual(pong_game.parse_moves(""), ["stay"])

    def test_interactive_match_uses_prompted_moves(self):
        output = io.StringIO()

        with patch("builtins.input", side_effect=["s", "q"]), redirect_stdout(output):
            pong_game.run_interactive_match(4)

        text = output.getvalue()
        self.assertIn("mode=interactive-human-vs-cpu", text)
        self.assertIn("Turn 1 move", text)
        self.assertIn("FRAME=1", text)
        self.assertIn("move=s", text)
        self.assertIn("BARRYPONG=pass", text)


if __name__ == "__main__":
    unittest.main()
