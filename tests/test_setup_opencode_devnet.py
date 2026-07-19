from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import setup_opencode_devnet


class SetupOpenCodeDevnetTests(unittest.TestCase):
    def test_generated_config_has_bounded_maze_agent(self):
        env = {
            "LLM_BASE_URL": "https://model.example/v1",
            "LLM_API_KEY": "test-key",
            "LLM_MODEL": "gpt-5-nano",
            "LLM_MAZE_MODEL": "gpt-5-cache",
            "MAZE_RETRY_MODEL": "gpt-5-nano-cache",
        }
        state_dir = setup_opencode_devnet.ROOT / ".lab-state"
        state_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=state_dir) as tmp:
            output_path = Path(tmp) / "opencode-devnet.json"
            with (
                patch.dict(os.environ, env, clear=True),
                patch.object(setup_opencode_devnet, "OUT", output_path),
                patch.object(setup_opencode_devnet, "install_lab_commands"),
                redirect_stdout(io.StringIO()),
            ):
                result = setup_opencode_devnet.main()

            config = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(
            set(config["provider"]["devnet"]["models"]),
            {"gpt-5-nano", "gpt-5-cache", "gpt-5-nano-cache"},
        )
        agent = config["agent"]["maze-editor"]
        self.assertEqual(agent["mode"], "primary")
        self.assertEqual(agent["maxSteps"], 16)
        self.assertIn("Never rerun an unchanged failing check", agent["prompt"])
        self.assertIn("no more than two corrective edits", agent["prompt"])
        self.assertIn("Return MAZE_EDIT_OK only", agent["prompt"])
        self.assertEqual(agent["permission"]["bash"]["*"], "deny")
        self.assertEqual(
            agent["permission"]["bash"]["python3 scripts/verify_maze_movement.py"],
            "allow",
        )
        self.assertEqual(
            agent["permission"]["bash"][
                "python3 -m py_compile dojo_app/maze_game.py dojo_app/maze_play.py"
            ],
            "allow",
        )


if __name__ == "__main__":
    unittest.main()
