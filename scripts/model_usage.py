#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dojo_app.lab_output import print_status
STATE_FILE = ROOT / ".lab-state" / "model-usage.json"
INTERESTING_HEADER_WORDS = (
    "budget",
    "cost",
    "quota",
    "remaining",
    "spend",
    "spent",
    "token",
    "usage",
)


def state_file() -> Path:
    override = os.getenv("VIBE_USAGE_FILE")
    if override:
        return Path(override)
    return STATE_FILE


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def blank_state() -> dict[str, Any]:
    return {
        "version": 1,
        "created_at": now(),
        "updated_at": None,
        "calls": 0,
        "errors": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "tools": {},
        "budget": {},
        "last_error": None,
        "last_headers": {},
        "events": [],
    }


def read_state(path: Path | None = None) -> dict[str, Any]:
    target = path or state_file()
    if not target.exists():
        return blank_state()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return blank_state()
    if not isinstance(data, dict):
        return blank_state()
    merged = blank_state()
    merged.update(data)
    return merged


def write_state(state: dict[str, Any], path: Path | None = None) -> None:
    target = path or state_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(target)


def intish(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(value))
    if isinstance(value, str):
        try:
            return max(0, int(float(value.strip())))
        except ValueError:
            return 0
    return 0


def floater(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace("$", "").replace(",", "")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def normalize_usage(usage: Any) -> dict[str, int]:
    if not isinstance(usage, dict):
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    input_tokens = intish(usage.get("input_tokens"))
    output_tokens = intish(usage.get("output_tokens"))

    if not input_tokens:
        input_tokens = intish(usage.get("prompt_tokens"))
    if not output_tokens:
        output_tokens = intish(usage.get("completion_tokens"))

    total_tokens = intish(usage.get("total_tokens"))
    if not total_tokens:
        total_tokens = input_tokens + output_tokens

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def interesting_headers(headers: Any) -> dict[str, str]:
    if not headers:
        return {}

    items: list[tuple[Any, Any]]
    if hasattr(headers, "items"):
        items = list(headers.items())
    else:
        items = []

    found: dict[str, str] = {}
    for key, value in items:
        name = str(key).lower()
        if any(word in name for word in INTERESTING_HEADER_WORDS):
            found[name] = str(value)
    return found


def parse_budget_text(text: str) -> dict[str, float]:
    result: dict[str, float] = {}
    if not text:
        return result

    patterns = [
        re.compile(r"spent\s+\$?([0-9]+(?:\.[0-9]+)?)\s+of\s+\$?([0-9]+(?:\.[0-9]+)?)", re.I),
        re.compile(r"used\s+\$?([0-9]+(?:\.[0-9]+)?)\s+of\s+\$?([0-9]+(?:\.[0-9]+)?)", re.I),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            result["spent_usd"] = float(match.group(1))
            result["limit_usd"] = float(match.group(2))
            result["source"] = "gateway"
            return result

    remaining = re.search(r"remaining[^0-9$]*\$?([0-9]+(?:\.[0-9]+)?)", text, re.I)
    if remaining:
        result["remaining_usd"] = float(remaining.group(1))
        result["source"] = "gateway"

    return result


def parse_budget_obj(value: Any) -> dict[str, float]:
    result: dict[str, float] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            name = str(key).lower()
            amount = floater(item)
            if amount is not None:
                if ("spent" in name or "used" in name or "cost" in name) and "token" not in name:
                    result.setdefault("spent_usd", amount)
                elif "remaining" in name and "token" not in name:
                    result.setdefault("remaining_usd", amount)
                elif ("budget" in name or "limit" in name or "quota" in name) and "token" not in name:
                    result.setdefault("limit_usd", amount)
            elif isinstance(item, (dict, list, str)):
                result.update({k: v for k, v in parse_budget_obj(item).items() if k not in result})
    elif isinstance(value, list):
        for item in value:
            result.update({k: v for k, v in parse_budget_obj(item).items() if k not in result})
    elif isinstance(value, str):
        result.update(parse_budget_text(value))

    if result:
        result.setdefault("source", "gateway")
    return result


def merge_budget(state: dict[str, Any], budget: dict[str, Any]) -> None:
    if not budget:
        return
    current = state.setdefault("budget", {})
    for key in ("spent_usd", "limit_usd", "remaining_usd", "source"):
        if key in budget:
            current[key] = budget[key]
    if "spent_usd" in current and "limit_usd" in current:
        current["remaining_usd"] = max(0.0, float(current["limit_usd"]) - float(current["spent_usd"]))
    current["updated_at"] = now()


def append_event(state: dict[str, Any], event: dict[str, Any]) -> None:
    events = state.setdefault("events", [])
    events.append(event)
    del events[:-20]


def record_model_response(tool: str, model: str, payload: dict[str, Any], headers: Any = None) -> None:
    usage = normalize_usage(payload.get("usage"))
    header_data = interesting_headers(headers)
    budget = parse_budget_obj(payload)
    if header_data:
        budget.update({k: v for k, v in parse_budget_obj(header_data).items() if k not in budget})

    if not usage["total_tokens"] and not budget and not header_data:
        return

    path = state_file()
    state = read_state(path)
    state["updated_at"] = now()
    state["calls"] = intish(state.get("calls")) + (1 if usage["total_tokens"] else 0)
    state["input_tokens"] = intish(state.get("input_tokens")) + usage["input_tokens"]
    state["output_tokens"] = intish(state.get("output_tokens")) + usage["output_tokens"]
    state["total_tokens"] = intish(state.get("total_tokens")) + usage["total_tokens"]

    tools = state.setdefault("tools", {})
    item = tools.setdefault(
        tool,
        {"calls": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
    )
    item["calls"] = intish(item.get("calls")) + (1 if usage["total_tokens"] else 0)
    item["input_tokens"] = intish(item.get("input_tokens")) + usage["input_tokens"]
    item["output_tokens"] = intish(item.get("output_tokens")) + usage["output_tokens"]
    item["total_tokens"] = intish(item.get("total_tokens")) + usage["total_tokens"]
    item["last_model"] = model
    item["updated_at"] = state["updated_at"]

    state["last_headers"] = header_data
    merge_budget(state, budget)
    append_event(
        state,
        {
            "at": state["updated_at"],
            "tool": tool,
            "model": model,
            **usage,
        },
    )
    write_state(state, path)


def record_model_error(tool: str, model: str, message: str) -> None:
    path = state_file()
    state = read_state(path)
    state["updated_at"] = now()
    state["errors"] = intish(state.get("errors")) + 1
    state["last_error"] = {
        "at": state["updated_at"],
        "tool": tool,
        "model": model,
        "message": message[:500],
    }
    merge_budget(state, parse_budget_text(message))
    append_event(
        state,
        {
            "at": state["updated_at"],
            "tool": tool,
            "model": model,
            "error": message[:160],
        },
    )
    write_state(state, path)


def env_float(names: tuple[str, ...]) -> tuple[float | None, str | None]:
    for name in names:
        value = os.getenv(name)
        if not value:
            continue
        parsed = floater(value)
        if parsed is not None and parsed > 0:
            return parsed, name
    return None, None


def budget_summary(state: dict[str, Any]) -> dict[str, Any]:
    budget = state.get("budget") if isinstance(state.get("budget"), dict) else {}
    if budget and budget.get("source") == "gateway":
        limit = floater(budget.get("limit_usd"))
        spent = floater(budget.get("spent_usd"))
        remaining = floater(budget.get("remaining_usd"))
        if limit is not None and spent is not None:
            remaining = max(0.0, limit - spent)
        if limit is not None and remaining is not None and spent is None:
            spent = max(0.0, limit - remaining)
        return {
            "source": "gateway",
            "limit": limit,
            "spent": spent,
            "remaining": remaining,
        }

    limit, limit_source = env_float(("LAB_MODEL_BUDGET_USD", "DEVNET_MODEL_BUDGET_USD", "LLM_BUDGET_USD"))
    in_rate, in_source = env_float(("LAB_MODEL_INPUT_USD_PER_1M", "LLM_INPUT_USD_PER_1M"))
    out_rate, out_source = env_float(("LAB_MODEL_OUTPUT_USD_PER_1M", "LLM_OUTPUT_USD_PER_1M"))
    if limit is None or in_rate is None or out_rate is None:
        return {
            "source": "not-reported",
            "limit": None,
            "spent": None,
            "remaining": None,
        }

    spent = intish(state.get("input_tokens")) * in_rate / 1_000_000
    spent += intish(state.get("output_tokens")) * out_rate / 1_000_000
    return {
        "source": "configured-estimate",
        "limit": limit,
        "spent": spent,
        "remaining": max(0.0, limit - spent),
        "limit_source": limit_source,
        "input_rate_source": in_source,
        "output_rate_source": out_source,
    }


def fmt_money(value: float | None) -> str:
    if value is None:
        return "unknown"
    return f"${value:.4f}"


def fmt_int(value: int) -> str:
    return f"{value:,}"


def plural(value: int, word: str) -> str:
    if value == 1:
        return word
    return f"{word}s"


def usage_summary(state: dict[str, Any], calls: int) -> str:
    errors = intish(state.get("errors"))
    input_tokens = intish(state.get("input_tokens"))
    output_tokens = intish(state.get("output_tokens"))
    total_tokens = intish(state.get("total_tokens"))

    if not calls and not total_tokens:
        return "no model calls recorded yet"

    return (
        f"{fmt_int(calls)} model {plural(calls, 'call')} recorded, "
        f"{fmt_int(total_tokens)} tokens "
        f"({fmt_int(input_tokens)} input, {fmt_int(output_tokens)} output), "
        f"{fmt_int(errors)} {plural(errors, 'error')}"
    )


def budget_status(budget: dict[str, Any], remaining_pct: float | None) -> str:
    source = budget.get("source")
    limit = budget.get("limit")
    spent = budget.get("spent")
    remaining = budget.get("remaining")

    if source == "gateway":
        if remaining is not None and remaining_pct is not None:
            return f"{fmt_money(remaining)} remaining ({remaining_pct:.1f}%) reported by the lab model route"
        if remaining is not None:
            return f"{fmt_money(remaining)} remaining reported by the lab model route"
        if spent is not None or limit is not None:
            return "budget details reported by the lab model route"
        return "lab model route reported budget details, but not a remaining amount"

    if source == "configured-estimate":
        if remaining is not None and remaining_pct is not None:
            return f"{fmt_money(remaining)} remaining ({remaining_pct:.1f}%) estimated from configured rates"
        if remaining is not None:
            return f"{fmt_money(remaining)} remaining estimated from configured rates"
        return "budget estimated from configured rates"

    return "remaining budget not reported by the lab route; use total_tokens as the local meter"


def print_usage(state: dict[str, Any]) -> int:
    budget = budget_summary(state)
    calls = intish(state.get("calls"))
    limit = budget.get("limit")
    spent = budget.get("spent")
    remaining = budget.get("remaining")
    remaining_pct = None
    if isinstance(limit, (int, float)) and limit > 0 and isinstance(remaining, (int, float)):
        remaining_pct = max(0.0, min(100.0, remaining / limit * 100))

    status = "empty"
    if calls:
        status = "ok"
    if remaining_pct is not None and remaining_pct < 20:
        status = "low"
    if remaining_pct is not None and remaining_pct < 5:
        status = "nearly-empty"

    print_status(f"MODEL_USAGE={status}")
    print_status(f"usage_summary={usage_summary(state, calls)}")
    print_status(f"budget_status={budget_status(budget, remaining_pct)}")
    print_status(f"calls={calls}")
    print_status(f"errors={intish(state.get('errors'))}")
    print_status(f"input_tokens={intish(state.get('input_tokens'))}")
    print_status(f"output_tokens={intish(state.get('output_tokens'))}")
    print_status(f"total_tokens={intish(state.get('total_tokens'))}")

    tools = state.get("tools") if isinstance(state.get("tools"), dict) else {}
    for tool in sorted(tools):
        item = tools.get(tool) if isinstance(tools.get(tool), dict) else {}
        print_status(
            f"{tool}_tokens={intish(item.get('total_tokens'))} "
            f"{tool}_calls={intish(item.get('calls'))}"
        )

    print_status(f"budget_source={budget.get('source', 'unknown')}")
    if budget.get("source") != "not-reported":
        print_status(f"budget_limit={fmt_money(limit)}")
        print_status(f"budget_spent={fmt_money(spent)}")
    print_status(f"budget_remaining={fmt_money(remaining)}")
    if remaining_pct is not None:
        print_status(f"budget_remaining_pct={remaining_pct:.1f}")

    if budget.get("source") == "configured-estimate":
        print_status("budget_note=estimated from configured rates; gateway-reported budget overrides this when available")
    elif budget.get("source") == "gateway":
        print_status("budget_note=reported by the lab model route")
    else:
        print_status("budget_note=the lab route reports per-call token usage but not the hard remaining budget")

    last_error = state.get("last_error")
    if isinstance(last_error, dict) and last_error.get("message"):
        print_status(f"last_error={last_error['message']}")

    if not calls:
        print_status("next=run a Codex or OpenCode model call, then run usage again")
    elif status in {"low", "nearly-empty"}:
        print_status("next=avoid long interactive chats or large build prompts")
    elif budget.get("source") == "not-reported":
        print_status("next=continue with required lab checks; keep optional prompts short")
    else:
        print_status("next=continue with the lab checks")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Show local model token usage for this lab pod.")
    parser.add_argument("--reset", action="store_true", help="clear the local usage counter")
    args = parser.parse_args(argv)

    path = state_file()
    if args.reset:
        write_state(blank_state(), path)
        print_status("MODEL_USAGE=reset")
        return 0

    return print_usage(read_state(path))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
