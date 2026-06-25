from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from dojo_app import barryflights_mcp_client, barryflights_mcp_server


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

    def test_evidence_file_is_small_and_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mcp-evidence.txt"
            barryflights_mcp_client.write_evidence(path, "flight_status", barryflights_mcp_server.format_status("SKY451"))

            text = path.read_text(encoding="utf-8")

        self.assertIn("MCP_SERVER=BarryFlights MCP", text)
        self.assertIn("MCP_TRANSPORT=local stdio", text)
        self.assertIn("MCP_TOOL=flight_status", text)
        self.assertIn("MCP_RESULT=Flight SKY451 status: On time", text)

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
