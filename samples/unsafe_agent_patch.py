"""Intentionally unsafe sample for the lab scanner."""

import subprocess


def run_user_math(user_input: str):
    return eval(user_input)


def shell_helper(path: str):
    return subprocess.run(f"ls {path}", shell=True, check=False, capture_output=True, text=True)

