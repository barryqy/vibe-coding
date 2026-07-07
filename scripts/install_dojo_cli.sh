#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_binary="${repo_root}/bin/dojo-linux-x86_64"
checksum_file="${source_binary}.sha256"
install_path="${HOME}/.local/bin/dojo"
player_tool="${HOME}/.local/bin/player"

case "$(uname -m)" in
  x86_64|amd64) ;;
  *)
    echo "dojo challenges require the x86-64 lab environment" >&2
    exit 1
    ;;
esac

expected="$(awk 'NR == 1 {print $1}' "${checksum_file}")"
if command -v sha256sum >/dev/null 2>&1; then
  actual="$(sha256sum "${source_binary}" | awk '{print $1}')"
else
  actual="$(shasum -a 256 "${source_binary}" | awk '{print $1}')"
fi

if [ -z "${expected}" ] || [ "${actual}" != "${expected}" ]; then
  echo "dojo binary checksum did not match" >&2
  exit 1
fi

mkdir -p "$(dirname "${install_path}")"
install -m 755 "${source_binary}" "${install_path}"
install -m 755 "${repo_root}/scripts/player" "${player_tool}"
rm -f "${HOME}/.local/bin/change-name.py"
