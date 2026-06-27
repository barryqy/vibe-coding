#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_LINES = [
    "APP: play.py",
    "DOCS: GAME_README.md",
    "GAME: rock-paper-scissors",
    "MODE: human-vs-computer",
    "MODE: human-vs-human",
    "VERIFY: python3 -m py_compile play.py",
    "VERIFY: timeout 10s python3 play.py --self-test",
    "VERIFY: printf '1\\nrock\\nq\\n' | timeout 10s python3 play.py",
    "VERIFY: printf '1\\nlizard\\nq\\n' | timeout 10s python3 play.py",
    "VERIFY: printf '2\\nrock\\nscissors\\nq\\n' | timeout 10s python3 play.py",
    "MARKER: RPS_SELF_TEST=pass",
]


def fenced_blocks(text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"```(?:text|markdown|md)?\s*\n(.*?)\n```", text, re.S)]


def extract_contract(text: str) -> str:
    candidates = [block for block in fenced_blocks(text) if "APP: play.py" in block]
    if not candidates and "APP: play.py" in text:
        lines = text.splitlines()
        start = next(i for i, line in enumerate(lines) if line.strip() == "APP: play.py")
        tail: list[str] = []
        for line in lines[start:]:
            clean = line.rstrip()
            if clean.startswith("```"):
                break
            if clean.startswith("Please create ") or clean.startswith("Here is "):
                break
            tail.append(clean)
        candidates.append("\n".join(tail).strip())

    if not candidates:
        raise ValueError("could not find APP: play.py in the model output")

    contract = candidates[0]
    contract = contract.replace("\r\n", "\n").replace("\r", "\n")
    contract = "\n".join(line.rstrip() for line in contract.splitlines()).strip()
    if "```" in contract:
        raise ValueError("contract still contains a Markdown code fence")
    return contract + "\n"


def validate_contract(contract: str) -> list[str]:
    lines = {line.strip() for line in contract.splitlines()}
    missing = [line for line in REQUIRED_LINES if line not in lines]
    bad_phrases = [
        "Please create",
        "Here is the contract",
        "To create the",
        "I will",
    ]
    for phrase in bad_phrases:
        if phrase in contract:
            missing.append(f"remove prose phrase: {phrase}")
    return missing


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Extract and validate the RPS game contract from model output.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)

    try:
        contract = extract_contract(args.input.read_text(encoding="utf-8"))
        problems = validate_contract(contract)
        if problems:
            for problem in problems:
                print(f"CONTRACT_CHECK=missing {problem}", file=sys.stderr)
            return 1
        args.output.write_text(contract, encoding="utf-8")
    except OSError as exc:
        print(f"CONTRACT_CHECK=io-error {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"CONTRACT_CHECK=fail {exc}", file=sys.stderr)
        return 1

    print("CONTRACT_CHECK=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
