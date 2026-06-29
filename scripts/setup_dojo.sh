#!/usr/bin/env bash

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root" || exit 1

lab_status() {
  PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}" python3 -m dojo_app.lab_output status "$1" 2>/dev/null \
    || printf '%s\n' "$1"
}

mkdir -p data .lab-state .second-brain/decisions
mkdir -p "$HOME/.local/bin"
ln -sf "$repo_root/scripts/cprint" "$HOME/.local/bin/cprint"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements.txt

if [ ! -f data/tasks.json ]; then
  printf '[]\n' > data/tasks.json
fi

lab_status "SETUP_DOJO=ready"
lab_status "NEXT=codex --version"
