#!/usr/bin/env python3
from __future__ import annotations

import compileall
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(name: str, cmd: list[str]) -> bool:
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode == 0:
        print(f"[OK] {name}")
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines()[-4:]:
                print(f"  {line}")
        return True

    print(f"[FAIL] {name}")
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    return False


def main() -> int:
    print("== Vibe Coding Quality Gate ==")

    compiled = compileall.compile_dir(ROOT / "dojo_app", quiet=1)
    compiled = compileall.compile_dir(ROOT / "scripts", quiet=1) and compiled
    if compiled:
        print("[OK] Python files compile")
    else:
        print("[FAIL] Python files compile")
        print("QUALITY_GATE=fail")
        return 1

    checks = [
        ("Unit tests passed", [sys.executable, "-m", "unittest", "discover", "-s", "tests"]),
        ("Security review passed", [sys.executable, "scripts/security_review.py", "dojo_app", "scripts"]),
        ("Agent consistency passed", [sys.executable, "scripts/consistency_check.py"]),
    ]

    for name, cmd in checks:
        if not run_step(name, cmd):
            print("QUALITY_GATE=fail")
            return 1

    print("QUALITY_GATE=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

