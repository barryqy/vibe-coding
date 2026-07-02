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

    def test_tty_renders_colored_confetti_frame(self):
        output = FakeTty()
        terminal_size = os.terminal_size((40, 12))

        with (
            patch.dict(os.environ, {"DOJO_COLOR": "1", "TERM": "xterm-256color"}, clear=False),
            patch.object(cli_confetti.shutil, "get_terminal_size", return_value=terminal_size),
        ):
            cli_confetti.celebrate(output, duration=0, seed=7)

        text = output.getvalue()
        self.assertIn(cli_confetti.CLEAR_SCREEN, text)
        self.assertIn(cli_confetti.SOLVED_TEXT, text)
        self.assertIn("\033[", text)


if __name__ == "__main__":
    unittest.main()
