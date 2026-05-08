from __future__ import annotations

import json
from pathlib import Path


DEFAULT_DB = Path("data/tasks.json")


def load_tasks(path: str | Path = DEFAULT_DB) -> list[dict]:
    db_path = Path(path)
    if not db_path.exists():
        return []

    try:
        raw = json.loads(db_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"bad task data in {db_path}") from exc

    if not isinstance(raw, list):
        raise ValueError(f"task data must be a list in {db_path}")

    return raw


def save_tasks(tasks: list[dict], path: str | Path = DEFAULT_DB) -> None:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = db_path.with_suffix(db_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(tasks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(db_path)

