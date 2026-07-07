from __future__ import annotations

import io
import os
import unittest
from unittest.mock import patch

from dojo_app import cli_confetti


class FakeTty(io.StringIO):
    def isatty(self) -> bool:
        return True


class CliConfettiTests(unittest.TestCase):
    def test_non_tty_uses_static_celebration(self):
        output = io.StringIO()

        cli_confetti.celebrate(output)

        self.assertEqual(output.getvalue(), "* + *  MAZE SOLVED!  * + *\n")

    def test_narrow_tty_uses_full_height_and_restores_output(self):
        output = FakeTty()
        terminal_size = os.terminal_size((20, 8))

        with (
            patch.dict(os.environ, {"DOJO_COLOR": "1", "TERM": "xterm-256color"}, clear=False),
            patch.object(cli_confetti.shutil, "get_terminal_size", return_value=terminal_size),
        ):
            cli_confetti.celebrate(output, duration=0, seed=7)

        text = output.getvalue()
        self.assertNotIn("\033[2J", text)
        self.assertNotIn("\033[H", text)
        self.assertIn(cli_confetti.ALT_SCREEN_ON, text)
        self.assertIn(cli_confetti.CURSOR_HOME, text)
        self.assertIn(cli_confetti.ALT_SCREEN_OFF, text)
        self.assertIn(cli_confetti.SOLVED_TEXT, text)
        self.assertIn("\033[", text)

    def test_default_animation_duration_is_four_times_the_original(self):
        self.assertEqual(cli_confetti.DEFAULT_DURATION, 5.6)

    def test_frame_fits_available_rows_in_a_narrow_terminal(self):
        frame = cli_confetti._draw_frame(19, 6, [], use_color=False)
        lines = frame.split("\r\n")

        self.assertEqual(len(lines), 6)
        self.assertTrue(all(len(line) == 19 for line in lines))


if __name__ == "__main__":
    unittest.main()
