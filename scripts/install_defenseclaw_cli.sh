#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

lab_status() {
  PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}" python3 -m dojo_app.lab_output status "$1" 2>/dev/null \
    || printf '%s\n' "$1"
}

DEFENSECLAW_VERSION="${DEFENSECLAW_VERSION:-0.8.0}"
DEFENSECLAW_TUI_TEXTUAL_VERSION="${DEFENSECLAW_TUI_TEXTUAL_VERSION:-8.2.7}"
state_dir="${repo_root}/.lab-state/defenseclaw"
venv_dir="${state_dir}/.venv"
cli_path="${venv_dir}/bin/defenseclaw"
gateway_dir="${state_dir}/bin"
gateway_path="${gateway_dir}/defenseclaw-gateway"
home_dir="${DEFENSECLAW_HOME:-${state_dir}/home}"
configured_marker="${state_dir}/guardrail-configured"
wheel_url="https://github.com/cisco-ai-defense/defenseclaw/releases/download/${DEFENSECLAW_VERSION}/defenseclaw-${DEFENSECLAW_VERSION}-py3-none-any.whl"
release_base="https://github.com/cisco-ai-defense/defenseclaw/releases/download/${DEFENSECLAW_VERSION}"

export DEFENSECLAW_HOME="$home_dir"
export PATH="${gateway_dir}:${HOME}/.local/bin:${PATH}"

download_file() {
  local url="$1"
  local out_file="$2"

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$out_file"
    return 0
  fi

  if command -v wget >/dev/null 2>&1; then
    wget -qO "$out_file" "$url"
    return 0
  fi

  python3 - "$url" "$out_file" <<'PY'
import sys
import urllib.request

urllib.request.urlretrieve(sys.argv[1], sys.argv[2])
PY
}

ensure_lab_home() {
  local cli="$1"

  mkdir -p "$DEFENSECLAW_HOME"
  if [ -f "${DEFENSECLAW_HOME}/config.yaml" ] && [ -f "${DEFENSECLAW_HOME}/audit.db" ]; then
    return 0
  fi

  "$cli" init \
    --skip-install \
    --non-interactive \
    --yes \
    --connector codex \
    --profile observe \
    --scanner-mode local \
    --no-start-gateway \
    --no-verify >/dev/null
  "$cli" policy activate strict >/dev/null 2>&1 || true
  rm -f "${configured_marker}"
}

python_version_ok() {
  local candidate="$1"
  local min_major="${2:-3}"
  local min_minor="${3:-11}"

  "$candidate" "$min_major" "$min_minor" - <<'PY' >/dev/null 2>&1
import sys

min_major = int(sys.argv[1])
min_minor = int(sys.argv[2])
raise SystemExit(0 if sys.version_info >= (min_major, min_minor) else 1)
PY
}

ensure_uv_runtime() {
  local tmpdir

  if command -v uv >/dev/null 2>&1 && command -v uvx >/dev/null 2>&1; then
    return 0
  fi

  echo "Installing uv for the DefenseClaw runtime and safe MCP scans..." >&2
  tmpdir="$(mktemp -d)"
  download_file "https://astral.sh/uv/install.sh" "${tmpdir}/install-uv.sh"
  mkdir -p "${HOME}/.local/bin"
  UV_UNMANAGED_INSTALL="${HOME}/.local/bin" sh "${tmpdir}/install-uv.sh" --quiet
  rm -rf "${tmpdir}"

  export PATH="${HOME}/.local/bin:${PATH}"
  hash -r

  if ! command -v uv >/dev/null 2>&1; then
    echo "uv was installed, but it is still not on PATH." >&2
    return 1
  fi
}

resolve_defenseclaw_python() {
  local candidate
  local uv_python

  for candidate in python3.13 python3.12 python3.11 python3; do
    if ! command -v "$candidate" >/dev/null 2>&1; then
      continue
    fi

    if python_version_ok "$candidate" 3 11; then
      command -v "$candidate"
      return 0
    fi
  done

  ensure_uv_runtime
  uv_python="$(uv python find 3.12 2>/dev/null || true)"
  if [ -z "$uv_python" ] || [ ! -x "$uv_python" ]; then
    echo "Installing Python 3.12 for DefenseClaw..." >&2
    uv python install 3.12
    uv_python="$(uv python find 3.12 2>/dev/null || true)"
  fi

  if [ -n "$uv_python" ] && [ -x "$uv_python" ]; then
    echo "$uv_python"
    return 0
  fi

  echo "DefenseClaw needs Python 3.11 or newer." >&2
  return 1
}

version_ok() {
  local candidate="$1"

  "$candidate" - "$DEFENSECLAW_VERSION" <<'PY' >/dev/null 2>&1
import importlib.metadata
import sys

want = sys.argv[1]
try:
    have = importlib.metadata.version("defenseclaw")
except importlib.metadata.PackageNotFoundError:
    raise SystemExit(1)

raise SystemExit(0 if have == want else 1)
PY
}

tui_runtime_ok() {
  local candidate="$1"

  "$candidate" - "$DEFENSECLAW_TUI_TEXTUAL_VERSION" <<'PY' >/dev/null 2>&1
import importlib.metadata
import sys

from textual.widget import Widget

want = sys.argv[1]
have = importlib.metadata.version("textual")
raise SystemExit(0 if have == want and hasattr(Widget, "update_classes") else 1)
PY
}

global_cli_version_ok() {
  defenseclaw --version 2>/dev/null | grep -q "version ${DEFENSECLAW_VERSION}"
}

gateway_version_ok() {
  local candidate="$1"
  [ -x "$candidate" ] \
    && "$candidate" --version 2>/dev/null | grep -q "version ${DEFENSECLAW_VERSION}"
}

choose_python() {
  resolve_defenseclaw_python
}

create_venv() {
  if command -v uv >/dev/null 2>&1; then
    uv venv --no-project --python "$python_bin" "$venv_dir"
    return 0
  fi

  "$python_bin" -m venv "$venv_dir"
}

install_defenseclaw_wheel() {
  if command -v uv >/dev/null 2>&1; then
    uv pip install --quiet --python "$venv_python" "$wheel_url"
    return 0
  fi

  lab_status "DEFENSECLAW_INSTALL=upgrading-pip"
  "$venv_python" -m pip install --quiet --upgrade --disable-pip-version-check pip
  "$venv_python" -m pip install --quiet --upgrade --disable-pip-version-check "$wheel_url"
}

detect_release_platform() {
  local os_name arch_name
  os_name="$(uname -s)"
  arch_name="$(uname -m)"
  case "${os_name}" in
    Linux) printf 'linux_%s\n' "$( [ "${arch_name}" = aarch64 ] || [ "${arch_name}" = arm64 ] && echo arm64 || echo amd64 )" ;;
    Darwin) printf 'darwin_%s\n' "$( [ "${arch_name}" = aarch64 ] || [ "${arch_name}" = arm64 ] && echo arm64 || echo amd64 )" ;;
    *) echo "unsupported-platform" >&2; return 1 ;;
  esac
}

python_module_available() {
  local module_name="$1"
  "$venv_python" - "$module_name" <<'PY' >/dev/null 2>&1
import importlib.util
import sys
raise SystemExit(0 if importlib.util.find_spec(sys.argv[1]) else 1)
PY
}

ensure_lab_scanners() {
  local missing=()
  if ! python_module_available skill_scanner; then
    missing+=("cisco-ai-skill-scanner")
  fi
  if ! python_module_available mcpscanner; then
    missing+=("cisco-ai-mcp-scanner>=4.3")
  fi
  if [ "${#missing[@]}" -eq 0 ]; then
    lab_status "DEFENSECLAW_SCANNERS=ready"
    return 0
  fi
  lab_status "DEFENSECLAW_INSTALL=installing-scanners"
  if command -v uv >/dev/null 2>&1; then
    uv pip install --quiet --python "$venv_python" "${missing[@]}"
  else
    "$venv_python" -m pip install --quiet --disable-pip-version-check "${missing[@]}"
  fi
  lab_status "DEFENSECLAW_SCANNERS=ready"
}

ensure_tui_runtime() {
  if tui_runtime_ok "$venv_python"; then
    lab_status "DEFENSECLAW_TUI=ready"
    return 0
  fi

  lab_status "DEFENSECLAW_INSTALL=installing-tui"
  if command -v uv >/dev/null 2>&1; then
    uv pip install --quiet --python "$venv_python" "textual==${DEFENSECLAW_TUI_TEXTUAL_VERSION}"
  else
    "$venv_python" -m pip install --quiet --disable-pip-version-check \
      "textual==${DEFENSECLAW_TUI_TEXTUAL_VERSION}"
  fi
  lab_status "DEFENSECLAW_TUI=ready"
}

install_gateway_binary() {
  if gateway_version_ok "$gateway_path"; then
    lab_status "DEFENSECLAW_GATEWAY=already-present"
    return 0
  fi
  local platform gateway_name tmpdir
  platform="$(detect_release_platform)"
  gateway_name="defenseclaw_${DEFENSECLAW_VERSION}_${platform}.tar.gz"
  tmpdir="$(mktemp -d)"
  lab_status "DEFENSECLAW_INSTALL=installing-gateway"
  download_file "${release_base}/${gateway_name}" "${tmpdir}/${gateway_name}"
  mkdir -p "${tmpdir}/gateway" "${gateway_dir}"
  tar -xzf "${tmpdir}/${gateway_name}" -C "${tmpdir}/gateway"
  install -m 0755 "${tmpdir}/gateway/defenseclaw" "$gateway_path"
  rm -rf "${tmpdir}"
  hash -r
  lab_status "DEFENSECLAW_GATEWAY=installed"
}

if [ -x "$cli_path" ] && version_ok "${venv_dir}/bin/python"; then
  venv_python="${venv_dir}/bin/python"
  ensure_uv_runtime
  ensure_lab_scanners
  ensure_tui_runtime
  install_gateway_binary
  ensure_lab_home "$cli_path"
  lab_status "DEFENSECLAW_INSTALL=already-present"
  lab_status "DEFENSECLAW_CLI=${cli_path}"
  lab_status "DEFENSECLAW_HOME=${DEFENSECLAW_HOME}"
  "$cli_path" version || true
  exit 0
fi

if command -v defenseclaw >/dev/null 2>&1 && global_cli_version_ok; then
  venv_python="$(command -v python3)"
  ensure_uv_runtime
  ensure_lab_scanners 2>/dev/null || true
  install_gateway_binary
  ensure_lab_home "$(command -v defenseclaw)"
  lab_status "DEFENSECLAW_INSTALL=using-existing"
  lab_status "DEFENSECLAW_CLI=$(command -v defenseclaw)"
  lab_status "DEFENSECLAW_HOME=${DEFENSECLAW_HOME}"
  defenseclaw version || true
  exit 0
fi

python_bin="$(choose_python)"
mkdir -p "$state_dir"

if [ -d "$venv_dir" ] && [ -x "${venv_dir}/bin/python" ] && ! python_version_ok "${venv_dir}/bin/python" 3 11; then
  lab_status "DEFENSECLAW_INSTALL=rebuilding-venv"
  rm -rf "$venv_dir"
fi

if [ -d "$venv_dir" ] && [ ! -x "${venv_dir}/bin/python" ]; then
  lab_status "DEFENSECLAW_INSTALL=rebuilding-incomplete-venv"
  rm -rf "$venv_dir"
fi

if [ ! -d "$venv_dir" ]; then
  lab_status "DEFENSECLAW_INSTALL=creating-venv"
  create_venv
fi

venv_python="${venv_dir}/bin/python"
ensure_uv_runtime
lab_status "DEFENSECLAW_INSTALL=installing-cli"
lab_status "DEFENSECLAW_INSTALL_NOTE=dependency install can take a minute on the first run"
install_defenseclaw_wheel
ensure_lab_scanners
ensure_tui_runtime
install_gateway_binary
lab_status "DEFENSECLAW_INSTALL=initializing-home"
ensure_lab_home "$cli_path"

lab_status "DEFENSECLAW_INSTALL=complete"
lab_status "DEFENSECLAW_CLI=${cli_path}"
lab_status "DEFENSECLAW_HOME=${DEFENSECLAW_HOME}"
"$cli_path" version || true
