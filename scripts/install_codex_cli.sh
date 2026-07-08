#!/usr/bin/env bash

set -euo pipefail

version="0.142.5"
target="x86_64-unknown-linux-musl"
installer_dir="${VIBE_INSTALLER_DIR:-/opt/vibe-coding/installers}"
archive="${installer_dir}/codex-package-${target}.tar.gz"
checksum="${archive}.sha256"
install_home="${CODEX_STANDALONE_HOME:-${HOME}/.codex}/packages/standalone"
release_dir="${install_home}/releases/${version}-${target}"
current_link="${install_home}/current"
command_link="${HOME}/.local/bin/codex"

file_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
    return
  fi
  shasum -a 256 "$1" | awk '{print $1}'
}

case "${VIBE_INSTALLER_ARCH:-$(uname -m)}" in
  x86_64 | amd64) ;;
  *)
    echo "Codex installer: this lab image requires x86-64 Linux." >&2
    exit 1
    ;;
esac

export PATH="${HOME}/.local/bin:${HOME}/.codex/bin:${PATH}"
if command -v codex >/dev/null 2>&1 && codex --version 2>/dev/null | grep -q "${version}"; then
  echo "Codex CLI ${version} is already installed."
  codex --version
  exit 0
fi

if [ ! -f "$archive" ] || [ ! -f "$checksum" ]; then
  echo "Codex installer: the lab image is missing the preloaded package." >&2
  echo "Expected: ${archive}" >&2
  exit 1
fi

expected="$(awk 'NR == 1 {print $1}' "$checksum")"
actual="$(file_sha256 "$archive")"
if [ -z "$expected" ] || [ "$actual" != "$expected" ]; then
  echo "Codex installer: package checksum did not match." >&2
  exit 1
fi

echo "Installing Codex CLI ${version} from the lab image..."
stage_dir="${install_home}/releases/.staging-${version}-$$"
rm -rf "$stage_dir"
mkdir -p "$stage_dir" "${HOME}/.local/bin"
trap 'rm -rf "$stage_dir"' EXIT

tar -xzf "$archive" -C "$stage_dir"
test -x "$stage_dir/bin/codex"
chmod 0755 "$stage_dir/bin/codex" "$stage_dir/codex-path/rg"
if [ -f "$stage_dir/codex-resources/bwrap" ]; then
  chmod 0755 "$stage_dir/codex-resources/bwrap"
fi

rm -rf "$release_dir"
mv "$stage_dir" "$release_dir"
ln -sfn "$release_dir" "$current_link"
ln -sfn "$current_link/bin/codex" "$command_link"
hash -r
trap - EXIT

echo "Installed: $(codex --version)"
if command -v bwrap >/dev/null 2>&1; then
  echo "Sandbox helper: $(command -v bwrap)"
elif [ -x "$current_link/codex-resources/bwrap" ]; then
  ln -sfn "$current_link/codex-resources/bwrap" "${HOME}/.local/bin/bwrap"
  echo "Sandbox helper: ${HOME}/.local/bin/bwrap"
else
  echo "Sandbox helper: not found" >&2
  exit 1
fi
