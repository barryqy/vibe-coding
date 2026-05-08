#!/usr/bin/env bash

set -uo pipefail

export PATH="$HOME/.local/bin:$HOME/.opencode/bin:$HOME/.bun/bin:$HOME/.claude/bin:$HOME/.claude/local:$PATH"

install_claude() {
  if command -v claude >/dev/null 2>&1; then
    echo "CLAUDE_INSTALL=already-present"
    return 0
  fi

  echo "CLAUDE_INSTALL=starting"
  if curl -fsSL https://claude.ai/install.sh | bash; then
    export PATH="$HOME/.local/bin:$HOME/.claude/bin:$HOME/.claude/local:$PATH"
    hash -r 2>/dev/null || true
    echo "CLAUDE_INSTALL=complete"
    return 0
  fi

  echo "CLAUDE_INSTALL=failed"
  return 0
}

install_opencode() {
  if command -v opencode >/dev/null 2>&1; then
    echo "OPENCODE_INSTALL=already-present"
    return 0
  fi

  echo "OPENCODE_INSTALL=starting"
  if curl -fsSL https://opencode.ai/install | bash; then
    export PATH="$HOME/.opencode/bin:$HOME/.local/bin:$PATH"
    hash -r 2>/dev/null || true
    echo "OPENCODE_INSTALL=complete"
    return 0
  fi

  echo "OPENCODE_INSTALL=failed"
  return 0
}

show_versions() {
  if command -v claude >/dev/null 2>&1; then
    echo "CLAUDE_VERSION=$(claude --version 2>/dev/null | head -1)"
  else
    echo "CLAUDE_VERSION=not-installed"
  fi

  if command -v opencode >/dev/null 2>&1; then
    echo "OPENCODE_VERSION=$(opencode --version 2>/dev/null | head -1)"
  else
    echo "OPENCODE_VERSION=not-installed"
  fi
}

install_claude
install_opencode
show_versions

echo "NEXT_STEP=python3 scripts/verify_ai_tools.py"
