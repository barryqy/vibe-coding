from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dojo_app import maze_game


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPT = ROOT / "skills" / "mazemaker" / "scripts" / "build_maze.py"


def load_skill_module():
    spec = importlib.util.spec_from_file_location("mazemaker_build_maze", SKILL_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load MazeMaker skill script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MazeMakerSkillTests(unittest.TestCase):
    def test_build_maze_artifact_writes_checked_maze(self):
        skill = load_skill_module()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            rel_path = Path(tmp).relative_to(ROOT) / "maze.txt"
            text = skill.build_maze_artifact(str(rel_path), seed="lab-42", order="SWEN")
            maze = maze_game.load_maze(str(ROOT / rel_path))

        self.assertIn("MAZEMAKER_SKILL=ready", text)
        self.assertIn("skill=mazemaker", text)
        self.assertIn("script=build_maze.py", text)
        self.assertIn("solvable=yes", text)
        self.assertIn("MAZEMAKER_SKILL=pass", text)
        self.assertTrue(maze_game.trusted_maze_lines(maze))

    def test_build_maze_artifact_rejects_bad_order(self):
        skill = load_skill_module()
        with self.assertRaises(ValueError):
            skill.build_maze_artifact(".lab-state/codex-output/maze.txt", seed="lab-42", order="NNNN")

    def test_build_maze_artifact_keeps_output_inside_repo(self):
        skill = load_skill_module()
        with self.assertRaises(ValueError):
            skill.build_maze_artifact("../maze.txt", seed="lab-42", order="NESW")

    def test_skill_script_cli_writes_checked_maze(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            rel_path = Path(tmp).relative_to(ROOT) / "maze.txt"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_SCRIPT),
                    "--maze-file",
                    str(rel_path),
                    "--seed",
                    "lab-42",
                    "--order",
                    "NESW",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            maze = maze_game.load_maze(str(ROOT / rel_path))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("MAZEMAKER_SKILL=pass", result.stdout)
        self.assertTrue(maze_game.trusted_maze_lines(maze))


if __name__ == "__main__":
    unittest.main()
