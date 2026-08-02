from __future__ import annotations

import unittest

from scripts.devnet_model_route import upstream_model


class DevnetModelRouteTests(unittest.TestCase):
    def test_production_cache_aliases_use_supported_models(self):
        base_url = "https://devnet.cisco.com/v1/llmproxy"

        self.assertEqual(upstream_model(base_url, "gpt-5-nano-cache"), "gpt-5-nano")
        self.assertEqual(upstream_model(base_url, "gpt-5-cache"), "gpt-5")

    def test_production_url_allows_a_trailing_slash(self):
        self.assertEqual(
            upstream_model(
                "https://devnet.cisco.com/v1/llmproxy/",
                "gpt-5-nano-cache",
            ),
            "gpt-5-nano",
        )

    def test_staging_keeps_cache_aliases(self):
        base_url = "https://devnet-testing.cisco.com/v1/llmproxy"

        self.assertEqual(
            upstream_model(base_url, "gpt-5-nano-cache"),
            "gpt-5-nano-cache",
        )
        self.assertEqual(upstream_model(base_url, "gpt-5-cache"), "gpt-5-cache")

    def test_lookalike_production_url_is_not_rewritten(self):
        self.assertEqual(
            upstream_model(
                "https://devnet.cisco.com.example/v1/llmproxy",
                "gpt-5-nano-cache",
            ),
            "gpt-5-nano-cache",
        )

    def test_supported_models_are_unchanged(self):
        base_url = "https://devnet.cisco.com/v1/llmproxy"

        self.assertEqual(upstream_model(base_url, "gpt-5-nano"), "gpt-5-nano")
        self.assertEqual(upstream_model(base_url, "gpt-5"), "gpt-5")


if __name__ == "__main__":
    unittest.main()
