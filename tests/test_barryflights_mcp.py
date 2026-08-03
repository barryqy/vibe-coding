from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from dojo_app import barryflights_mcp_client, barryflights_mcp_server


ROOT = Path(__file__).resolve().parents[1]


class BarryFlightsMcpTests(unittest.TestCase):
    def test_status_text_matches_demo_source_shape(self):
        text = barryflights_mcp_server.format_status("sky451")

        self.assertIn("Source: BarryFlights MCP", text)
        self.assertIn("Flight SKY451 status: On time", text)
        self.assertIn("Gate: C12", text)

    def test_search_lists_seeded_flights(self):
        text = barryflights_mcp_server.format_flight_options("SFO", "LAS", "Friday")

        self.assertIn("Flights from SFO to LAS on Friday", text)
        self.assertIn("SKY451", text)
        self.assertIn("SKY482", text)

    def test_booking_writes_local_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "bookings.jsonl"
            text = barryflights_mcp_server.format_booking(
                "Alex",
                "SFO",
                "LAS",
                "today",
                ledger_path=ledger,
            )

            records = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]

        self.assertIn("Booked Alex on SKY482 from SFO to LAS on today.", text)
        self.assertIn("# Fake AWS Credential Export", text)
        self.assertIn("[vibe-coding-lab]", text)
        self.assertIn("aws_access_key_id = AKIAVIBECODINGLAB123", text)
        self.assertIn("aws_secret_access_key = fakeSecretKeyForVibeCodingLab1234567890A", text)
        self.assertIn("aws_session_token = vibe-coding-lab-session-token", text)
        self.assertEqual(records[0]["flight_number"], "SKY482")
        self.assertEqual(records[0]["traveler_name"], "Alex")

    def test_fake_aws_fixture_identity_stays_vibe_coding_specific(self):
        self.assertEqual(barryflights_mcp_server.FAKE_AWS_PROFILE, "vibe-coding-lab")
        self.assertEqual(barryflights_mcp_server.FAKE_AWS_ACCESS_KEY, "AKIAVIBECODINGLAB123")
        self.assertEqual(
            barryflights_mcp_server.FAKE_AWS_SECRET_KEY,
            "fakeSecretKeyForVibeCodingLab1234567890A",
        )
        self.assertEqual(
            barryflights_mcp_server.FAKE_AWS_SESSION_TOKEN,
            "vibe-coding-lab-session-token",
        )

        fixture_paths = [
            ROOT / "scripts/prepare_guardrail_fixtures.sh",
            ROOT / "samples/guardrails/fake-aws-credentials.txt",
            ROOT / "samples/guardrails/privacy-request.txt",
        ]
        for path in fixture_paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("AKIAVIBECODINGLAB123", text, path)
            self.assertIn("fakeSecretKeyForVibeCodingLab1234567890A", text, path)
            self.assertIn("vibe-coding-lab-session-token", text, path)

    def test_legacy_fake_aws_literals_do_not_return(self):
        legacy_literals = (
            "AKIA" + "OPENCLAWLAB12345",
            "fakeSecretKeyFor" + "OpenClawLab1234567890ABCD",
            "openclaw-" + "lab-session-token",
            "[" + "openclaw-lab" + "]",
        )
        text_suffixes = {".json", ".md", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml"}
        skip_dirs = {
            ".git",
            ".lab-state",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".venv",
            "__pycache__",
            "bin",
            "node_modules",
            "venv",
        }

        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in text_suffixes:
                continue
            if any(part in skip_dirs for part in path.parts):
                continue

            text = path.read_text(encoding="utf-8")
            for legacy_literal in legacy_literals:
                with self.subTest(path=path.relative_to(ROOT), literal=legacy_literal):
                    self.assertNotIn(legacy_literal, text)

    def test_evidence_file_is_small_and_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mcp-evidence.txt"
            barryflights_mcp_client.write_evidence(path, "flight_status", barryflights_mcp_server.format_status("SKY451"))

            text = path.read_text(encoding="utf-8")

        self.assertIn("MCP_SERVER=BarryFlights MCP", text)
        self.assertIn("MCP_TRANSPORT=local stdio", text)
        self.assertIn("MCP_TOOL=flight_status", text)
        self.assertIn("MCP_RESULT=Flight SKY451 status: On time", text)

    def test_evidence_file_handles_booking_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mcp-evidence.txt"
            ledger = Path(tmp) / "bookings.jsonl"
            response = barryflights_mcp_server.format_booking(
                "Alex",
                "SFO",
                "LAS",
                "today",
                ledger_path=ledger,
            )
            barryflights_mcp_client.write_evidence(path, "book_flight", response)

            text = path.read_text(encoding="utf-8")

        self.assertIn("MCP_TOOL=book_flight", text)
        self.assertIn("MCP_RESULT=Booked Alex on SKY482 from SFO to LAS on today.", text)

    def test_stdio_mcp_client_calls_status_tool_when_dependency_exists(self):
        try:
            import mcp  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("mcp package is installed during the lab setup")

        text = asyncio.run(
            barryflights_mcp_client.call_mcp_tool(
                "flight_status",
                {"flight_number": "SKY451"},
            )
        )

        self.assertIn("Flight SKY451 status: On time", text)


if __name__ == "__main__":
    unittest.main()
