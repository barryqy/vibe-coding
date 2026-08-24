#!/usr/bin/env bash

set -euo pipefail

expected_commit="${1:-}"
event_branch="${VIBE_EVENT_BRANCH:-event/teil39-1-20260824}"
repo_url="${VIBE_REPO_URL:-https://github.com/barryqy/vibe-coding.git}"
workspace="${VIBE_WORKSPACE:-${HOME}/src}"
repo_path="${workspace}/vibe-coding"
retry_sleep="${VIBE_RETRY_SLEEP:-2}"

if [[ ! "$expected_commit" =~ ^[0-9a-f]{40}$ ]]; then
  printf '%s\n' "The TEIL39-1 event version is invalid. Contact lab support." >&2
  exit 2
fi

fetch_event() {
  local attempt

  for attempt in 1 2 3; do
    if git -C "$repo_path" fetch --depth 1 origin "$event_branch"; then
      return 0
    fi
    if [ "$attempt" -lt 3 ]; then
      sleep "$retry_sleep"
    fi
  done

  return 1
}

mkdir -p "$workspace"

if [ -d "$repo_path/.git" ]; then
  if ! git -C "$repo_path" diff --quiet || ! git -C "$repo_path" diff --cached --quiet; then
    printf '%s\n' "This session already contains dojo work. Start a fresh lab session for TEIL39-1." >&2
    exit 1
  fi
  if ! fetch_event; then
    printf '%s\n' "Could not load the TEIL39-1 event files. Try the play button again." >&2
    exit 1
  fi
elif [ -e "$repo_path" ]; then
  printf '%s\n' "vibe-coding exists but is not a Git checkout; contact lab support." >&2
  exit 1
else
  if ! git clone --depth 1 --branch "$event_branch" "$repo_url" "$repo_path"; then
    printf '%s\n' "Could not download the TEIL39-1 event files. Try the play button again." >&2
    exit 1
  fi
fi

cd "$repo_path"
if ! git checkout --detach "$expected_commit"; then
  printf '%s\n' "The TEIL39-1 event version is unavailable. Contact lab support." >&2
  exit 1
fi
if [ "$(git rev-parse HEAD)" != "$expected_commit" ]; then
  printf '%s\n' "The TEIL39-1 event version could not be verified. Contact lab support." >&2
  exit 1
fi

./scripts/setup_dojo.sh
pwd
