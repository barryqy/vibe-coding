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

if ! bash "${repo_root}/scripts/install_dojo_cli.sh"; then
  lab_status "DOJO_CHALLENGES=unavailable"
fi

python_env_ready() {
  [ -x .venv/bin/python ] || return 1
  .venv/bin/python - <<'PY' >/dev/null 2>&1
from importlib.metadata import version


def parts(name: str) -> tuple[int, ...]:
    values = []
    for item in version(name).split("."):
        if not item.isdigit():
            break
        values.append(int(item))
    return tuple(values)


assert (1, 13) <= parts("mcp") < (2,)
assert (2, 31) <= parts("requests") < (3,)
PY
}

if ! python_env_ready; then
  if [ -d .venv ] && [ ! -x .venv/bin/python ]; then
    rm -rf .venv
  fi
  if [ ! -d .venv ]; then
    python3 -m venv .venv
  fi
  .venv/bin/python -m pip install -q -r requirements.txt
fi

if [ ! -f data/tasks.json ]; then
  printf '[]\n' > data/tasks.json
fi

export LAB_REPO_ROOT="${repo_root}"
source "${repo_root}/scripts/lab_session_env.sh"

codex_init_log="${repo_root}/.lab-state/codex-init.log"
if ! {
  python3 scripts/setup_codex_devnet.py
  python3 scripts/start_codex_model_adapter.py
} >"${codex_init_log}" 2>&1; then
  scripts/cprint stream <"${codex_init_log}"
  lab_status "DOJO_INIT=failed"
  exit 1
fi

if [ -x "${HOME}/.local/bin/dojo" ]; then
  "${HOME}/.local/bin/dojo" join
fi
