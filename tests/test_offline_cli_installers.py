from __future__ import annotations

import hashlib
import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def write_checksum(archive: Path) -> None:
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(archive.suffix + ".sha256").write_text(
        f"{digest}  {archive.name}\n",
        encoding="utf-8",
    )


class OfflineCliInstallerTests(unittest.TestCase):
    def run_installer(self, script: str, home: Path, packages: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["VIBE_INSTALLER_DIR"] = str(packages)
        env["VIBE_INSTALLER_ARCH"] = "x86_64"
        env["PATH"] = f"{home}/.local/bin:{home}/.opencode/bin:/usr/bin:/bin"
        return subprocess.run(
            ["bash", f"scripts/{script}"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_codex_installs_from_preloaded_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            packages = base / "packages"
            payload = base / "codex-payload"
            packages.mkdir()
            executable(payload / "bin/codex", "#!/bin/sh\necho 'codex-cli 0.142.5'\n")
            executable(payload / "codex-path/rg", "#!/bin/sh\nexit 0\n")
            executable(payload / "codex-resources/bwrap", "#!/bin/sh\nexit 0\n")
            archive = packages / "codex-package-x86_64-unknown-linux-musl.tar.gz"
            with tarfile.open(archive, "w:gz") as bundle:
                for item in payload.rglob("*"):
                    bundle.add(item, arcname=item.relative_to(payload))
            write_checksum(archive)

            result = self.run_installer("install_codex_cli.sh", home, packages)
            rerun = self.run_installer("install_codex_cli.sh", home, packages)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Installing Codex CLI 0.142.5 from the lab image", result.stdout)
            self.assertIn("Installed: codex-cli 0.142.5", result.stdout)
            self.assertEqual(rerun.returncode, 0, rerun.stdout + rerun.stderr)
            self.assertIn("already installed", rerun.stdout)

    def test_opencode_installs_from_preloaded_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            packages = base / "packages"
            payload = base / "opencode-payload"
            packages.mkdir()
            executable(payload / "opencode", "#!/bin/sh\necho '1.0.190'\n")
            archive = packages / "opencode-linux-x64.tar.gz"
            with tarfile.open(archive, "w:gz") as bundle:
                bundle.add(payload / "opencode", arcname="opencode")
            write_checksum(archive)

            result = self.run_installer("install_opencode_cli.sh", home, packages)
            rerun = self.run_installer("install_opencode_cli.sh", home, packages)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Installing OpenCode 1.0.190 from the lab image", result.stdout)
            self.assertIn("Installed: OpenCode 1.0.190", result.stdout)
            self.assertEqual(rerun.returncode, 0, rerun.stdout + rerun.stderr)
            self.assertIn("already installed", rerun.stdout)

    def test_missing_preloaded_package_is_an_image_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            result = self.run_installer(
                "install_opencode_cli.sh",
                base / "home",
                base / "missing",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("lab image is missing the preloaded package", result.stderr)


if __name__ == "__main__":
    unittest.main()
