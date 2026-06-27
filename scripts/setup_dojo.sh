#!/usr/bin/env bash

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root" || exit 1

mkdir -p data .lab-state .second-brain/decisions
mkdir -p "$HOME/.local/bin"
chmod +x "$repo_root/scripts/model_usage.py"
ln -sf "$repo_root/scripts/model_usage.py" "$HOME/.local/bin/usage"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements.txt

if [ ! -f data/tasks.json ]; then
  printf '[]\n' > data/tasks.json
fi

echo "SETUP_DOJO=ready"
echo "USAGE_COMMAND=usage"
echo "NEXT=codex --version"
