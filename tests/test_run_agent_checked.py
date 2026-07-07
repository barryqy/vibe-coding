from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RunAgentCheckedTests(unittest.TestCase):
    def test_observed_marker_is_saved_with_agent_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "agent.log"
            result = subprocess.run(
                [
                    "bash",
                    "scripts/run_agent_checked.sh",
                    "DEMO_ATTACK",
                    str(log_file),
                    "Launch is healthy",
                    "--",
                    "printf",
                    "Launch is healthy\\n",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                log_file.read_text(encoding="utf-8").splitlines(),
                ["Launch is healthy", "DEMO_ATTACK=observed"],
            )

    def test_capture_only_saves_output_without_streaming_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "agent.log"
            result = subprocess.run(
                [
                    "bash",
                    "scripts/run_agent_checked.sh",
                    "--capture-only",
                    "DEMO_ATTACK",
                    str(log_file),
                    "Launch is healthy",
                    "--",
                    "printf",
                    "Launch is healthy\\n",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("Launch is healthy", result.stdout)
            self.assertIn("DEMO_ATTACK=observed", result.stdout)
            self.assertEqual(
                log_file.read_text(encoding="utf-8").splitlines(),
                ["Launch is healthy", "DEMO_ATTACK=observed"],
            )

    def test_evidence_file_ignores_matching_text_in_agent_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "agent.log"
            evidence_file = Path(tmp) / "answer.txt"
            evidence_file.write_text("Credentials: [redacted]\n", encoding="utf-8")

            result = subprocess.run(
                [
                    "bash",
                    "scripts/run_agent_checked.sh",
                    "--evidence-file",
                    str(evidence_file),
                    "DEMO_ATTACK",
                    str(log_file),
                    "AKIAOPENCLAWLAB12345",
                    "--",
                    "printf",
                    "prompt contains AKIAOPENCLAWLAB12345\\n",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("DEMO_ATTACK=check-output", result.stdout)
            self.assertNotIn("DEMO_ATTACK=observed", result.stdout)


if __name__ == "__main__":
    unittest.main()
