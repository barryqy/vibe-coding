#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

DEFENSECLAW_VERSION="${DEFENSECLAW_VERSION:-0.8.0}"
state_dir="${repo_root}/.lab-state/defenseclaw"
venv_dir="${state_dir}/.venv"
cli_path="${venv_dir}/bin/defenseclaw"
home_dir="${DEFENSECLAW_HOME:-${state_dir}/home}"
wheel_url="https://github.com/cisco-ai-defense/defenseclaw/releases/download/${DEFENSECLAW_VERSION}/defenseclaw-${DEFENSECLAW_VERSION}-py3-none-any.whl"

export DEFENSECLAW_HOME="$home_dir"

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
    --no-start-gateway \
    --no-verify >/dev/null
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

  if command -v uv >/dev/null 2>&1; then
    return 0
  fi

  echo "Installing uv so DefenseClaw can use Python 3.12..." >&2
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

global_cli_version_ok() {
  defenseclaw --version 2>/dev/null | grep -q "version ${DEFENSECLAW_VERSION}"
}

choose_python() {
  resolve_defenseclaw_python
}

if [ -x "$cli_path" ] && version_ok "${venv_dir}/bin/python"; then
  ensure_lab_home "$cli_path"
  echo "DEFENSECLAW_INSTALL=already-present"
  echo "DEFENSECLAW_CLI=${cli_path}"
  echo "DEFENSECLAW_HOME=${DEFENSECLAW_HOME}"
  "$cli_path" version || true
  exit 0
fi

if command -v defenseclaw >/dev/null 2>&1 && global_cli_version_ok; then
  ensure_lab_home "$(command -v defenseclaw)"
  echo "DEFENSECLAW_INSTALL=using-existing"
  echo "DEFENSECLAW_CLI=$(command -v defenseclaw)"
  echo "DEFENSECLAW_HOME=${DEFENSECLAW_HOME}"
  defenseclaw version || true
  exit 0
fi

python_bin="$(choose_python)"
mkdir -p "$state_dir"

if [ -d "$venv_dir" ] && [ -x "${venv_dir}/bin/python" ] && ! python_version_ok "${venv_dir}/bin/python" 3 11; then
  echo "DEFENSECLAW_INSTALL=rebuilding-venv"
  rm -rf "$venv_dir"
fi

if [ ! -d "$venv_dir" ]; then
  echo "DEFENSECLAW_INSTALL=creating-venv"
  "$python_bin" -m venv "$venv_dir"
fi

venv_python="${venv_dir}/bin/python"
"$venv_python" -m pip install --upgrade --disable-pip-version-check pip >/dev/null
"$venv_python" -m pip install --upgrade --disable-pip-version-check "$wheel_url" >/dev/null
ensure_lab_home "$cli_path"

echo "DEFENSECLAW_INSTALL=complete"
echo "DEFENSECLAW_CLI=${cli_path}"
echo "DEFENSECLAW_HOME=${DEFENSECLAW_HOME}"
"$cli_path" version || true
