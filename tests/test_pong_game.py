from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
