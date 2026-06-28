from __future__ import annotations

import io
import os
import unittest
from unittest.mock import patch

from dojo_app import lab_output


class FakeTty(io.StringIO):
    def isatty(self) -> bool:
        return True


class LabOutputTests(unittest.TestCase):
    def test_plain_output_when_not_tty(self):
        stream = io.StringIO()
        self.assertEqual(lab_output.format_status("MAZE_CHECK=pass", stream), "MAZE_CHECK=pass")

    def test_force_color_for_pass_marker(self):
        stream = FakeTty()
        with patch.dict(os.environ, {"DOJO_COLOR": "1"}, clear=False):
            text = lab_output.format_status("MAZE_CHECK=pass", stream)
        self.assertIn("\033[32m", text)
        self.assertIn("MAZE_CHECK=pass", text)

    def test_fail_marker_is_red(self):
        stream = FakeTty()
        with patch.dict(os.environ, {"DOJO_COLOR": "1"}, clear=False):
            text = lab_output.format_status("SECURITY_REVIEW=fail", stream)
        self.assertIn("\033[31m", text)
        self.assertIn("SECURITY_REVIEW=fail", text)

    def test_no_color_env_wins_without_force(self):
        stream = FakeTty()
        with patch.dict(os.environ, {"NO_COLOR": "1", "DOJO_COLOR": "0"}, clear=False):
            text = lab_output.format_status("MODEL_USAGE=ok", stream)
        self.assertEqual(text, "MODEL_USAGE=ok")


if __name__ == "__main__":
    unittest.main()
