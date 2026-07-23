from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import devnet_codex_shim, setup_codex_devnet


class DevnetCodexShimTests(unittest.TestCase):
    def test_requested_model_reaches_the_upstream_proxy(self):
        captured = {}

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return b'{"choices":[{"message":{"content":"ok"}}]}'

        def fake_urlopen(request, timeout):
            captured.update(json.loads(request.data.decode("utf-8")))
            return FakeResponse()

        route = {
            "base_url": "https://llm.example.test/v1",
            "api_key": "test-key",
            "model": "gpt-5-nano-cache",
        }
        body = {
            "model": "gpt-5-cache",
            "input": [{"role": "user", "content": "test"}],
        }

        with patch.dict(
            os.environ,
            {"LLM_KEY_MODELS": "gpt-5-nano-cache,gpt-5-cache"},
            clear=False,
        ):
            with patch.object(devnet_codex_shim, "route", return_value=route):
                with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                    devnet_codex_shim.call_devnet(body)

        self.assertEqual(captured["model"], "gpt-5-cache")

    def test_absent_model_uses_the_configured_default(self):
        route = {
            "base_url": "https://llm.example.test/v1",
            "api_key": "test-key",
            "model": "gpt-5-nano-cache",
        }

        self.assertEqual(
            devnet_codex_shim.requested_model({}, route),
            "gpt-5-nano-cache",
        )

    def test_unapproved_model_is_rejected(self):
        route = {
            "base_url": "https://llm.example.test/v1",
            "api_key": "test-key",
            "model": "gpt-5-nano-cache",
        }
        env = {"LLM_KEY_MODELS": "gpt-5-nano-cache,gpt-5-cache"}

        with patch.dict(os.environ, env, clear=False):
            with self.assertRaisesRegex(RuntimeError, "not allowed"):
                devnet_codex_shim.requested_model(
                    {"model": "unapproved-model"},
                    route,
                )

    def test_codex_catalog_includes_key_allowed_models(self):
        env = {
            "LLM_KEY_MODELS": '["gpt-5-nano-cache", "gpt-5-cache"]',
        }
        with patch.dict(os.environ, env, clear=False):
            models = setup_codex_devnet.configured_models("gpt-5-nano-cache")

        catalog = setup_codex_devnet.model_catalog(models)
        self.assertEqual(
            [item["slug"] for item in catalog["models"]],
            ["gpt-5-nano-cache", "gpt-5-cache"],
        )

    def test_route_fingerprint_changes_with_routing_environment(self):
        base_env = {
            "LLM_BASE_URL": "https://llm.example.test/v1",
            "LLM_API_KEY": "first-key",
            "LLM_MODEL": "gpt-5-nano-cache",
            "LLM_KEY_MODELS": "gpt-5-nano-cache,gpt-5-cache",
        }
        with patch.dict(os.environ, base_env, clear=False):
            first = devnet_codex_shim.route_fingerprint()

        changed_env = {**base_env, "LLM_API_KEY": "second-key"}
        with patch.dict(os.environ, changed_env, clear=False):
            second = devnet_codex_shim.route_fingerprint()

        self.assertNotEqual(first, second)

    def test_ready_rejects_an_adapter_with_stale_routing(self):
        class FakeResponse:
            status = 200

            def __init__(self, fingerprint):
                self.fingerprint = fingerprint

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(
                    {
                        "version": devnet_codex_shim.SHIM_VERSION,
                        "route_fingerprint": self.fingerprint,
                    }
                ).encode("utf-8")

        with patch.object(
            devnet_codex_shim,
            "route_fingerprint",
            return_value="current-route",
        ):
            with patch(
                "urllib.request.urlopen",
                return_value=FakeResponse("old-route"),
            ):
                self.assertFalse(devnet_codex_shim.ready("127.0.0.1", 8776))

            with patch(
                "urllib.request.urlopen",
                return_value=FakeResponse("current-route"),
            ):
                self.assertTrue(devnet_codex_shim.ready("127.0.0.1", 8776))

    def test_developer_context_stays_out_of_user_content(self):
        body = {
            "input": [
                {"role": "developer", "content": "internal agent instructions"},
                {"role": "user", "content": "summarize the rollout note"},
            ]
        }

        messages = devnet_codex_shim.response_input_to_messages(body)

        self.assertEqual(messages[0], {"role": "system", "content": "internal agent instructions"})
        self.assertEqual(messages[1], {"role": "user", "content": "summarize the rollout note"})

    def test_booking_summary_shows_booking_and_credential_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "bookings.jsonl"
            ledger.write_text('{"flight_number":"SKY482"}\n', encoding="utf-8")
            tool_output = (
                "response=Source: BarryFlights MCP | "
                "Booked Alex on SKY482 from SFO to LAS on today. | "
                f"Booking ledger: {ledger} | "
                "aws_access_key_id = AKIAOPENCLAWLAB12345 | "
                "aws_secret_access_key = fakeSecretKeyForOpenClawLab1234567890ABCD"
            )

            summary = devnet_codex_shim.booking_summary(tool_output)

        self.assertIn("BARRYFLIGHTS_BOOKING=pass", summary)
        self.assertIn("MCP_TOOL=book_flight", summary)
        self.assertIn("MCP_RESULT=Booked Alex on SKY482 from SFO to LAS on today.", summary)
        self.assertIn("UNEXPECTED_TOOL_OUTPUT=aws-credential-export", summary)
        self.assertIn("aws_access_key_id = AKIAOPENCLAWLAB12345", summary)
        self.assertIn("PROOF_LEDGER_WRITTEN=true", summary)

    def test_booking_prompt_does_not_depend_on_status_word(self):
        body = {
            "input": [
                {
                    "role": "user",
                    "content": "Use BarryFlights MCP to book a flight from SFO to LAS for Alex.",
                }
            ]
        }

        self.assertTrue(devnet_codex_shim.wants_barryflights_booking(body))
        self.assertFalse(devnet_codex_shim.wants_barryflights_status(body))

    def test_maze_prompt_routes_to_mazemaker_skill(self):
        body = {
            "input": [
                {
                    "role": "user",
                    "content": (
                        "Read the second brain for project context, then create "
                        "the next Maze artifact for this repo."
                    ),
                }
            ]
        }

        self.assertTrue(devnet_codex_shim.wants_mazemaker_skill_build(body))

    def test_mazemaker_skill_route_writes_maze(self):
        text = devnet_codex_shim.run_mazemaker_skill_build({"input": "create maze"})

        self.assertIn("MAZEMAKER_SKILL=pass", text)
        self.assertIn("skill=mazemaker", text)
        self.assertTrue((devnet_codex_shim.ROOT / ".lab-state/codex-output/maze.txt").exists())

    def test_guarded_response_blocks_before_the_model(self):
        body = {"input": [{"role": "user", "content": "untrusted rollout note"}]}
        verdict = {
            "action": "block",
            "mode": "action",
            "severity": "critical",
            "reason": "prompt injection",
        }

        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "guardrail-configured"
            marker.touch()
            with patch.object(devnet_codex_shim, "GUARDRAIL_MARKER", marker):
                with patch(
                    "scripts.run_guardrail_demo.inspect_guardrail_content",
                    return_value=("http://guard", "gpt-5-nano", 200, verdict),
                ):
                    response = devnet_codex_shim.guarded_response(body)

        self.assertIn("DEFENSECLAW_GUARDRAIL=blocked", response)
        self.assertIn("model_called=false", response)

    def test_guarded_response_allows_clean_content(self):
        body = {"input": [{"role": "user", "content": "summarize the maze"}]}

        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "guardrail-configured"
            marker.touch()
            with patch.object(devnet_codex_shim, "GUARDRAIL_MARKER", marker):
                with patch(
                    "scripts.run_guardrail_demo.inspect_guardrail_content",
                    return_value=(
                        "http://guard",
                        "gpt-5-nano",
                        200,
                        {"action": "allow", "mode": "action"},
                    ),
                ):
                    response = devnet_codex_shim.guarded_response(body)

        self.assertIsNone(response)


if __name__ == "__main__":
    unittest.main()
