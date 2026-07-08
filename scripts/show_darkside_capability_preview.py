#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


LINE_PREFIXES = (
    "GENERATED_CODE_SIDE_EFFECT=",
    "stolen_report=",
    "aws_access_key_id ",
    "SKILL_DATA_EXPOSURE=",
    "stolen_file=",
    "rce_marker=",
    "MCP_CODE_EXECUTION=",
    "DARKSIDE_AGENT_CAPABILITIES=",
)


def capability_preview(text: str) -> list[str]:
    result = []
    seen_prefixes = set()

    for line in text.splitlines():
        prefix = next((item for item in LINE_PREFIXES if line.startswith(item)), None)
        if prefix is None or prefix in seen_prefixes:
            continue
        result.append(line)
        seen_prefixes.add(prefix)

    return result


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} EVIDENCE_FILE", file=sys.stderr)
        return 2

    path = Path(argv[1])
    try:
        lines = capability_preview(path.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"preview unavailable: {exc}", file=sys.stderr)
        return 1

    if not lines:
        print(f"preview unavailable: no capability evidence in {path}", file=sys.stderr)
        return 1

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
