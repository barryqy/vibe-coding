#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

echo "RISK_GENERATED_CODE=eval,shell"
python3 scripts/run_darkside_code_demo.py

echo "RISK_SKILL=credential-read,outbound-post"
python3 scripts/run_risky_skill_demo.py

echo "RISK_MCP=file-read,eval,shell"
.venv/bin/python scripts/run_risky_mcp_demo.py
