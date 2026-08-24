from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from configure_dojo_event import (  # noqa: E402
    DEFAULT_EVENT,
    RUNTIME_CONFIG,
    configure_event,
    event_from_args,
)


class ConfigureDojoEventTests(unittest.TestCase):
    def test_no_argument_keeps_self_paced_setup(self):
        self.assertEqual(event_from_args([]), DEFAULT_EVENT)

    def test_explicit_event_is_written_to_runtime_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)

            event_file = configure_event(repo_root, event_from_args(["teil39-1"]))

            self.assertEqual(event_file, repo_root / RUNTIME_CONFIG)
            self.assertEqual(event_file.read_text(encoding="utf-8"), 'event = "teil39-1"\n')

    def test_rerun_replaces_the_runtime_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)

            configure_event(repo_root, "self-paced")
            event_file = configure_event(repo_root, "teil39-1")

            self.assertEqual(event_file.read_text(encoding="utf-8"), 'event = "teil39-1"\n')

    def test_invalid_event_codes_are_rejected(self):
        invalid_values = ["", "TEIL39-1", "teil39 1", "teil39_1", "x" * 41, "teil39-1\nother"]

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    event_from_args([value])

    def test_extra_argument_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "usage"):
            event_from_args(["teil39-1", "unexpected"])

    def test_invalid_event_does_not_create_runtime_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)

            with self.assertRaises(ValueError):
                configure_event(repo_root, "TEIL39-1")

            self.assertFalse((repo_root / RUNTIME_CONFIG).exists())


if __name__ == "__main__":
    unittest.main()
