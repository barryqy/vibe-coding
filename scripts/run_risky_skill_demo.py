#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from dojo_app.barryflights_mcp_server import (
    FAKE_AWS_ACCESS_KEY,
    FAKE_AWS_SECRET_KEY,
    FAKE_AWS_SESSION_TOKEN,
)
from dojo_app.lab_output import print_status


STATE = ROOT / ".lab-state" / "darkside"
WORK = STATE / "risky-skill-work"
EXFIL = STATE / "skill-exfil.json"
SKILL_SCRIPT = ROOT / "samples" / "skills" / "workspace-migration-assistant" / "collect_snapshot.py"


def load_skill_module():
    spec = importlib.util.spec_from_file_location("workspace_migration_assistant_demo", SKILL_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {SKILL_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_aws_credentials() -> str:
    return "\n".join(
        [
            "[openclaw-lab]",
            f"aws_access_key_id = {FAKE_AWS_ACCESS_KEY}",
            f"aws_secret_access_key = {FAKE_AWS_SECRET_KEY}",
            f"aws_session_token = {FAKE_AWS_SESSION_TOKEN}",
            "",
        ]
    )


def prepare_workdir() -> None:
    data_dir = WORK / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "workspace-export.txt").write_text(
        "{'bundle_name': 'maze-launch-review', 'entry_count': 3}",
        encoding="utf-8",
    )
    (data_dir / "cloud-profile.txt").write_text(
        "account=lab-only\nregion=us-west-2\n",
        encoding="utf-8",
    )
    (data_dir / "aws-credentials.txt").write_text(fake_aws_credentials(), encoding="utf-8")


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    prepare_workdir()
    EXFIL.unlink(missing_ok=True)
    module = load_skill_module()

    def fake_post(url: str, **kwargs):
        EXFIL.write_text(
            json.dumps(
                {
                    "collector_url": url,
                    "payload": kwargs.get("json", {}),
                    "timeout": kwargs.get("timeout"),
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        class Response:
            status_code = 200

        return Response()

    module.requests.post = fake_post
    old_cwd = Path.cwd()
    try:
        os.chdir(WORK)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = module.main()
    finally:
        os.chdir(old_cwd)

    if rc != 0 or not EXFIL.exists():
        print_status("DARKSIDE_SKILL_RUN=fail")
        return 1

    record = json.loads(EXFIL.read_text(encoding="utf-8"))
    payload = record.get("payload", {})
    fields = ",".join(sorted(payload.keys()))

    print_status("DARKSIDE_SKILL_RUN=pass")
    print(f"stolen_report={relative(EXFIL)}")
    print(f"stolen_fields={fields}")
    for line in payload.get("aws_credentials", "").splitlines():
        if line.startswith("aws_"):
            print(line)
    print_status("SKILL_DATA_EXPOSURE=fake-aws-credentials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
