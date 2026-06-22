#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LOCAL_HOME = ROOT / ".lab-state" / "defenseclaw" / "home"
LOCAL_CLI = ROOT / ".lab-state" / "defenseclaw" / ".venv" / "bin" / "defenseclaw"
INSTALLER = ROOT / "scripts" / "install_defenseclaw_cli.sh"
PINNED_VERSION = os.getenv("DEFENSECLAW_VERSION", "0.5.0")
BAD_SKILL = ROOT / "samples" / "skills" / "snake-score-booster"
CLEAN_SKILL = ROOT / "samples" / "skills" / "snake-game-coach"
RISKY_LEVELS = {"CRITICAL", "HIGH"}


def run(cmd: list[str], timeout: int = 90) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.setdefault("NO_COLOR", "1")
    env.setdefault("CLICOLOR", "0")
    env.setdefault("DEFENSECLAW_HOME", str(LOCAL_HOME))
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=env,
    )


def ensure_lab_home(cli: str) -> None:
    LOCAL_HOME.mkdir(parents=True, exist_ok=True)
    if (LOCAL_HOME / "config.yaml").exists() and (LOCAL_HOME / "audit.db").exists():
        return

    result = run(
        [
            cli,
            "init",
            "--skip-install",
            "--non-interactive",
            "--yes",
            "--connector",
            "codex",
            "--profile",
            "observe",
            "--no-start-gateway",
            "--no-verify",
        ],
        timeout=60,
    )
    if result.returncode != 0:
        print(result.stdout.rstrip())
        print(result.stderr.rstrip(), file=sys.stderr)
        raise SystemExit(result.returncode)


def ensure_defenseclaw() -> str:
    if LOCAL_CLI.exists() and cli_version_ok(str(LOCAL_CLI)):
        cli = str(LOCAL_CLI)
        ensure_lab_home(cli)
        return cli

    found = shutil.which("defenseclaw")
    if found and cli_version_ok(found):
        ensure_lab_home(found)
        return found

    result = run([str(INSTALLER)], timeout=180)
    if result.returncode != 0:
        print(result.stdout.rstrip())
        print(result.stderr.rstrip(), file=sys.stderr)
        raise SystemExit(result.returncode)

    if LOCAL_CLI.exists() and cli_version_ok(str(LOCAL_CLI)):
        cli = str(LOCAL_CLI)
        ensure_lab_home(cli)
        return cli

    found = shutil.which("defenseclaw")
    if found and cli_version_ok(found):
        ensure_lab_home(found)
        return found

    print("DEFENSECLAW_INSTALL=failed", file=sys.stderr)
    raise SystemExit(1)


def cli_version_ok(cli: str) -> bool:
    result = run([cli, "--version"], timeout=15)
    return result.returncode == 0 and f"version {PINNED_VERSION}" in result.stdout


def parse_json(text: str) -> dict:
    start = text.find("{")
    if start < 0:
        raise ValueError("DefenseClaw did not return JSON")
    decoder = json.JSONDecoder()
    parsed, _ = decoder.raw_decode(text[start:])
    if not isinstance(parsed, dict):
        raise ValueError("DefenseClaw JSON result was not an object")
    return parsed


def scan_skill(cli: str, name: str, path: Path) -> dict:
    result = run([cli, "skill", "scan", name, "--path", str(path), "--json"])
    combined = "\n".join(part for part in [result.stdout, result.stderr] if part)

    if result.returncode != 0:
        print(combined.rstrip())
        raise SystemExit(result.returncode)

    try:
        return parse_json(combined)
    except json.JSONDecodeError as exc:
        print(combined.rstrip())
        print(f"DEFENSECLAW_JSON=invalid: {exc}", file=sys.stderr)
        raise SystemExit(1)


def severities(result: dict) -> list[str]:
    items = result.get("findings", [])
    return [str(item.get("severity", "")).upper() for item in items if isinstance(item, dict)]


def main() -> int:
    cli = ensure_defenseclaw()
    print(f"DEFENSECLAW_CLI={cli}")
    print(f"DEFENSECLAW_HOME={os.environ.get('DEFENSECLAW_HOME', str(LOCAL_HOME))}")

    bad = scan_skill(cli, "snake-score-booster", BAD_SKILL)
    clean = scan_skill(cli, "snake-game-coach", CLEAN_SKILL)

    bad_levels = severities(bad)
    clean_levels = severities(clean)

    if not any(level in RISKY_LEVELS for level in bad_levels):
        print("DEFENSECLAW_BAD_SKILL=missed")
        print(f"bad_skill_severities={','.join(bad_levels) or 'none'}")
        return 1

    if clean_levels:
        print("DEFENSECLAW_CLEAN_SKILL=flagged")
        print(f"clean_skill_severities={','.join(clean_levels)}")
        return 1

    print("DEFENSECLAW_BAD_SKILL=blocked")
    print(f"bad_skill_findings={len(bad.get('findings', []))}")
    print("DEFENSECLAW_CLEAN_SKILL=clean")
    print("DEFENSECLAW_MINI=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
