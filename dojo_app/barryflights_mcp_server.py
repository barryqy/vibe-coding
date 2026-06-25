"""Local dojo version of the BarryFlights MCP demo used by dev.aidefense.cisco.com."""

from __future__ import annotations

import os
import logging


MCP_SERVER_NAME = "BarryFlights MCP"
STATUS_BY_FLIGHT = {
    "SKY451": ("On time", "C12", "08:15"),
    "SKY482": ("Boarding", "A6", "12:40"),
    "SKY509": ("Delayed 25m", "B9", "18:10"),
}
FLIGHTS = [
    {"flight_number": "SKY451", "depart": "08:15", "arrive": "10:32", "stops": "Nonstop", "price": "$249"},
    {"flight_number": "SKY482", "depart": "12:40", "arrive": "15:05", "stops": "Nonstop", "price": "$279"},
    {"flight_number": "SKY509", "depart": "18:10", "arrive": "20:44", "stops": "1 stop", "price": "$221"},
]

SEARCH_DESCRIPTION = "SkyBridge flight search. Search available flights for a traveler."
BOOK_DESCRIPTION = "SkyBridge booking tool. Reserve a demo flight and return a confirmation."
STATUS_DESCRIPTION = "SkyBridge flight status lookup. Return the current status, gate, and departure time for a flight number."


def format_flight_options(origin: str, destination: str, date: str) -> str:
    lines = [f"Source: {MCP_SERVER_NAME}", f"Flights from {origin} to {destination} on {date}:"]
    for flight in FLIGHTS:
        lines.append(
            f"- {flight['flight_number']} | depart {flight['depart']} | "
            f"arrive {flight['arrive']} | {flight['stops']} | {flight['price']}"
        )
    return "\n".join(lines)


def format_booking_confirmation(traveler_name: str, origin: str, destination: str, date: str) -> str:
    flight = FLIGHTS[1]
    name = traveler_name.strip() or "Demo Traveler"
    return (
        f"Source: {MCP_SERVER_NAME}\n"
        f"Booked demo hold for {name} on {flight['flight_number']} from {origin} to {destination} on {date}.\n"
        f"Departure: {flight['depart']} | Arrival: {flight['arrive']} | Price: {flight['price']}"
    )


def format_status(flight_number: str) -> str:
    normalized = (flight_number or "").strip().upper()
    status, gate, depart = STATUS_BY_FLIGHT.get(normalized, ("Scheduled", "TBD", "09:00"))
    return (
        f"Source: {MCP_SERVER_NAME}\n"
        f"Flight {normalized or 'UNKNOWN'} status: {status}\n"
        f"Gate: {gate}\n"
        f"Departure: {depart}"
    )


def build_mcp():
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(MCP_SERVER_NAME)

    @mcp.tool(name="search_flights", description=SEARCH_DESCRIPTION)
    def search_flights(origin: str, destination: str, date: str, traveler_name: str = "") -> str:
        return format_flight_options(origin, destination, date)

    @mcp.tool(name="book_flight", description=BOOK_DESCRIPTION)
    def book_flight(traveler_name: str, origin: str, destination: str, date: str) -> str:
        return format_booking_confirmation(traveler_name, origin, destination, date)

    @mcp.tool(name="flight_status", description=STATUS_DESCRIPTION)
    def flight_status(flight_number: str) -> str:
        return format_status(flight_number)

    return mcp


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("mcp").setLevel(logging.WARNING)
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower() or "stdio"
    if transport != "stdio":
        raise SystemExit("This dojo MCP server supports stdio for the lab.")
    build_mcp().run("stdio")


if __name__ == "__main__":
    main()
