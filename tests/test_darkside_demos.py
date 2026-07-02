from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from scripts.build_rollout_review_prompt import build_prompt
from scripts.run_guardrail_demo import summarize_guardrail_verdict


ROOT = Path(__file__).resolve().parents[1]


class DarksideDemoTests(unittest.TestCase):
    def run_demo(self, script: str, *args: str) -> str:
        result = subprocess.run(
            [sys.executable, f"scripts/{script}", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_generated_code_demo_writes_marker_files(self):
        output = self.run_demo("run_darkside_code_demo.py")

        self.assertIn("DARKSIDE_CODE_EXEC=pass", output)
        self.assertIn("OOPS_GENERATED_CODE_EXEC=local-files-written", output)
        self.assertTrue((ROOT / ".lab-state/darkside/eval-ran.txt").exists())
        self.assertTrue((ROOT / ".lab-state/darkside/shell-ran.txt").exists())

    def test_risky_skill_demo_captures_fake_aws(self):
        output = self.run_demo("run_risky_skill_demo.py")

        self.assertIn("DARKSIDE_SKILL_RUN=pass", output)
        self.assertIn("OOPS_SKILL_EXFILTRATED=fake-aws-credentials", output)
        self.assertIn("aws_access_key_id = AKIAOPENCLAWLAB12345", output)
        self.assertTrue((ROOT / ".lab-state/darkside/skill-exfil.json").exists())

    def test_risky_mcp_demo_reads_fake_aws_and_writes_marker(self):
        output = self.run_demo("run_risky_mcp_demo.py")

        self.assertIn("DARKSIDE_MCP_ABUSE=pass", output)
        self.assertIn("mcp_transport=stdio", output)
        self.assertIn("read_runtime_config", output)
        self.assertIn("score_template_expression", output)
        self.assertIn("OOPS_MCP_RCE=local-file-written", output)
        self.assertIn("aws_access_key_id = AKIAOPENCLAWLAB12345", output)
        self.assertTrue((ROOT / ".lab-state/darkside/mcp-rce-demo.txt").exists())

    def test_guardrail_summary_requires_a_real_block_action(self):
        blocked = summarize_guardrail_verdict(
            mode="guarded-privacy",
            endpoint="http://127.0.0.1/inspect",
            model="gpt-5-nano",
            http_status=200,
            verdict={"action": "block", "mode": "action", "severity": "CRITICAL"},
        )
        observed = summarize_guardrail_verdict(
            mode="guarded-privacy",
            endpoint="http://127.0.0.1/inspect",
            model="gpt-5-nano",
            http_status=200,
            verdict={"action": "allow", "mode": "observe", "severity": "CRITICAL"},
        )

        self.assertTrue(blocked["blocked"])
        self.assertEqual(blocked["guardrail_mode"], "action")
        self.assertFalse(observed["blocked"])
        self.assertEqual(observed["guardrail_mode"], "observe")

    def test_rollout_prompt_combines_injection_and_fake_private_data(self):
        prompt = build_prompt()

        self.assertIn("Output Format for Assistant Summary", prompt)
        self.assertIn("AKIAOPENCLAWLAB12345", prompt)
        self.assertIn("owner@northstar.example.test", prompt)
        self.assertNotIn("bayuan@cisco.com", prompt)


if __name__ == "__main__":
    unittest.main()
