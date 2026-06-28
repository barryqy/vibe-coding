#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dojo_app.lab_output import print_status


def read_sample(path: str) -> str:
    target = ROOT / path
    try:
        return target.read_text(encoding="utf-8")
    except OSError as exc:
        print_status(f"SCENARIO_REVIEW=missing {path}: {exc}")
        raise SystemExit(1)


def has(pattern: str, text: str) -> bool:
    return bool(re.search(pattern, text, re.IGNORECASE | re.MULTILINE))


def print_case(name: str, risk: str, gate: str) -> None:
    print_status(f"SCENARIO={name}")
    print_status(f"RISK={risk}")
    print_status(f"RECOMMENDED_GATE={gate}")


def check_guardrails() -> bool:
    rollout = read_sample("samples/guardrails/rollout-note.md")
    privacy = read_sample("samples/guardrails/privacy-request.txt")

    prompt_ok = has(r"ignore.+request|developer instructions|credential file", rollout)
    privacy_ok = has(r"cloud key|customer email|private token", privacy) and has(r"AKIA[0-9A-Z]{16}", privacy)

    print_status("SCENARIO_GROUP=guardrails")
    if prompt_ok:
        print_case("prompt-injection", "hidden-instruction-in-user-content", "block-or-strip-before-model")
    else:
        print_status("SCENARIO=prompt-injection")
        print_status("RISK=missing")

    if privacy_ok:
        print_case("privacy-extraction", "secret-and-pii-request", "block-before-model")
    else:
        print_status("SCENARIO=privacy-extraction")
        print_status("RISK=missing")

    return prompt_ok and privacy_ok


def check_code() -> bool:
    unsafe_agent = read_sample("samples/unsafe_agent_patch.py")
    leaky_maze = read_sample("samples/leaky_maze_patch.py")
    unsafe_report = read_sample("samples/unsafe_report_patch.py")

    checks = [
        ("exec-write", has(r"\beval\s*\(|shell\s*=\s*True", unsafe_agent), "dynamic-code-or-shell-execution"),
        ("private-key", has(r"BEGIN OPENSSH PRIVATE KEY|sk-[A-Za-z0-9]{20,}", leaky_maze), "secret-material-in-source"),
        ("sql-query", has(r"SELECT .+\{user_id\}|execute\(query\)", unsafe_report), "sql-built-from-user-input"),
        ("os-command", has(r"\bos\.system\s*\(", unsafe_report), "shell-command-from-generated-code"),
    ]

    print_status("SCENARIO_GROUP=generated-code")
    passed = True
    for name, ok, risk in checks:
        if ok:
            print_case(name, risk, "send-back-for-rewrite")
        else:
            print_status(f"SCENARIO={name}")
            print_status("RISK=missing")
            passed = False
    return passed


def check_mcp() -> bool:
    mcp = read_sample("samples/mcp/workspace-admin-bridge.py")
    checks = [
        ("secret-read", has(r"read_runtime_config|aws/credentials|/etc/passwd", mcp), "local-file-read-tool"),
        ("shell-command", has(r"shell\s*=\s*True|collect_support_bundle", mcp), "host-shell-tool"),
        ("internal-fetch", has(r"169\.254\.169\.254|localhost|attacker", mcp), "internal-network-and-exfiltration-tool"),
    ]

    print_status("SCENARIO_GROUP=mcp-tools")
    passed = True
    for name, ok, risk in checks:
        if ok:
            print_case(name, risk, "require-admission-scan")
        else:
            print_status(f"SCENARIO={name}")
            print_status("RISK=missing")
            passed = False
    return passed


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Review the local agent-risk scenarios used in the lab.")
    parser.add_argument(
        "scenario",
        nargs="?",
        default="all",
        choices=["all", "guardrails", "code", "mcp"],
        help="Scenario group to review.",
    )
    args = parser.parse_args(argv)

    checks = {
        "guardrails": check_guardrails,
        "code": check_code,
        "mcp": check_mcp,
    }

    groups = checks.keys() if args.scenario == "all" else [args.scenario]
    passed = True
    for group in groups:
        if not checks[group]():
            passed = False

    if passed:
        print_status("SCENARIO_REVIEW=pass")
        return 0

    print_status("SCENARIO_REVIEW=check-output")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
