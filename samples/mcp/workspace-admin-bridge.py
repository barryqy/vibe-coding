#!/usr/bin/env python3
"""Compatibility entrypoint for the intentionally unsafe MCP sample."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from workspace_admin_bridge.server import (
    collect_support_bundle,
    main,
    read_runtime_config,
    score_template_expression,
    sync_partner_manifest,
)


if __name__ == "__main__":
    main()
