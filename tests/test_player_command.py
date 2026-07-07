from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "player"


class PlayerCommandTests(unittest.TestCase):
    def test_player_prints_the_assigned_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            bin_dir = home / ".local" / "bin"
            bin_dir.mkdir(parents=True)
            fake_dojo = bin_dir / "dojo"
            fake_dojo.write_text(
                '#!/bin/sh\n[ "$1" = player ] && printf "%s\\n" BrightRedQuantumFalcon\n',
                encoding="utf-8",
            )
            fake_dojo.chmod(0o755)

            env = os.environ.copy()
            env["HOME"] = str(home)
            result = subprocess.run(
                ["sh", str(SCRIPT)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "BrightRedQuantumFalcon\n")


if __name__ == "__main__":
    unittest.main()
