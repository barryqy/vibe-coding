#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".lab-state" / "codex"
HOME = STATE / "home"
CONFIG = HOME / "config.toml"
MODEL_CATALOG = HOME / "model-catalog.json"
SKILLS_HOME = HOME / "skills"
MAZEMAKER_SKILL_SOURCE = ROOT / "skills" / "mazemaker"
SHIM_BASE_URL = "http://127.0.0.1:8776/v1"


def install_usage_command() -> None:
    source = ROOT / "scripts" / "model_usage.py"
    target = Path.home() / ".local" / "bin" / "usage"
    if not source.exists():
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.unlink()
    except FileNotFoundError:
        pass
    target.symlink_to(source)


def mcp_python() -> Path:
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return venv_python
    return Path(sys.executable)


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def mcp_config_text() -> str:
    return "\n".join(
        [
            "[mcp_servers.barryflights]",
            f"command = {toml_string(str(mcp_python()))}",
            f"args = [{toml_string('-m')}, {toml_string('dojo_app.barryflights_mcp_server')}]",
            f"cwd = {toml_string(str(ROOT))}",
            "",
        ]
    )


def ensure_mcp_cwd(text: str, server_name: str) -> str:
    marker = f"[mcp_servers.{server_name}]"
    start = text.find(marker)
    if start < 0:
        return text

    next_section = text.find("\n[", start + len(marker))
    end = next_section if next_section >= 0 else len(text)
    block = text[start:end]
    if "\ncwd =" in block:
        return text

    lines = block.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("args = "):
            lines.insert(index + 1, f"cwd = {toml_string(str(ROOT))}")
            break
    else:
        lines.append(f"cwd = {toml_string(str(ROOT))}")

    return text[:start] + "\n".join(lines) + text[end:]


def remove_mcp_section(text: str, server_name: str) -> str:
    marker = f"[mcp_servers.{server_name}]"
    start = text.find(marker)
    if start < 0:
        return text

    section_start = start
    if section_start > 0 and text[section_start - 1] == "\n":
        section_start -= 1
    next_section = text.find("\n[", start + len(marker))
    section_end = next_section if next_section >= 0 else len(text)
    return text[:section_start] + text[section_end:]


def install_mazemaker_skill() -> None:
    target = SKILLS_HOME / "mazemaker"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(MAZEMAKER_SKILL_SOURCE, target)


def ensure_mcp_config() -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    install_mazemaker_skill()
    if CONFIG.exists():
        text = CONFIG.read_text(encoding="utf-8")
        original_text = text
        text = remove_mcp_section(text, "mazemaker")
        text = text.replace(
            f"args = [{toml_string(str(ROOT / 'dojo_app' / 'barryflights_mcp_server.py'))}]",
            f"args = [{toml_string('-m')}, {toml_string('dojo_app.barryflights_mcp_server')}]",
        )
        text = ensure_mcp_cwd(text, "barryflights")
        missing = []
        if "[mcp_servers.barryflights]" not in text:
            missing.extend(
                [
                    "[mcp_servers.barryflights]",
                    f"command = {toml_string(str(mcp_python()))}",
                    f"args = [{toml_string('-m')}, {toml_string('dojo_app.barryflights_mcp_server')}]",
                    f"cwd = {toml_string(str(ROOT))}",
                    "",
                ]
            )
        if missing:
            CONFIG.write_text(text.rstrip() + "\n\n" + "\n".join(missing), encoding="utf-8")
        elif text != original_text:
            CONFIG.write_text(text, encoding="utf-8")
        return

    CONFIG.write_text(mcp_config_text(), encoding="utf-8")


def model_catalog(model: str) -> dict:
    return {
        "models": [
            {
                "slug": model,
                "display_name": "DevNet Lab Model",
                "description": "Model supplied by the DevNet learning lab.",
                "default_reasoning_level": "none",
                "supported_reasoning_levels": [],
                "shell_type": "shell_command",
                "visibility": "list",
                "supported_in_api": True,
                "priority": 0,
                "supports_reasoning_summaries": False,
                "support_verbosity": False,
                "truncation_policy": {"mode": "tokens", "limit": 10000},
                "supports_parallel_tool_calls": False,
                "experimental_supported_tools": [],
                "context_window": 128000,
                "max_context_window": 128000,
                "base_instructions": "You are Codex, a coding agent.",
                "model_messages": {
                    "instructions_template": (
                        "You are Codex, a coding agent. Help the user complete "
                        "software tasks clearly and safely.\n\n{{ personality }}"
                    ),
                    "instructions_variables": {
                        "personality_default": "",
                        "personality_friendly": "Be concise, helpful, and collaborative.",
                        "personality_pragmatic": "Be concise, factual, and focused on the task.",
                    },
                },
            }
        ]
    }


def main() -> int:
    base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o")
    install_usage_command()

    if not base_url or not api_key:
        ensure_mcp_config()
        print("CODEX_MODEL_ROUTE=skipped")
        print("reason=LLM_BASE_URL or LLM_API_KEY is missing")
        print("local_mcp=barryflights")
        print("local_skill=mazemaker")
        print("usage_command=usage")
        return 0

    HOME.mkdir(parents=True, exist_ok=True)
    install_mazemaker_skill()
    MODEL_CATALOG.write_text(
        json.dumps(model_catalog(model), indent=2) + "\n",
        encoding="utf-8",
    )
    CONFIG.write_text(
        "\n".join(
            [
                f"model = {toml_string(model)}",
                'model_provider = "devnet"',
                "model_context_window = 128000",
                f"model_catalog_json = {toml_string(str(MODEL_CATALOG))}",
                'approval_policy = "never"',
                'sandbox = "read-only"',
                'web_search = "disabled"',
                'model_reasoning_effort = "none"',
                'model_reasoning_summary = "none"',
                "",
                "[model_providers.devnet]",
                'name = "DevNet Learning Lab LLM"',
                f"base_url = {toml_string(SHIM_BASE_URL)}",
                'wire_api = "responses"',
                "",
                mcp_config_text(),
            ]
        ),
        encoding="utf-8",
    )

    print("CODEX_MODEL_ROUTE=ready")
    print(f"codex_home={HOME.relative_to(ROOT)}")
    print(f"config={CONFIG.relative_to(ROOT)}")
    print(f"model={model}")
    print(f"model_catalog={MODEL_CATALOG.relative_to(ROOT)}")
    print("model_context_window=128000")
    print("adapter=python3 scripts/start_codex_model_adapter.py")
    print("local_mcp=barryflights")
    print(f"local_skill={(SKILLS_HOME / 'mazemaker').relative_to(ROOT)}")
    print("usage_command=usage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
