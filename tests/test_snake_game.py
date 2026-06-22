from __future__ import annotations

import unittest

from dojo_app import snake_game


class SnakeGameTests(unittest.TestCase):
    def test_frame_has_border_snake_food_and_lesson(self):
        frame = snake_game.draw_frame(0)

        self.assertIn("+------------------+", frame)
        self.assertIn("oo@", frame)
        self.assertIn("*", frame)
        self.assertIn("do-not-hide-keys-in-games", frame)

    def test_snake_moves_right(self):
        first = snake_game.move_snake(0)[0]
        second = snake_game.move_snake(1)[0]

        self.assertEqual(second[0], first[0] + 1)
        self.assertEqual(second[1], first[1])


if __name__ == "__main__":
    unittest.main()
