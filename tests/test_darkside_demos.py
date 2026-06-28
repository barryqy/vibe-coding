from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DarksideDemoTests(unittest.TestCase):
    def run_demo(self, script: str) -> str:
        result = subprocess.run(
            [sys.executable, f"scripts/{script}"],
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
        self.assertIn("OOPS_MCP_RCE=local-file-written", output)
        self.assertIn("aws_access_key_id = AKIAOPENCLAWLAB12345", output)
        self.assertTrue((ROOT / ".lab-state/darkside/mcp-rce-demo.txt").exists())


if __name__ == "__main__":
    unittest.main()
