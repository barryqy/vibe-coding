from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


class DefenseClawInstallerOutputTests(unittest.TestCase):
    def run_installer(self, plugin_state: str) -> subprocess.CompletedProcess[str]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)

        repo = Path(tmp.name) / "repo"
        home = Path(tmp.name) / "home"
        script = repo / "scripts/install_defenseclaw_cli.sh"
        script.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/install_defenseclaw_cli.sh", script)

        state = repo / ".lab-state/defenseclaw"
        executable(state / ".venv/bin/python", "#!/bin/sh\nexit 0\n")
        executable(
            state / ".venv/bin/defenseclaw",
            textwrap.dedent(
                """\
                #!/bin/sh
                printf '%s\n' \
                  '' \
                  '  DefenseClaw versions' \
                  '' \
                  '  COMPONENT  VERSION          STATUS   ORIGIN' \
                  '  cli        0.8.0            ok       defenseclaw (python)' \
                  '  gateway    0.8.0            ok       /tmp/defenseclaw-gateway'
                case "$FAKE_PLUGIN_STATE" in
                  installed)
                    printf '%s\n' '  plugin     0.8.0            ok       ~/.openclaw/extensions/defenseclaw'
                    ;;
                  error)
                    printf '%s\n' '  plugin     (error)          error    ~/.openclaw/extensions/defenseclaw'
                    ;;
                  *)
                    printf '%s\n' '  plugin     (not installed)  missing  ~/.openclaw/extensions/defenseclaw'
                    ;;
                esac
                printf '%s\n' '' '  All components in sync.' ''
                printf '%s\n' 'version diagnostic stays visible' >&2
                """
            ),
        )
        executable(
            state / "bin/defenseclaw-gateway",
            "#!/bin/sh\necho 'defenseclaw-gateway version 0.8.0'\n",
        )
        executable(home / ".local/bin/uv", "#!/bin/sh\nexit 0\n")
        executable(home / ".local/bin/uvx", "#!/bin/sh\nexit 0\n")
        (state / "home").mkdir(parents=True)
        (state / "home/config.yaml").touch()
        (state / "home/audit.db").touch()

        env = os.environ.copy()
        env["DEFENSECLAW_HOME"] = str(state / "home")
        env["FAKE_PLUGIN_STATE"] = plugin_state
        env["HOME"] = str(home)
        env["PATH"] = f"{home}/.local/bin:/usr/bin:/bin"
        return subprocess.run(
            ["bash", str(script)],
            cwd=repo,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_hides_missing_optional_openclaw_plugin(self):
        result = self.run_installer("missing")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("cli        0.8.0", result.stdout)
        self.assertIn("gateway    0.8.0", result.stdout)
        self.assertNotIn("plugin     (not installed)", result.stdout)
        self.assertIn("version diagnostic stays visible", result.stderr)

    def test_keeps_installed_plugin_status(self):
        result = self.run_installer("installed")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("plugin     0.8.0", result.stdout)

    def test_keeps_plugin_errors_visible(self):
        result = self.run_installer("error")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("plugin     (error)", result.stdout)


if __name__ == "__main__":
    unittest.main()
