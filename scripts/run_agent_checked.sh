#!/usr/bin/env bash

set -uo pipefail

stream_log=1
log_shown=0
evidence_file=""

while [ "${1:-}" = "--capture-only" ] || [ "${1:-}" = "--evidence-file" ]; do
  if [ "$1" = "--capture-only" ]; then
    stream_log=0
    shift
    continue
  fi

  if [ "$#" -lt 2 ]; then
    echo "--evidence-file needs a path" >&2
    exit 2
  fi
  evidence_file="$2"
  shift 2
done

if [ "$#" -lt 5 ] || [ "$4" != "--" ]; then
  echo "usage: run_agent_checked.sh [--capture-only] [--evidence-file FILE] STATUS_KEY LOG_FILE EXPECTED_REGEX -- COMMAND..." >&2
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

if grep -Eiq 'budget exceeded|model budget exhausted|model-budget-exhausted' "${log_file}"; then
  report_status "${status_key}=model-budget-exhausted"
  scripts/cprint yellow "The model budget is exhausted. Continue; the later local scans and guarded block do not need another model answer."
  exit 0
fi

if grep -Eiq 'provider_timeout_error|upstream_timeout|HTTP 504' "${log_file}"; then
  show_log
  report_status "${status_key}=agent-timeout"
  exit 0
fi

if grep -Eiq 'upstream_(provider|status)|provider_status|upstream_http_error' "${log_file}"; then
  show_log
  report_status "${status_key}=provider-error"
  scripts/cprint yellow "The model provider returned an error. Check the adapter log before retrying."
  return_code="${agent_rc}"
  [ "${return_code}" -ne 0 ] || return_code=1
  exit "${return_code}"
fi

if grep -Eiq 'HTTP 429|rate[_ -]?limit|too many requests' "${log_file}"; then
  report_status "${status_key}=rate-limited"
  scripts/cprint yellow "The model route is rate-limited. Do not retry immediately; continue with the local checks."
  exit 0
fi

if [ "${agent_rc}" -eq 124 ]; then
  report_status "${status_key}=agent-timeout"
  exit 0
fi

if grep -Eiq 'ProviderModelNotFound|ModelNotFound|Provider request failed|provider[_ -]?error|provider_(invalid_response|connection_error)|upstream_(invalid_response|connection_error|not_configured)|configuration_error|upstream_http_error|HTTP 5[0-9]{2}' "${log_file}"; then
  show_log
  report_status "${status_key}=provider-error"
  scripts/cprint yellow "The model provider returned an error. Check the adapter log before retrying."
  return_code="${agent_rc}"
  [ "${return_code}" -ne 0 ] || return_code=1
  exit "${return_code}"
fi

if [ "${agent_rc}" -ne 0 ]; then
  show_log
  report_status "${status_key}=failed"
  return_code="${agent_rc}"
  [ "${return_code}" -ne 0 ] || return_code=1
  exit "${return_code}"
fi

check_file="${evidence_file:-${log_file}}"
if [ -f "${check_file}" ] && grep -Eq "${expected_regex}" "${check_file}"; then
  report_status "${status_key}=observed"
  exit 0
fi

show_log
report_status "${status_key}=check-output"
