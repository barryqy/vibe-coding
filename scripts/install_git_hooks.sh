#!/bin/sh
# Point this repo at version-controlled hooks that strip Cursor co-author trailers.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
chmod +x .githooks/*
git config core.hooksPath .githooks
echo "core.hooksPath=.githooks"
