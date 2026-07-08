#!/usr/bin/env bash

set -euo pipefail

version="1.0.190"
installer_dir="${VIBE_INSTALLER_DIR:-/opt/vibe-coding/installers}"
archive="${installer_dir}/opencode-linux-x64.tar.gz"
checksum="${archive}.sha256"
binary="${HOME}/.opencode/bin/opencode"
command_link="${HOME}/.local/bin/opencode"

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
    echo "OpenCode installer: this lab image requires x86-64 Linux." >&2
    exit 1
    ;;
esac

export PATH="${HOME}/.local/bin:${HOME}/.opencode/bin:${PATH}"
if command -v opencode >/dev/null 2>&1 && [ "$(opencode --version 2>/dev/null)" = "$version" ]; then
  echo "OpenCode ${version} is already installed."
  opencode --version
  exit 0
fi

if [ ! -f "$archive" ] || [ ! -f "$checksum" ]; then
  echo "OpenCode installer: the lab image is missing the preloaded package." >&2
  echo "Expected: ${archive}" >&2
  exit 1
fi

expected="$(awk 'NR == 1 {print $1}' "$checksum")"
actual="$(file_sha256 "$archive")"
if [ -z "$expected" ] || [ "$actual" != "$expected" ]; then
  echo "OpenCode installer: package checksum did not match." >&2
  exit 1
fi

echo "Installing OpenCode ${version} from the lab image..."
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
tar -xzf "$archive" -C "$tmp_dir"
test -x "$tmp_dir/opencode"

mkdir -p "$(dirname "$binary")" "${HOME}/.local/bin"
install -m 0755 "$tmp_dir/opencode" "$binary"
ln -sfn "$binary" "$command_link"
hash -r

echo "Installed: OpenCode $(opencode --version)"
