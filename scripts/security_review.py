#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".lab-state", "data"}
PY_PATTERNS = [
    ("HIGH", re.compile(r"\beval\s*\("), "uses eval()"),  # lab-scanner: ignore
    ("HIGH", re.compile(r"\bexec\s*\("), "uses exec()"),  # lab-scanner: ignore
    ("HIGH", re.compile(r"shell\s*=\s*True"), "runs a shell command through shell=True"),  # lab-scanner: ignore
    ("MEDIUM", re.compile(r"\bos\.system\s*\("), "uses os.system()"),  # lab-scanner: ignore
    ("MEDIUM", re.compile(r"\bpickle\.loads\s*\("), "deserializes pickle data"),  # lab-scanner: ignore
    ("MEDIUM", re.compile(r"\byaml\.load\s*\("), "loads YAML without an explicit safe loader"),  # lab-scanner: ignore
]
TEXT_PATTERNS = [
    ("HIGH", re.compile(r"-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----"), "contains a private key"),
    ("HIGH", re.compile(r"sk-[A-Za-z0-9]{20,}"), "looks like a live API key"),
    ("HIGH", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "looks like an AWS access key"),
    ("MEDIUM", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "contains SSN-shaped data"),
    ("MEDIUM", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "contains email-like PII"),
]


def iter_files(paths: list[Path]):
    for start in paths:
        if not start.exists():
            yield start
            continue

        if start.is_file():
            yield start
            continue

        for item in start.rglob("*"):
            if any(part in SKIP_DIRS for part in item.parts):
                continue
            if item.is_file() and item.suffix in {".py", ".md", ".json", ".toml", ".yaml", ".yml", ".txt"}:
                yield item


def scan_file(path: Path) -> list[tuple[str, int, str]]:
    if not path.exists():
        return [("HIGH", 0, "path does not exist")]

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return []

    patterns = list(TEXT_PATTERNS)
    if path.suffix == ".py":
        patterns.extend(PY_PATTERNS)

    issues = []
    for line_no, line in enumerate(lines, start=1):
        if "lab-scanner: ignore" in line:
            continue
        for severity, pattern, message in patterns:
            if pattern.search(line):
                issues.append((severity, line_no, message))
    return issues


def main(argv: list[str]) -> int:
    roots = [Path(arg) for arg in argv] if argv else [Path("dojo_app"), Path("scripts")]
    all_files = list(iter_files(roots))
    findings = []

    for path in all_files:
        for severity, line_no, message in scan_file(path):
            findings.append((severity, path, line_no, message))

    if findings:
        print("SECURITY_REVIEW=fail")
        for severity, path, line_no, message in findings:
            location = f"{path}:{line_no}" if line_no else str(path)
            print(f"[{severity}] {location} {message}")
        return 1

    print("SECURITY_REVIEW=pass")
    print(f"Scanned {len(all_files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
