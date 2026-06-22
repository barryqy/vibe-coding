#!/usr/bin/env bash

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root" || exit 1

mkdir -p data .lab-state .second-brain/decisions

if [ ! -f data/tasks.json ]; then
  printf '[]\n' > data/tasks.json
fi

python3 scripts/tool_doctor.py
python3 scripts/vibe_score.py

echo "SETUP_DOJO=ready"
