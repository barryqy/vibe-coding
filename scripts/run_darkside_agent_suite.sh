#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"
state_dir="${repo_root}/.lab-state/darkside"
mkdir -p "${state_dir}"

{
  echo "RISK_GENERATED_CODE=eval,shell"
  python3 scripts/run_darkside_code_demo.py
} >"${state_dir}/generated-code-risk.txt"
cat "${state_dir}/generated-code-risk.txt"

{
  echo "RISK_SKILL=credential-read,outbound-post"
  python3 scripts/run_risky_skill_demo.py
} >"${state_dir}/risky-skill-risk.txt"
cat "${state_dir}/risky-skill-risk.txt"

{
  echo "RISK_MCP=file-read,eval,shell"
  .venv/bin/python scripts/run_risky_mcp_demo.py
} >"${state_dir}/risky-mcp-risk.txt"
cat "${state_dir}/risky-mcp-risk.txt"
