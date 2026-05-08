from __future__ import annotations

from datetime import datetime, timezone


VALID_PRIORITIES = {"low", "normal", "high"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_title(title: str) -> str:
    if not isinstance(title, str):
        raise TypeError("title must be a string")

    clean = " ".join(title.strip().split())
    if not clean:
        raise ValueError("title cannot be empty")
    return clean


def next_id(tasks: list[dict]) -> int:
    highest = 0
    for task in tasks:
        try:
            item_id = int(task.get("id", 0))
        except (TypeError, ValueError):
            continue
        if item_id > highest:
            highest = item_id
    return highest + 1


def add_task(tasks: list[dict], title: str, owner: str = "unassigned", priority: str = "normal") -> dict:
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"priority must be one of: {', '.join(sorted(VALID_PRIORITIES))}")

    task = {
        "id": next_id(tasks),
        "title": normalize_title(title),
        "owner": owner.strip() if owner.strip() else "unassigned",
        "priority": priority,
        "done": False,
        "created_at": utc_now(),
        "completed_at": None,
    }
    tasks.append(task)
    return task


def complete_task(tasks: list[dict], task_id: int) -> dict:
    for task in tasks:
        if task.get("id") == task_id:
            if not task.get("done"):
                task["done"] = True
                task["completed_at"] = utc_now()
            return task
    raise LookupError(f"task not found: {task_id}")


def list_tasks(tasks: list[dict], owner: str | None = None, include_done: bool = True) -> list[dict]:
    found = []
    for task in tasks:
        if owner and task.get("owner") != owner:
            continue
        if not include_done and task.get("done"):
            continue
        found.append(dict(task))
    return found


def summarize(tasks: list[dict]) -> dict:
    open_count = 0
    done_count = 0
    high_count = 0

    for task in tasks:
        if task.get("done"):
            done_count += 1
        else:
            open_count += 1
        if task.get("priority") == "high":
            high_count += 1

    return {
        "total": len(tasks),
        "open": open_count,
        "done": done_count,
        "high_priority": high_count,
    }

