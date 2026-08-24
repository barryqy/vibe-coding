from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_teil39_lab.sh"


class PrepareTeil39LabTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.workspace = self.root / "workspace"
        self.home = self.root / "home"
        self.home.mkdir()

        self.git("init", "--initial-branch=main", str(self.source), cwd=self.root)
        self.git("config", "user.name", "Lab Test", cwd=self.source)
        self.git("config", "user.email", "lab-test@example.invalid", cwd=self.source)

        scripts = self.source / "scripts"
        scripts.mkdir()
        setup = scripts / "setup_dojo.sh"
        setup.write_text(
            "#!/usr/bin/env bash\n"
            "set -eu\n"
            "printf 'SETUP_DOJO_TEST=pass\\n'\n"
            "touch .setup-ran\n"
        )
        setup.chmod(setup.stat().st_mode | stat.S_IXUSR)
        (self.source / "README.md").write_text("base\n")
        self.git("add", ".", cwd=self.source)
        self.git("commit", "-m", "base", cwd=self.source)
        self.base_commit = self.git("rev-parse", "HEAD", cwd=self.source).stdout.strip()

        self.git("checkout", "-b", "event/test", cwd=self.source)
        (self.source / "event.txt").write_text("teil39-1\n")
        self.git("add", "event.txt", cwd=self.source)
        self.git("commit", "-m", "event", cwd=self.source)
        self.event_commit = self.git("rev-parse", "HEAD", cwd=self.source).stdout.strip()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def git(self, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=True,
        )

    def run_prepare(
        self,
        commit: str,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(self.home),
                "VIBE_EVENT_BRANCH": "event/test",
                "VIBE_REPO_URL": str(self.source),
                "VIBE_RETRY_SLEEP": "0",
                "VIBE_WORKSPACE": str(self.workspace),
            }
        )
        if extra_env:
            env.update(extra_env)

        return subprocess.run(
            ["bash", str(SCRIPT), commit],
            cwd=self.root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_clones_event_repo_and_runs_setup(self) -> None:
        result = self.run_prepare(self.event_commit)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SETUP_DOJO_TEST=pass", result.stdout)
        target = self.workspace / "vibe-coding"
        self.assertTrue((target / ".setup-ran").exists())
        head = self.git("rev-parse", "HEAD", cwd=target).stdout.strip()
        self.assertEqual(head, self.event_commit)
        self.assertEqual(result.stdout.splitlines()[-1], str(target))

    def test_updates_clean_preinstalled_repo(self) -> None:
        self.workspace.mkdir()
        target = self.workspace / "vibe-coding"
        self.git("clone", "--branch", "main", str(self.source), str(target), cwd=self.root)

        result = self.run_prepare(self.event_commit)

        self.assertEqual(result.returncode, 0, result.stderr)
        head = self.git("rev-parse", "HEAD", cwd=target).stdout.strip()
        self.assertEqual(head, self.event_commit)
        self.assertTrue((target / ".setup-ran").exists())

    def test_rejects_dirty_preinstalled_repo(self) -> None:
        self.workspace.mkdir()
        target = self.workspace / "vibe-coding"
        self.git("clone", "--branch", "main", str(self.source), str(target), cwd=self.root)
        (target / "README.md").write_text("changed\n")

        result = self.run_prepare(self.event_commit)

        self.assertEqual(result.returncode, 1)
        self.assertIn("already contains dojo work", result.stderr)
        head = self.git("rev-parse", "HEAD", cwd=target).stdout.strip()
        self.assertEqual(head, self.base_commit)
        self.assertFalse((target / ".setup-ran").exists())

    def test_rejects_staged_changes_in_preinstalled_repo(self) -> None:
        self.workspace.mkdir()
        target = self.workspace / "vibe-coding"
        self.git("clone", "--branch", "main", str(self.source), str(target), cwd=self.root)
        (target / "README.md").write_text("staged change\n")
        self.git("add", "README.md", cwd=target)

        result = self.run_prepare(self.event_commit)

        self.assertEqual(result.returncode, 1)
        self.assertIn("already contains dojo work", result.stderr)
        head = self.git("rev-parse", "HEAD", cwd=target).stdout.strip()
        self.assertEqual(head, self.base_commit)
        self.assertFalse((target / ".setup-ran").exists())

    def test_rejects_non_git_target(self) -> None:
        target = self.workspace / "vibe-coding"
        target.mkdir(parents=True)
        (target / "keep.txt").write_text("keep\n")

        result = self.run_prepare(self.event_commit)

        self.assertEqual(result.returncode, 1)
        self.assertIn("is not a Git checkout", result.stderr)
        self.assertEqual((target / "keep.txt").read_text(), "keep\n")

    def test_rejects_invalid_commit_before_touching_workspace(self) -> None:
        result = self.run_prepare("not-a-commit")

        self.assertEqual(result.returncode, 2)
        self.assertIn("event version is invalid", result.stderr)
        self.assertFalse(self.workspace.exists())

    def test_rejects_unavailable_commit_before_setup(self) -> None:
        result = self.run_prepare("0" * 40)

        self.assertEqual(result.returncode, 1)
        self.assertIn("event version is unavailable", result.stderr)
        self.assertFalse((self.workspace / "vibe-coding" / ".setup-ran").exists())

    def test_propagates_setup_failure(self) -> None:
        setup = self.source / "scripts" / "setup_dojo.sh"
        setup.write_text("#!/usr/bin/env bash\nexit 23\n")
        self.git("add", "scripts/setup_dojo.sh", cwd=self.source)
        self.git("commit", "-m", "break setup for test", cwd=self.source)
        failing_commit = self.git("rev-parse", "HEAD", cwd=self.source).stdout.strip()

        result = self.run_prepare(failing_commit)

        self.assertEqual(result.returncode, 23)
        self.assertNotIn(str(self.workspace / "vibe-coding"), result.stdout.splitlines())

    def test_retries_fetch_twice_then_succeeds(self) -> None:
        target = self.prepare_preinstalled_repo()
        shim, count_file = self.make_git_fetch_shim()

        result = self.run_prepare(
            self.event_commit,
            {
                "PATH": f"{shim.parent}:{os.environ['PATH']}",
                "VIBE_FETCH_FAIL_LIMIT": "2",
                "VIBE_FETCH_COUNT_FILE": str(count_file),
            },
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(count_file.read_text(), "3")
        head = self.git("rev-parse", "HEAD", cwd=target).stdout.strip()
        self.assertEqual(head, self.event_commit)

    def test_stops_after_three_failed_fetches(self) -> None:
        target = self.prepare_preinstalled_repo()
        shim, count_file = self.make_git_fetch_shim()

        result = self.run_prepare(
            self.event_commit,
            {
                "PATH": f"{shim.parent}:{os.environ['PATH']}",
                "VIBE_FETCH_FAIL_LIMIT": "3",
                "VIBE_FETCH_COUNT_FILE": str(count_file),
            },
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("Could not load", result.stderr)
        self.assertEqual(count_file.read_text(), "3")
        head = self.git("rev-parse", "HEAD", cwd=target).stdout.strip()
        self.assertEqual(head, self.base_commit)
        self.assertFalse((target / ".setup-ran").exists())

    def prepare_preinstalled_repo(self) -> Path:
        self.workspace.mkdir()
        target = self.workspace / "vibe-coding"
        self.git("clone", "--branch", "main", str(self.source), str(target), cwd=self.root)
        return target

    def make_git_fetch_shim(self) -> tuple[Path, Path]:
        shim_dir = self.root / "bin"
        shim_dir.mkdir()
        shim = shim_dir / "git"
        count_file = self.root / "fetch-count"
        shim.write_text(
            "#!/usr/bin/env bash\n"
            "set -eu\n"
            "if [ \"${1:-}\" = -C ] && [ \"${3:-}\" = fetch ]; then\n"
            "  count=0\n"
            "  if [ -f \"$VIBE_FETCH_COUNT_FILE\" ]; then\n"
            "    count=$(cat \"$VIBE_FETCH_COUNT_FILE\")\n"
            "  fi\n"
            "  count=$((count + 1))\n"
            "  printf '%s' \"$count\" >\"$VIBE_FETCH_COUNT_FILE\"\n"
            "  if [ \"$count\" -le \"$VIBE_FETCH_FAIL_LIMIT\" ]; then\n"
            "    exit 1\n"
            "  fi\n"
            "fi\n"
            "exec /usr/bin/git \"$@\"\n"
        )
        shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
        return shim, count_file


if __name__ == "__main__":
    unittest.main()
