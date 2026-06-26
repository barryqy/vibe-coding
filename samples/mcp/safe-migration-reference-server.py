#!/usr/bin/env python3
"""Clean MCP server used as the safe comparison sample."""

from __future__ import annotations

import json

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    class FastMCP:  # type: ignore[override]
        def __init__(self, name: str):
            self.name = name

        def tool(self):
            def decorator(func):
                return func

            return decorator

        def run(self) -> None:
            raise RuntimeError("fastmcp is required to run this MCP server.")


mcp = FastMCP("safe-migration-reference")

CHECKLISTS = {
    "checks": [
        "Confirm the agent can reach the intended model route.",
        "Review new tools before adding them to the workspace.",
        "Keep one small rollback note before changing a workflow.",
    ],
    "launch": [
        "Keep the workspace small and readable.",
        "Run one short prompt before enabling extra tools.",
        "Add extensions only after they have been reviewed.",
    ],
    "fallback": [
        "Remove untrusted extensions from the workspace.",
        "Restore the previous runtime config.",
        "Keep scanner output with the change notes.",
    ],
}


@mcp.tool()
def get_cutover_checklist(stage: str) -> str:
    """Return a short rollout checklist for checks, launch, or fallback."""
    stage_name = stage.strip().lower()
    if stage_name not in CHECKLISTS:
        return "Unknown stage. Use checks, launch, or fallback."

    return json.dumps({"stage": stage_name, "items": CHECKLISTS[stage_name]}, indent=2)


@mcp.tool()
def estimate_ticket_window(host_count: int, change_type: str = "rolling") -> str:
    """Estimate a simple rollout window from the host count and change type."""
    if host_count < 1:
        return "Host count must be greater than zero."

    if change_type not in {"rolling", "full-stop"}:
        return "Change type must be rolling or full-stop."

    per_host = 6 if change_type == "rolling" else 10
    return json.dumps(
        {
            "host_count": host_count,
            "change_type": change_type,
            "estimated_minutes": host_count * per_host,
        },
        indent=2,
    )


@mcp.tool()
def search_runbooks(query: str, limit: int = 3) -> str:
    """Return a few canned runbook matches for a rollout topic."""
    if not query.strip():
        return "Query is required."

    if limit < 1 or limit > 10:
        return "Limit must stay between 1 and 10."

    results = [
        {"title": f"{query} cutover checklist", "confidence": 0.95},
        {"title": f"{query} rollback steps", "confidence": 0.89},
        {"title": f"{query} validation notes", "confidence": 0.82},
    ]
    return json.dumps({"query": query, "results": results[:limit]}, indent=2)


if __name__ == "__main__":
    mcp.run()
