#!/usr/bin/env bash
# Shared session setup for Vibe Coding 101 lab modules.
# Source from lab exercises:  source scripts/lab_session_env.sh

set -euo pipefail

LAB_REPO_ROOT="${LAB_REPO_ROOT:-/home/developer/src/vibe-coding}"
cd "${LAB_REPO_ROOT}"
export PATH="${LAB_REPO_ROOT}/.lab-state/defenseclaw/bin:${HOME}/.local/bin:${HOME}/.codex/bin:${PATH}"
export DEFENSECLAW_HOME="${LAB_REPO_ROOT}/.lab-state/defenseclaw/home"
export LAB_LLM_MAX_OUTPUT_TOKENS="${LAB_LLM_MAX_OUTPUT_TOKENS:-512}"
mkdir -p .lab-state/codex-output .lab-state/defenseclaw
