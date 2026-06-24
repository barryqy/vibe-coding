#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KB_FILES = [
    Path(".second-brain/RESOLVER.md"),
    Path(".second-brain/schema.md"),
    Path(".second-brain/projects/vibe-coding-dojo.md"),
    Path(".second-brain/sessions/current-agent-handoff.md"),
]
PONG = ROOT / "dojo_app" / "pong_game.py"
PONG_TEST = ROOT / "tests" / "test_pong_game.py"
OUT = ROOT / ".lab-state" / "opencode-output" / "kb-pong-feature.jsonl"
PROMPT = "Read the second brain and reply with the next action only."


def run(cmd: list[str], timeout: int = 60, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout, check=False, env=env)


def ensure_ready() -> None:
    missing = [str(path) for path in KB_FILES if not (ROOT / path).exists()]
    if missing:
        print("OPENCODE_KB=missing")
        for path in missing:
            print(f"missing={path}")
        raise SystemExit(1)

    if not (ROOT / ".lab-state" / "opencode-devnet.json").exists():
        setup = run([sys.executable, "scripts/setup_opencode_devnet.py"], timeout=20)
        print(setup.stdout, end="")
        if setup.returncode != 0:
            print(setup.stderr, end="", file=sys.stderr)
            raise SystemExit(setup.returncode)
        if not (ROOT / ".lab-state" / "opencode-devnet.json").exists():
            print("OPENCODE_DEVNET_CONFIG=missing")
            print("reason=run inside the DevNet lab model environment")
            raise SystemExit(1)

    adapter = run([sys.executable, "scripts/start_opencode_model_adapter.py"], timeout=20)
    print(adapter.stdout, end="")
    if adapter.returncode != 0:
        print(adapter.stderr, end="", file=sys.stderr)
        raise SystemExit(adapter.returncode)


def opencode_command() -> list[str]:
    model = os.getenv("LLM_MODEL", "gpt-4o")
    cmd = [
        "opencode",
        "run",
        "--format",
        "json",
        "--title",
        "kb-pong-feature",
        "--agent",
        "plan",
        "--model",
        f"devnet/{model}",
        PROMPT,
    ]
    for path in KB_FILES:
        cmd.extend(["--file", str(path)])
    return cmd


def call_opencode() -> str:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["OPENCODE_CONFIG"] = str(ROOT / ".lab-state" / "opencode-devnet.json")
    env.setdefault("OPENCODE_DISABLE_AUTOUPDATE", "true")
    env.setdefault("OPENCODE_DISABLE_LSP_DOWNLOAD", "true")

    cmd = opencode_command()
    print("OPENCODE_KB_COMMAND=" + " ".join(cmd[:10]) + " ...")

    with OUT.open("w", encoding="utf-8") as out:
        process = subprocess.Popen(
            cmd,
            cwd=ROOT,
            env=env,
            text=True,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            process.wait(timeout=70)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
            print("OPENCODE_KB_READ=timeout")
            raise SystemExit(1)

    if process.returncode != 0:
        print("OPENCODE_KB_READ=failed")
        print(f"opencode_rc={process.returncode}")
        print(OUT.read_text(encoding="utf-8")[-1200:])
        raise SystemExit(process.returncode)

    text = extract_text(OUT)
    if "center net" not in text.lower() or "pong" not in text.lower():
        print("OPENCODE_KB_READ=unexpected")
        print(text[:800])
        raise SystemExit(1)

    print("OPENCODE_KB_READ=pass")
    print("OPENCODE_NEXT_ACTION=" + " ".join(text.split())[:240])
    return text


def extract_text(path: Path) -> str:
    parts: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        part = event.get("part", {})
        if isinstance(part, dict) and part.get("type") == "text":
            value = part.get("text", "")
            if isinstance(value, str):
                parts.append(value)
    return "\n".join(parts)


def apply_feature() -> str:
    pong = PONG.read_text(encoding="utf-8")
    tests = PONG_TEST.read_text(encoding="utf-8")
    changed = False

    if "NET_X = WIDTH // 2" not in pong:
        pong = pong.replace("PADDLE_SIZE = 3\n", "PADDLE_SIZE = 3\nNET_X = WIDTH // 2\n")
        changed = True

    net_block = "        if y % 2 == 0:\n            line[NET_X] = \":\"\n"
    if "line[NET_X]" not in pong:
        pong = pong.replace(
            "        if y in cpu:\n            line[-1] = \"|\"\n",
            "        if y in cpu:\n            line[-1] = \"|\"\n" + net_block,
        )
        changed = True

    if 'self.assertIn(":", frame)' not in tests:
        tests = tests.replace(
            '        self.assertIn("o", frame)\n',
            '        self.assertIn("o", frame)\n        self.assertIn(":", frame)\n',
        )
        changed = True

    if changed:
        print("OPENCODE_APPLYING=center-net")
        PONG.write_text(pong, encoding="utf-8")
        PONG_TEST.write_text(tests, encoding="utf-8")
        return "applied"
    return "already-present"


def update_handoff() -> None:
    path = ROOT / ".second-brain" / "sessions" / "current-agent-handoff.md"
    body = path.read_text(encoding="utf-8")
    if "OpenCode read this handoff and applied the center-net Pong feature." in body:
        return
    body += "\n## Latest Update\n\nOpenCode read this handoff and applied the center-net Pong feature.\n"
    path.write_text(body, encoding="utf-8")


def main() -> int:
    ensure_ready()
    call_opencode()
    status = apply_feature()
    update_handoff()

    print(f"OPENCODE_PONG_FEATURE={status}")
    tests = run([sys.executable, "-m", "unittest", "tests.test_pong_game"], timeout=30)
    if tests.returncode != 0:
        print(tests.stdout, end="")
        print(tests.stderr, end="", file=sys.stderr)
        print("OPENCODE_PONG_TESTS=fail")
        return tests.returncode

    print("OPENCODE_PONG_TESTS=pass")
    print("NEXT: python3 scripts/check_repo.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
