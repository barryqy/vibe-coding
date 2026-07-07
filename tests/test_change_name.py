from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "change-name.py"


class ChangeNameTests(unittest.TestCase):
    def test_valid_name_is_sent_to_dojo(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            args_file = tmp_path / "args.txt"
            fake_dojo = tmp_path / "dojo"
            fake_dojo.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$*" >"$DOJO_ARGS_FILE"\n',
                encoding="utf-8",
            )
            fake_dojo.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp_path}{os.pathsep}{env.get('PATH', '')}"
            env["DOJO_ARGS_FILE"] = str(args_file)

            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input="KindPanda\n",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(args_file.read_text(encoding="utf-8"), "join --name KindPanda\n")

    def test_invalid_name_never_calls_dojo(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="not a valid name\n",
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("3-32 letters", result.stdout)


if __name__ == "__main__":
    unittest.main()
