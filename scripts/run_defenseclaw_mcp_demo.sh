#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck disable=SC1091
source "${repo_root}/scripts/lab_session_env.sh"

state_dir="${repo_root}/.lab-state/defenseclaw"
venv_dir="${state_dir}/.venv"
cli_path="${venv_dir}/bin/defenseclaw"
reports_dir="${state_dir}/reports"
risky_mcp_package="${repo_root}/samples/mcp"

if [ ! -x "${cli_path}" ]; then
  echo "DefenseClaw CLI is not installed. Run ./scripts/install_defenseclaw_cli.sh first." >&2
  exit 1
fi

# shellcheck disable=SC1091
source "${venv_dir}/bin/activate"

mkdir -p "${reports_dir}"

if ! command -v uvx >/dev/null 2>&1; then
  echo "uvx is required for the allowlisted MCP scan path. Run ./scripts/install_defenseclaw_cli.sh first." >&2
  exit 1
fi

# A rejected admission is recorded in the local policy store. Clear that
# previous verdict so rerunning the exercise performs the content scan again.
DEFENSECLAW_HOME="${DEFENSECLAW_HOME}" defenseclaw mcp unblock workspace_admin >/dev/null 2>&1 || true

set +e
malicious_output="$(
  DEFENSECLAW_HOME="${DEFENSECLAW_HOME}" defenseclaw mcp set workspace_admin \
    --command uvx \
    --args "[\"--from\",\"${risky_mcp_package}\",\"workspace-admin-bridge\"]" \
    --transport stdio 2>&1
)"
malicious_rc=$?
set -e

printf '%s\n' "${malicious_output}" > "${reports_dir}/defenseclaw-malicious-mcp.txt"
cat "${reports_dir}/defenseclaw-malicious-mcp.txt"

if [ "${malicious_rc}" -eq 0 ]; then
  echo "DEFENSECLAW_MCP_ADMISSION=unexpected-allowed" >&2
  exit 1
fi

if printf '%s' "${malicious_output}" | grep -Eiq 'not an allowlisted stdio launcher|allowed: npx, uvx'; then
  echo "DEFENSECLAW_MCP_ADMISSION=launcher-only" >&2
  exit 1
fi

if ! printf '%s' "${malicious_output}" | grep -Eq '\[(HIGH|CRITICAL)\]' \
  || ! printf '%s' "${malicious_output}" | grep -q 'Location: tool:'; then
  echo "DEFENSECLAW_MCP_ADMISSION=unexpected-result" >&2
  exit 1
fi

echo "DEFENSECLAW_MCP_ADMISSION=blocked"
echo "block_reason=per-tool-content"
echo "DEFENSECLAW_MCP=pass"
echo "Plain language: DefenseClaw refused the risky MCP server after content-based findings, not just the launcher name."
