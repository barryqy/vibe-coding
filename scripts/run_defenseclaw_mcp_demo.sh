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
risky_mcp="${repo_root}/samples/mcp/workspace-admin-bridge.py"

if [ ! -x "${cli_path}" ]; then
  echo "DefenseClaw CLI is not installed. Run ./scripts/install_defenseclaw_cli.sh first." >&2
  exit 1
fi

# shellcheck disable=SC1091
source "${venv_dir}/bin/activate"

mkdir -p "${reports_dir}"

python_bin="${repo_root}/.venv/bin/python"
if [ ! -x "${python_bin}" ]; then
  python_bin="$(command -v python3)"
fi

host_python="${VIBE_MCP_PYTHON_BIN:-${python_bin}}"

sidecar_health() {
  python3 - <<'PY' 2>/dev/null
import urllib.request
with urllib.request.urlopen("http://127.0.0.1:18970/health/liveliness", timeout=2) as resp:
    raise SystemExit(0 if resp.status == 200 else 1)
PY
}

ensure_sidecar() {
  if sidecar_health; then
    return 0
  fi
  if command -v defenseclaw-gateway >/dev/null 2>&1; then
    defenseclaw-gateway restart >/tmp/defenseclaw-sidecar.log 2>&1 \
      || defenseclaw-gateway start >/tmp/defenseclaw-sidecar.log 2>&1 || true
  fi
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if sidecar_health; then
      return 0
    fi
    sleep 1
  done
  echo "DefenseClaw sidecar API did not become ready." >&2
  return 1
}

ensure_sidecar

set +e
malicious_output="$(
  DEFENSECLAW_HOME="${DEFENSECLAW_HOME}" defenseclaw mcp set workspace_admin \
    --command "${host_python}" \
    --args "[\"${risky_mcp}\"]" \
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
  if ! printf '%s' "${malicious_output}" | grep -Eiq 'script injection|credential harvesting|HIGH|CRITICAL'; then
    echo "DEFENSECLAW_MCP_ADMISSION=allowlist-only" >&2
    echo "Note: scanner saw launcher refusal without per-tool content findings." >&2
    exit 1
  fi
fi

if ! printf '%s' "${malicious_output}" | grep -Eiq 'HIGH|CRITICAL|script injection|credential harvesting|refusing to scan|block|reject'; then
  echo "DEFENSECLAW_MCP_ADMISSION=unexpected-result" >&2
  exit 1
fi

echo "DEFENSECLAW_MCP_ADMISSION=blocked"
echo "DEFENSECLAW_MCP=pass"
echo "Plain language: DefenseClaw refused the risky MCP server after content-based findings, not just the launcher name."
