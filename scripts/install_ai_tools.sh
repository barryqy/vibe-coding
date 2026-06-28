#!/usr/bin/env bash

set -uo pipefail

export PATH="$HOME/.local/bin:$HOME/.opencode/bin:$HOME/.bun/bin:$PATH"
CODEX_INSTALL_VERSION="${CODEX_INSTALL_VERSION:-0.137.0}"
OPENCODE_INSTALL_VERSION="${OPENCODE_INSTALL_VERSION:-1.0.190}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
install_mode="${1:-all}"

lab_status() {
  PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" python3 -m dojo_app.lab_output status "$1" 2>/dev/null \
    || printf '%s\n' "$1"
}

case "$install_mode" in
  all | --all)
    install_mode="all"
    ;;
  codex | codex-only | --codex | --codex-only)
    install_mode="codex"
    ;;
  opencode | opencode-only | --opencode | --opencode-only)
    install_mode="opencode"
    ;;
  *)
    echo "Usage: $0 [--codex-only|--opencode-only|--all]" >&2
    exit 2
    ;;
esac

file_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
    return 0
  fi

  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
    return 0
  fi

  return 1
}

codex_package_digest() {
  case "$1:$2" in
    0.137.0:x86_64-unknown-linux-musl)
      echo "b364488097efd12da3b5ffb1b0099cabd8b377b1f97043158f7f771b1456953f"
      ;;
    0.137.0:aarch64-unknown-linux-musl)
      echo "8756c80ad058199676d058bbd919812466d796886e7574a57c4e007f766e707c"
      ;;
    *)
      return 1
      ;;
  esac
}

codex_target() {
  case "$(uname -m)" in
    x86_64 | amd64)
      echo "x86_64-unknown-linux-musl"
      ;;
    arm64 | aarch64)
      echo "aarch64-unknown-linux-musl"
      ;;
    *)
      return 1
      ;;
  esac
}

ensure_codex_bubblewrap() {
  local install_home bundled

  if command -v bwrap >/dev/null 2>&1; then
    lab_status "BUBBLEWRAP=system-present"
    return 0
  fi

  install_home="${CODEX_STANDALONE_HOME:-$HOME/.codex}"
  bundled="${install_home}/packages/standalone/current/codex-resources/bwrap"
  if [ -f "$bundled" ]; then
    mkdir -p "$HOME/.local/bin"
    chmod 0755 "$bundled" 2>/dev/null || true
    ln -sf "$bundled" "$HOME/.local/bin/bwrap"
    export PATH="$HOME/.local/bin:$PATH"
    hash -r 2>/dev/null || true
    if command -v bwrap >/dev/null 2>&1; then
      lab_status "BUBBLEWRAP=bundled-codex"
      return 0
    fi
  fi

  lab_status "BUBBLEWRAP=not-found"
  return 0
}

install_codex_native_package() {
  local target digest asset url tmp_dir archive actual install_home standalone releases release_dir stage_dir current_link

  command -v curl >/dev/null 2>&1 || return 1
  command -v tar >/dev/null 2>&1 || return 1

  target="$(codex_target)" || return 1
  digest="$(codex_package_digest "$CODEX_INSTALL_VERSION" "$target")" || return 1
  asset="codex-package-${target}.tar.gz"
  url="https://github.com/openai/codex/releases/download/rust-v${CODEX_INSTALL_VERSION}/${asset}"
  tmp_dir="$(mktemp -d)"
  archive="${tmp_dir}/${asset}"

  lab_status "CODEX_INSTALL=fallback-native-package"
  if ! curl -fsSL "$url" -o "$archive"; then
    rm -rf "$tmp_dir"
    return 1
  fi

  actual="$(file_sha256 "$archive")" || {
    rm -rf "$tmp_dir"
    return 1
  }
  if [ "$actual" != "$digest" ]; then
    lab_status "CODEX_INSTALL=fallback-checksum-failed"
    rm -rf "$tmp_dir"
    return 1
  fi

  install_home="${CODEX_STANDALONE_HOME:-$HOME/.codex}"
  standalone="${install_home}/packages/standalone"
  releases="${standalone}/releases"
  release_dir="${releases}/${CODEX_INSTALL_VERSION}-${target}"
  stage_dir="${releases}/.staging.${CODEX_INSTALL_VERSION}-${target}.$$"
  current_link="${standalone}/current"

  rm -rf "$stage_dir"
  mkdir -p "$stage_dir" "$HOME/.local/bin"
  if ! tar -xzf "$archive" -C "$stage_dir"; then
    rm -rf "$tmp_dir" "$stage_dir"
    return 1
  fi
  if ! chmod 0755 "$stage_dir/bin/codex" "$stage_dir/codex-path/rg"; then
    rm -rf "$tmp_dir" "$stage_dir"
    return 1
  fi
  if [ -f "$stage_dir/codex-resources/bwrap" ]; then
    chmod 0755 "$stage_dir/codex-resources/bwrap"
  fi
  ln -sf "bin/codex" "$stage_dir/codex"

  rm -rf "$release_dir"
  mv "$stage_dir" "$release_dir"
  rm -rf "$current_link"
  ln -s "$release_dir" "$current_link"
  ln -sf "$current_link/bin/codex" "$HOME/.local/bin/codex"
  rm -rf "$tmp_dir"
  export PATH="$HOME/.local/bin:$PATH"
  hash -r 2>/dev/null || true
  command -v codex >/dev/null 2>&1 && codex --version >/dev/null 2>&1
}

install_codex() {
  if command -v codex >/dev/null 2>&1; then
    lab_status "CODEX_INSTALL=already-present"
    ensure_codex_bubblewrap
    return 0
  fi

  lab_status "CODEX_INSTALL=starting"
  if curl -fsSL https://chatgpt.com/codex/install.sh | CODEX_NON_INTERACTIVE=1 sh; then
    export PATH="$HOME/.local/bin:$PATH"
    hash -r 2>/dev/null || true
    lab_status "CODEX_INSTALL=complete"
    ensure_codex_bubblewrap
    return 0
  fi

  if install_codex_native_package; then
    lab_status "CODEX_INSTALL=complete"
    ensure_codex_bubblewrap
    return 0
  fi

  if command -v npm >/dev/null 2>&1; then
    lab_status "CODEX_INSTALL=fallback-npm"
    mkdir -p "$HOME/.local/bin" "$HOME/.local/share/codex-npm"
    if npm install --prefix "$HOME/.local/share/codex-npm" "@openai/codex@${CODEX_INSTALL_VERSION}"; then
      ln -sf "$HOME/.local/share/codex-npm/node_modules/.bin/codex" "$HOME/.local/bin/codex"
      export PATH="$HOME/.local/bin:$PATH"
      hash -r 2>/dev/null || true
      lab_status "CODEX_INSTALL=complete"
      ensure_codex_bubblewrap
      return 0
    fi
  fi

  lab_status "CODEX_INSTALL=failed"
  return 0
}

install_opencode() {
  if command -v opencode >/dev/null 2>&1; then
    lab_status "OPENCODE_INSTALL=already-present"
    return 0
  fi

  lab_status "OPENCODE_INSTALL=starting"
  mkdir -p "$HOME/.local/bin" "$HOME/.opencode/bin" "$ROOT/.lab-state/opencode-download"
  archive="$ROOT/.lab-state/opencode-download/opencode-linux-x64.tar.gz"
  url="https://github.com/anomalyco/opencode/releases/download/v${OPENCODE_INSTALL_VERSION}/opencode-linux-x64.tar.gz"

  if curl -fL --max-time 180 --progress-bar -o "$archive" "$url"; then
    tar -xzf "$archive" -C "$ROOT/.lab-state/opencode-download"
    install -m 755 "$ROOT/.lab-state/opencode-download/opencode" "$HOME/.opencode/bin/opencode"
    ln -sf "$HOME/.opencode/bin/opencode" "$HOME/.local/bin/opencode"
    export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH"
    hash -r 2>/dev/null || true
    lab_status "OPENCODE_INSTALL=complete"
    return 0
  fi

  lab_status "OPENCODE_INSTALL=failed"
  return 0
}

show_versions() {
  if command -v codex >/dev/null 2>&1; then
    lab_status "CODEX_VERSION=$(codex --version 2>/dev/null | head -1)"
  else
    lab_status "CODEX_VERSION=not-installed"
  fi

  if command -v opencode >/dev/null 2>&1; then
    lab_status "OPENCODE_VERSION=$(opencode --version 2>/dev/null | head -1)"
  else
    lab_status "OPENCODE_VERSION=not-installed"
  fi
}

case "$install_mode" in
  codex)
    install_codex
    ;;
  opencode)
    install_opencode
    ;;
  all)
    install_opencode
    install_codex
    ;;
esac

show_versions

case "$install_mode" in
  codex)
    lab_status "NEXT_STEP=codex --version"
    lab_status "OPENCODE_LATER=./scripts/install_ai_tools.sh --opencode-only"
    ;;
  opencode)
    lab_status "NEXT_STEP=python3 scripts/setup_opencode_devnet.py"
    ;;
  all)
    lab_status "NEXT_STEP=codex --version"
    ;;
esac
