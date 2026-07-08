#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from dojo_app.lab_output import print_status


STATE = ROOT / ".lab-state" / "darkside"


def load_sample_module():
    path = ROOT / "samples" / "unsafe_agent_patch.py"
    spec = importlib.util.spec_from_file_location("unsafe_agent_patch_demo", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    eval_marker = STATE / "eval-ran.txt"
    shell_marker = STATE / "shell-ran.txt"
    eval_marker.unlink(missing_ok=True)
    shell_marker.unlink(missing_ok=True)

    sample = load_sample_module()
    sample.run_user_math(
        "__import__('pathlib').Path(%r).write_text('eval executed')"
        % str(eval_marker)
    )
    sample.shell_helper(f".; printf shell-executed > {shell_marker}")

    print_status("DARKSIDE_CODE_EXEC=ready")
    print(f"eval_marker={relative(eval_marker)}")
    print(f"shell_marker={relative(shell_marker)}")
    print_status("GENERATED_CODE_SIDE_EFFECT=local-files-written")

    if eval_marker.exists() and shell_marker.exists():
        print_status("DARKSIDE_CODE_EXEC=pass")
        return 0

    print_status("DARKSIDE_CODE_EXEC=fail")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
