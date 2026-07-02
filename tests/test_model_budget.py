from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from scripts import devnet_codex_shim, devnet_openai_shim


class ModelBudgetTests(unittest.TestCase):
    def test_default_output_limit_is_small(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(devnet_codex_shim.output_limit(), 512)
            self.assertEqual(devnet_openai_shim.output_limit(), 512)

    def test_output_limit_cannot_exceed_1024(self):
        with patch.dict(os.environ, {"LAB_LLM_MAX_OUTPUT_TOKENS": "9000"}):
            self.assertEqual(devnet_codex_shim.output_limit(), 1024)
            self.assertEqual(devnet_openai_shim.output_limit(), 1024)

    def test_nano_is_the_default_model(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(devnet_codex_shim.route()["model"], "gpt-5-nano")
            self.assertEqual(devnet_openai_shim.route()["model"], "gpt-5-nano")

    def test_adapters_cap_forwarded_output_tokens(self):
        captured = []

        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"choices":[{"message":{"content":"ok"}}]}'

        def fake_urlopen(request, timeout):
            captured.append(json.loads(request.data.decode("utf-8")))
            return Response()

        env = {
            "LLM_BASE_URL": "http://model.test/v1",
            "LLM_API_KEY": "test",
            "LLM_MODEL": "gpt-5-nano",
            "LAB_LLM_MAX_OUTPUT_TOKENS": "512",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                devnet_codex_shim.call_devnet(
                    {"input": "short answer", "max_output_tokens": 9000}
                )
                devnet_openai_shim.call_devnet(
                    {
                        "messages": [{"role": "user", "content": "short answer"}],
                        "max_tokens": 9000,
                    }
                )

        self.assertEqual([body["max_tokens"] for body in captured], [512, 512])


if __name__ == "__main__":
    unittest.main()
