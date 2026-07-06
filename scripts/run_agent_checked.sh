#!/usr/bin/env bash

set -uo pipefail

if [ "$#" -lt 5 ] || [ "$4" != "--" ]; then
  echo "usage: run_agent_checked.sh STATUS_KEY LOG_FILE EXPECTED_REGEX -- COMMAND..." >&2
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

set +e
"$@" >"${log_file}" 2>&1
agent_rc=$?
set -e

scripts/cprint stream <"${log_file}"

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
  report_status "${status_key}=failed"
  return_code="${agent_rc}"
  [ "${return_code}" -ne 0 ] || return_code=1
  exit "${return_code}"
fi

if grep -Eq "${expected_regex}" "${log_file}"; then
  report_status "${status_key}=observed"
  exit 0
fi

report_status "${status_key}=check-output"
