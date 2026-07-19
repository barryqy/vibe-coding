from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RunAgentCheckedTests(unittest.TestCase):
    def run_case(self, output: str, returncode: int = 0):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        log_file = Path(tmp.name) / "agent.log"
        command = f"printf '%s\\n' \"$1\"; exit {returncode}"
        result = subprocess.run(
            [
                "bash",
                "scripts/run_agent_checked.sh",
                "--capture-only",
                "DEMO_ATTACK",
                str(log_file),
                "never-match",
                "--",
                "bash",
                "-c",
                command,
                "_",
                output,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        return result, log_file.read_text(encoding="utf-8")

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

    def test_budget_rate_limit_provider_and_timeout_are_distinct(self):
        cases = [
            ("budget exceeded", 0, "model-budget-exhausted", 0),
            (
                'HTTP 429: {"type":"provider_error","upstream_provider":"azure",'
                '"upstream_status":429,"message":"rate limit"}',
                1,
                "provider-error",
                1,
            ),
            ("HTTP 429: Too Many Requests", 1, "rate-limited", 0),
            ("rate_limit_exceeded", 1, "rate-limited", 0),
            ("HTTP 502: upstream unavailable", 1, "provider-error", 1),
            ("ProviderModelNotFound", 0, "provider-error", 1),
            ("provider_invalid_response", 1, "provider-error", 1),
            ("upstream_invalid_response", 1, "provider-error", 1),
            ("provider_connection_error", 1, "provider-error", 1),
            ("upstream_connection_error", 1, "provider-error", 1),
            ("configuration_error", 1, "provider-error", 1),
            ("upstream_not_configured", 1, "provider-error", 1),
            (
                'HTTP 504: {"type":"provider_timeout_error","code":"upstream_timeout"}',
                1,
                "agent-timeout",
                0,
            ),
            ("still working", 124, "agent-timeout", 0),
        ]

        for output, command_rc, expected, expected_rc in cases:
            with self.subTest(output=output):
                result, log = self.run_case(output, command_rc)

                self.assertEqual(result.returncode, expected_rc, result.stdout + result.stderr)
                self.assertIn(f"DEMO_ATTACK={expected}", result.stdout)
                self.assertIn(f"DEMO_ATTACK={expected}", log)


if __name__ == "__main__":
    unittest.main()
