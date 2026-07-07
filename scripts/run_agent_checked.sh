#!/usr/bin/env bash

set -uo pipefail

stream_log=1
log_shown=0
if [ "${1:-}" = "--capture-only" ]; then
  stream_log=0
  shift
fi

if [ "$#" -lt 5 ] || [ "$4" != "--" ]; then
  echo "usage: run_agent_checked.sh [--capture-only] STATUS_KEY LOG_FILE EXPECTED_REGEX -- COMMAND..." >&2
  exit 2
fi

status_key="$1"
log_file="$2"
expected_regex="$3"
shift 4

mkdir -p "$(dirname "${log_file}")"

report_status() {
  printf '%s\n' "$1" >>"${log_file}"
  scripts/cprint status "$1"
}

show_log() {
  if [ "${log_shown}" -eq 1 ]; then
    return
  fi
  scripts/cprint stream <"${log_file}"
  log_shown=1
}

set +e
"$@" >"${log_file}" 2>&1
agent_rc=$?
set -e

if [ "${stream_log}" -eq 1 ]; then
  show_log
fi

if grep -Eiq 'budget exceeded|HTTP 429|rate_limit' "${log_file}"; then
  report_status "${status_key}=model-budget-exhausted"
  scripts/cprint yellow "The model budget is exhausted. Continue; the later local scans and guarded block do not need another model answer."
  exit 0
fi

if [ "${agent_rc}" -eq 124 ]; then
  report_status "${status_key}=agent-timeout"
  exit 0
fi

if [ "${agent_rc}" -ne 0 ] || grep -Eiq 'ProviderModelNotFound|ModelNotFound' "${log_file}"; then
  show_log
  report_status "${status_key}=failed"
  return_code="${agent_rc}"
  [ "${return_code}" -ne 0 ] || return_code=1
  exit "${return_code}"
fi

if grep -Eq "${expected_regex}" "${log_file}"; then
  report_status "${status_key}=observed"
  exit 0
fi

show_log
report_status "${status_key}=check-output"
