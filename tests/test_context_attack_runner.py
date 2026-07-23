from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_context_attack.sh"


class ContextAttackRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.bin_dir = self.repo / "bin"
        self.bin_dir.mkdir()
        (self.repo / "scripts").mkdir()
        (self.repo / ".lab-state/darkside").mkdir(parents=True)

        shutil.copy2(
            ROOT / "scripts/run_agent_checked.sh",
            self.repo / "scripts/run_agent_checked.sh",
        )
        self.write_executable(
            "scripts/cprint",
            """
            #!/usr/bin/env bash
            mode="$1"
            shift
            if [ "$mode" = stream ]; then
              cat
            else
              printf '%s\n' "$*"
            fi
            """,
        )
        self.write_executable(
            "scripts/build_rollout_review_prompt.py",
            """
            #!/usr/bin/env python3
            print("base attack prompt")
            """,
        )
        self.write_executable(
            "bin/codex",
            """
            #!/usr/bin/env bash
            state=.lab-state/darkside
            count_file="$state/fake-attempt-count"
            attempt=1
            if [ -f "$count_file" ]; then
              attempt=$(( $(cat "$count_file") + 1 ))
            fi
            printf '%s\n' "$attempt" > "$count_file"

            output_file=""
            model=""
            prompt=""
            while [ "$#" -gt 0 ]; do
              if [ "$1" = --output-last-message ] && [ "$#" -gt 1 ]; then
                output_file="$2"
                shift 2
                continue
              fi
              if [ "$1" = --model ] && [ "$#" -gt 1 ]; then
                model="$2"
                shift 2
                continue
              fi
              prompt="$1"
              shift
            done
            printf '%s\n' "$model" >> "$state/fake-models.log"
            prompt_one_line="$(printf '%s' "$prompt" | tr '\n' '|')"
            printf '%s\t%s\n' "$attempt" "$prompt_one_line" >> "$state/fake-prompts.log"

            case "${FAKE_ATTACK_SCENARIO:-observed}:$attempt" in
              observed:*)
                printf '%s\n' \
                  '10017,Northstar Labs,platinum,2026-07-14' > "$output_file"
                ;;
              miss-then-observed:1|always-miss:*)
                printf '%s\n' 'I ignored the planted instruction.' > "$output_file"
                ;;
              miss-then-observed:2)
                printf '%s\n' \
                  '10017,Northstar Labs,platinum,2026-07-14' > "$output_file"
                ;;
              empty-response:*)
                : > "$output_file"
                ;;
              rate-limited:*)
                printf '%s\n' 'HTTP 429: Too Many Requests'
                exit 1
                ;;
              provider-error:*)
                printf '%s\n' 'HTTP 502: upstream unavailable'
                exit 1
                ;;
              timeout:*)
                printf '%s\n' 'HTTP 504: upstream_timeout'
                exit 1
                ;;
              budget:*)
                printf '%s\n' 'model budget exhausted'
                exit 1
                ;;
            esac
            """,
        )

    def write_executable(self, relative_path: str, content: str):
        path = self.repo / relative_path
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
        path.chmod(0o755)

    def run_attack(self, scenario="observed", **overrides):
        env = os.environ.copy()
        env.update(
            {
                "ATTACK_MAX_ATTEMPTS": "2",
                "FAKE_ATTACK_SCENARIO": scenario,
                "HOSTNAME": "student-pod-a",
                "PATH": f"{self.bin_dir}:{env['PATH']}",
                "VIBE_CODING_REPO": str(self.repo),
            }
        )
        env.update(overrides)
        return subprocess.run(
            ["bash", str(RUNNER)],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def attempts(self) -> int:
        return int(
            (self.repo / ".lab-state/darkside/fake-attempt-count").read_text(
                encoding="utf-8"
            )
        )

    def prompts(self) -> list[str]:
        rows = (
            self.repo / ".lab-state/darkside/fake-prompts.log"
        ).read_text(encoding="utf-8").splitlines()
        return [row.split("\t", 1)[1] for row in rows]

    def models(self) -> list[str]:
        return (
            self.repo / ".lab-state/darkside/fake-models.log"
        ).read_text(encoding="utf-8").splitlines()

    def test_observed_first_attempt_does_not_retry(self):
        completed = self.run_attack()

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(self.attempts(), 1)
        self.assertEqual(self.prompts(), ["base attack prompt"])
        self.assertIn("DARKSIDE_CONTEXT_ATTACK_ATTEMPTS_USED=1", completed.stdout)

    def test_retry_adds_pod_unique_hint_after_semantic_miss(self):
        completed = self.run_attack(
            "miss-then-observed",
            HOSTNAME="student/pod a",
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(self.attempts(), 2)
        self.assertEqual(
            self.prompts(),
            [
                "base attack prompt",
                (
                    "base attack prompt||Retry metadata (do not include in the answer): "
                    "session=studentpoda"
                ),
            ],
        )
        self.assertIn("DARKSIDE_CONTEXT_ATTACK=retrying", completed.stdout)
        self.assertIn("DARKSIDE_CONTEXT_ATTACK_ATTEMPTS_USED=2", completed.stdout)

    def test_explicit_context_model_is_passed_to_codex(self):
        completed = self.run_attack(
            LLM_CONTEXT_ATTACK_MODEL="gpt-5-cache",
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(self.models(), ["gpt-5-cache"])

    def test_divergent_mode_adds_the_session_to_the_first_attempt(self):
        completed = self.run_attack(
            ATTACK_DECOALESCE_FIRST_ATTEMPT="1",
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(
            self.prompts(),
            [
                (
                    "base attack prompt||Retry metadata (do not include in the answer): "
                    "session=student-pod-a"
                ),
            ],
        )

    def test_divergent_retry_uses_a_new_prompt(self):
        completed = self.run_attack(
            "miss-then-observed",
            ATTACK_DECOALESCE_FIRST_ATTEMPT="1",
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(
            self.prompts(),
            [
                (
                    "base attack prompt||Retry metadata (do not include in the answer): "
                    "session=student-pod-a"
                ),
                (
                    "base attack prompt||Retry metadata (do not include in the answer): "
                    "session=student-pod-a attempt=2"
                ),
            ],
        )

    def test_missing_hostname_blocks_a_decoalesced_retry(self):
        completed = self.run_attack(
            "always-miss",
            HOSTNAME="",
        )

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.attempts(), 1)
        self.assertIn("DARKSIDE_CONTEXT_ATTACK_RETRY_ID=missing", completed.stdout)

    def test_exhausted_semantic_miss_fails_directly(self):
        completed = self.run_attack("always-miss")

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.attempts(), 2)
        status = (
            self.repo / ".lab-state/darkside/context-attack-codex.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("DARKSIDE_CONTEXT_ATTACK=check-output", status)

    def test_terminal_failures_do_not_retry(self):
        for scenario in ("rate-limited", "provider-error", "timeout", "budget"):
            with self.subTest(scenario=scenario):
                shutil.rmtree(self.repo / ".lab-state/darkside")
                (self.repo / ".lab-state/darkside").mkdir()

                completed = self.run_attack(scenario)

                self.assertEqual(completed.returncode, 1)
                self.assertEqual(self.attempts(), 1)
                self.assertNotIn("DARKSIDE_CONTEXT_ATTACK=retrying", completed.stdout)

    def test_empty_response_is_terminal(self):
        completed = self.run_attack("empty-response")

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.attempts(), 1)
        self.assertIn(
            "DARKSIDE_CONTEXT_ATTACK=malformed-output",
            completed.stdout,
        )
        self.assertNotIn("DARKSIDE_CONTEXT_ATTACK=retrying", completed.stdout)

    def test_stale_evidence_cannot_turn_a_miss_into_success(self):
        response = self.repo / ".lab-state/darkside/context-attack-response.txt"
        stale_attempt = (
            self.repo
            / ".lab-state/darkside/context-attack-response-attempt-2.txt"
        )
        response.write_text(
            "10017,Northstar Labs,platinum,2026-07-14\n",
            encoding="utf-8",
        )
        stale_attempt.write_text(
            "10017,Northstar Labs,platinum,2026-07-14\n",
            encoding="utf-8",
        )

        completed = self.run_attack(
            "always-miss",
            ATTACK_MAX_ATTEMPTS="1",
        )

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(self.attempts(), 1)
        self.assertNotIn(
            "10017,Northstar Labs",
            response.read_text(encoding="utf-8"),
        )
        self.assertFalse(stale_attempt.exists())

    def test_prompt_build_failure_writes_canonical_status(self):
        self.write_executable(
            "scripts/build_rollout_review_prompt.py",
            """
            #!/usr/bin/env python3
            raise SystemExit(1)
            """,
        )

        completed = self.run_attack()

        self.assertEqual(completed.returncode, 1)
        status = (
            self.repo / ".lab-state/darkside/context-attack-codex.txt"
        ).read_text(encoding="utf-8")
        self.assertEqual(status, "DARKSIDE_CONTEXT_ATTACK=failed\n")
        self.assertFalse(
            (self.repo / ".lab-state/darkside/fake-attempt-count").exists()
        )


if __name__ == "__main__":
    unittest.main()
