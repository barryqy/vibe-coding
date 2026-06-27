from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import model_usage  # noqa: E402


class ModelUsageTests(unittest.TestCase):
    def test_records_chat_completion_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usage.json"
            old = os.environ.get("VIBE_USAGE_FILE")
            os.environ["VIBE_USAGE_FILE"] = str(path)
            try:
                model_usage.record_model_response(
                    "opencode",
                    "gpt-4o",
                    {
                        "usage": {
                            "prompt_tokens": 12,
                            "completion_tokens": 5,
                            "total_tokens": 17,
                        }
                    },
                )
                state = model_usage.read_state(path)
            finally:
                if old is None:
                    os.environ.pop("VIBE_USAGE_FILE", None)
                else:
                    os.environ["VIBE_USAGE_FILE"] = old

        self.assertEqual(state["calls"], 1)
        self.assertEqual(state["input_tokens"], 12)
        self.assertEqual(state["output_tokens"], 5)
        self.assertEqual(state["total_tokens"], 17)
        self.assertEqual(state["tools"]["opencode"]["calls"], 1)

    def test_records_gateway_budget_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usage.json"
            old = os.environ.get("VIBE_USAGE_FILE")
            os.environ["VIBE_USAGE_FILE"] = str(path)
            try:
                model_usage.record_model_error(
                    "codex",
                    "gpt-4o",
                    "HTTP 429: budget exceeded: spent $0.5383 of $0.5000",
                )
                state = model_usage.read_state(path)
            finally:
                if old is None:
                    os.environ.pop("VIBE_USAGE_FILE", None)
                else:
                    os.environ["VIBE_USAGE_FILE"] = old

        self.assertEqual(state["errors"], 1)
        self.assertEqual(state["budget"]["source"], "gateway")
        self.assertEqual(state["budget"]["spent_usd"], 0.5383)
        self.assertEqual(state["budget"]["limit_usd"], 0.5)
        self.assertEqual(state["budget"]["remaining_usd"], 0.0)

    def test_prints_not_reported_without_gateway_budget(self):
        state = model_usage.blank_state()
        state["calls"] = 1
        state["input_tokens"] = 10
        state["output_tokens"] = 3
        state["total_tokens"] = 13

        output = io.StringIO()
        with redirect_stdout(output):
            rc = model_usage.print_usage(state)

        self.assertEqual(rc, 0)
        text = output.getvalue()
        self.assertIn("MODEL_USAGE=ok", text)
        self.assertIn("budget_source=not-reported", text)
        self.assertIn("budget_remaining=unknown", text)


if __name__ == "__main__":
    unittest.main()
