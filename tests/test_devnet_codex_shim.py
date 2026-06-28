from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
