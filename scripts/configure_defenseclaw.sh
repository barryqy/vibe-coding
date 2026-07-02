#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck disable=SC1091
source "${repo_root}/scripts/lab_session_env.sh"

state_dir="${repo_root}/.lab-state/defenseclaw"
venv_dir="${state_dir}/.venv"
cli_path="${venv_dir}/bin/defenseclaw"
configured_marker="${state_dir}/guardrail-configured"

if [ ! -x "${cli_path}" ]; then
  echo "DefenseClaw CLI is not installed. Run ./scripts/install_defenseclaw_cli.sh first." >&2
  exit 1
fi

# shellcheck disable=SC1091
source "${venv_dir}/bin/activate"

base_url="${LLM_BASE_URL:-}"
api_key="${LLM_API_KEY:-}"
model_name="${LLM_MODEL:-gpt-5-nano}"

if [ -z "${base_url}" ] || [ -z "${api_key}" ]; then
  echo "LLM_BASE_URL and LLM_API_KEY must be set for guardrail configuration." >&2
  exit 1
fi

lab_llm_base="${base_url%/}"
if [[ "${lab_llm_base}" == */chat/completions ]]; then
  lab_llm_base="${lab_llm_base%/chat/completions}"
fi

export LLM_API_KEY="${api_key}"
export OPENAI_API_KEY="${api_key}"
export OPENAI_API_BASE="${lab_llm_base}"
export OPENAI_BASE_URL="${lab_llm_base}"
export VIBE_LLM_API_BASE="${lab_llm_base}"

read_guardrail_port() {
  DEFENSECLAW_HOME="${DEFENSECLAW_HOME}" python3 - <<'PY'
import os
from pathlib import Path

import yaml

home = Path(os.environ["DEFENSECLAW_HOME"])
cfg_path = home / "config.yaml"
if not cfg_path.exists():
    print(4000)
    raise SystemExit(0)

cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
guardrail = cfg.get("guardrail", {}) or {}
print(int(guardrail.get("port", 4000) or 4000))
PY
}

guardrail_healthy() {
  local port="$1"
  python3 - "${port}" <<'PY'
import sys
import urllib.request

port = sys.argv[1]
url = f"http://127.0.0.1:{port}/health"
try:
    with urllib.request.urlopen(url, timeout=2) as resp:
        raise SystemExit(0 if resp.status == 200 else 1)
except Exception:
    raise SystemExit(1)
PY
}

wait_for_guardrail() {
  local port="$1"
  local attempts="${2:-45}"
  local idx=0

  while [ "${idx}" -lt "${attempts}" ]; do
    if guardrail_healthy "${port}"; then
      return 0
    fi
    idx=$((idx + 1))
    sleep 1
  done
  return 1
}

echo "[1/5] Configuring DefenseClaw for the DevNet lab model..."
DEFENSECLAW_HOME="${DEFENSECLAW_HOME}" VIBE_LLM_API_BASE="${lab_llm_base}" LLM_MODEL="${model_name}" python3 - <<'PY'
import os
from pathlib import Path

import yaml

home = Path(os.environ["DEFENSECLAW_HOME"])
cfg_path = home / "config.yaml"
cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
if not isinstance(cfg, dict):
    cfg = {}

model_name = os.environ.get("LLM_MODEL", "gpt-5-nano").strip()
lab_base = os.environ.get("VIBE_LLM_API_BASE", "").rstrip("/")
guardrail = cfg.setdefault("guardrail", {})
top_llm = cfg.setdefault("llm", {})
guardrail_llm = guardrail.setdefault("llm", {})

guardrail["enabled"] = True
guardrail["mode"] = "action"
guardrail["scanner_mode"] = "local"
guardrail["model_name"] = model_name
guardrail["model"] = ""
guardrail["api_base"] = ""
guardrail["api_key_env"] = ""
guardrail["original_model"] = guardrail.get("original_model") or f"openai/{model_name}"

top_llm["provider"] = "openai"
top_llm["model"] = f"openai/{model_name}"
top_llm["api_key_env"] = "LLM_API_KEY"
top_llm["base_url"] = lab_base
top_llm["timeout"] = int(top_llm.get("timeout") or 30)
top_llm["max_retries"] = int(top_llm.get("max_retries") or 2)

guardrail_llm["provider"] = "openai"
guardrail_llm["model"] = f"openai/{model_name}"
guardrail_llm["api_key_env"] = "LLM_API_KEY"
guardrail_llm["base_url"] = lab_base
guardrail_llm["timeout"] = top_llm["timeout"]
guardrail_llm["max_retries"] = top_llm["max_retries"]

home.mkdir(parents=True, exist_ok=True)
cfg_path.write_text(yaml.dump(cfg, default_flow_style=False, sort_keys=False), encoding="utf-8")

env_path = home / ".env"
lines = []
if env_path.exists():
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        key = raw.split("=", 1)[0].strip()
        if key in {"LLM_API_KEY", "OPENAI_API_KEY", "VIBE_LLM_API_BASE", "OPENAI_API_BASE", "OPENAI_BASE_URL"}:
            continue
        lines.append(raw)
entries = {
    "LLM_API_KEY": os.environ.get("LLM_API_KEY", ""),
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
    "VIBE_LLM_API_BASE": lab_base,
    "OPENAI_API_BASE": lab_base,
    "OPENAI_BASE_URL": lab_base,
}
lines.extend(f"{k}={v}" for k, v in sorted(entries.items()) if v)
env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
env_path.chmod(0o600)
print(f"Configured guardrail for openai/{model_name} -> {lab_base}")
PY

echo "[2/5] Activating strict policy and setting up the guardrail sidecar..."
DEFENSECLAW_HOME="${DEFENSECLAW_HOME}" defenseclaw policy activate strict
DEFENSECLAW_HOME="${DEFENSECLAW_HOME}" defenseclaw setup guardrail \
  --non-interactive \
  --connector codex \
  --mode action \
  --scanner-mode local \
  --rule-pack strict \
  --no-verify \
  --no-restart

# Connector detection can conservatively downgrade setup to observe mode.
# This lab calls the local inspect API directly, so pin its global mode after setup.
DEFENSECLAW_HOME="${DEFENSECLAW_HOME}" python3 - <<'PY'
import os
from pathlib import Path

import yaml

home = Path(os.environ["DEFENSECLAW_HOME"])
cfg_path = home / "config.yaml"
cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
guardrail = cfg.setdefault("guardrail", {})
guardrail["enabled"] = True
guardrail["mode"] = "action"
guardrail["rule_pack_dir"] = str(home / "policies" / "guardrail" / "strict")
guardrail.setdefault("hilt", {})["enabled"] = False

connectors = guardrail.get("connectors", {})
if isinstance(connectors, dict) and isinstance(connectors.get("codex"), dict):
    connectors["codex"]["mode"] = "action"

cfg_path.write_text(yaml.dump(cfg, default_flow_style=False, sort_keys=False), encoding="utf-8")
cfg_path.chmod(0o600)
print("Guardrail enforcement pinned to action mode with the strict rule pack.")
PY

echo "[3/5] Waiting for the DefenseClaw sidecar API..."
if command -v defenseclaw-gateway >/dev/null 2>&1; then
  defenseclaw-gateway restart >/dev/null 2>&1 || defenseclaw-gateway start >/dev/null 2>&1 || true
fi

guardrail_mode="$(DEFENSECLAW_HOME="${DEFENSECLAW_HOME}" python3 - <<'PY'
import os
from pathlib import Path

import yaml

cfg = yaml.safe_load((Path(os.environ["DEFENSECLAW_HOME"]) / "config.yaml").read_text(encoding="utf-8")) or {}
print((cfg.get("guardrail", {}) or {}).get("mode", ""))
PY
)"
if [ "$guardrail_mode" != "action" ]; then
  echo "DefenseClaw did not stay in action mode." >&2
  exit 1
fi

api_port=18970
api_ready=0
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if python3 - <<'PY' 2>/dev/null
import urllib.request
with urllib.request.urlopen("http://127.0.0.1:18970/health", timeout=2) as resp:
    raise SystemExit(0 if resp.status == 200 else 1)
PY
  then
    api_port=18970
    api_ready=1
    break
  fi
  sleep 1
done

if [ "${api_ready}" -ne 1 ]; then
  echo "DefenseClaw sidecar API did not become healthy." >&2
  DEFENSECLAW_HOME="${DEFENSECLAW_HOME}" defenseclaw status || true
  exit 1
fi

echo "DefenseClaw sidecar API is healthy at http://127.0.0.1:${api_port}/health"

echo "[4/5] Preparing guardrail demo fixtures..."
bash "${repo_root}/scripts/prepare_guardrail_fixtures.sh" >/dev/null

echo "[5/5] Marking DefenseClaw guardrail as configured for this lab..."
mkdir -p "$(dirname "${configured_marker}")"
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${configured_marker}"
DEFENSECLAW_HOME="${DEFENSECLAW_HOME}" defenseclaw status || true
echo "DEFENSECLAW_GUARDRAIL=configured"
echo "DEFENSECLAW_SIDECAR=http://127.0.0.1:${api_port}/health"
echo "Plain language: requests can now be inspected at the DefenseClaw sidecar before they reach the model."
