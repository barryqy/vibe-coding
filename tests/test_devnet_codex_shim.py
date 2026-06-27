from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dojo_app import tictactoe_game
from scripts import devnet_codex_shim


class DevnetCodexShimTests(unittest.TestCase):
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
        self.assertIn("OOPS_EXTRA_OUTPUT=aws-credential-export", summary)
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

    def test_tictactoe_prompt_routes_to_scenario(self):
        body = {
            "input": [
                {
                    "role": "user",
                    "content": (
                        "Read the second brain for project context, then create "
                        "one tic-tac-toe scenario for this repo."
                    ),
                }
            ]
        }

        self.assertTrue(devnet_codex_shim.wants_tictactoe_scenario(body))

    def test_project_note_prompt_does_not_route_to_scenario(self):
        body = {
            "input": [
                {
                    "role": "user",
                    "content": (
                        "Write the content for .second-brain/projects/vibe-coding-dojo.md. "
                        "Tic-tac-toe scenario requests should follow "
                        ".second-brain/patterns/tictactoe-scenario.md."
                    ),
                }
            ]
        }

        self.assertFalse(devnet_codex_shim.wants_tictactoe_scenario(body))

    def test_tictactoe_scenario_text_is_checkable(self):
        text = devnet_codex_shim.tictactoe_scenario_text()
        scenario = tictactoe_game.parse_scenario(text)

        self.assertIn("MODE: human-vs-computer", text)
        self.assertIn("NEXT: X", text)
        self.assertIn("BOARD:", text)
        self.assertEqual(scenario.board, tuple("........."))


if __name__ == "__main__":
    unittest.main()
