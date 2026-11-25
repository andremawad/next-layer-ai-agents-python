"""Episode 11: an MCP server for the clinic tools (fake data).

    pip install "mcp>=2.3"
    python clinic_server.py          # speaks MCP over stdin/stdout; a host starts it for you

Any MCP host (our mcp_agent.py, an IDE, a desktop chat app) can now discover and call these
tools without knowing they're Python. Frontend version: this is an API with its own OpenAPI
spec, and MCP is the standard plug every client already understands.
"""
from __future__ import annotations

import os

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

HOURS = {"sunday": "closed", "saturday": "10:00-14:00"}
POLICY = "Same-day cancellations cost $50. Cancel the day before and it's free."


def demo_bookings() -> dict[str, dict]:
    return {
        "B-101": {"owner": "sara", "when": "Tue 10:00", "doctor": "Dr. Lina"},
        "B-102": {"owner": "sara", "when": "Thu 16:30", "doctor": "Dr. Omar"},
        "B-201": {"owner": "adam", "when": "Wed 09:00", "doctor": "Dr. Lina"},
    }


def current_user() -> str:
    # Who the user is comes from how the server was started, never from a tool argument.
    return os.environ.get("CLINIC_USER", "sara")


def make_server(bookings: dict[str, dict] | None = None) -> MCPServer:
    data = demo_bookings() if bookings is None else bookings
    server = MCPServer("clinic", instructions="Tools for one patient's clinic bookings.",
                       log_level="WARNING")   # stdout is the protocol; keep stderr quiet too

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def get_opening_hours(day: str) -> str:
        """Opening hours for one weekday, for example 'sunday'."""
        return HOURS.get(day.strip().lower(), "09:00-17:00")

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def list_bookings() -> dict:
        """List the current patient's bookings."""
        return {k: v for k, v in data.items() if v["owner"] == current_user()}

    @server.tool(annotations=ToolAnnotations(destructiveHint=True))
    def cancel_booking(booking_id: str) -> str:
        """Cancel one of the current patient's bookings. Hosts should ask the user first."""
        booking = data.get(booking_id)
        if booking is None or booking["owner"] != current_user():   # authorization, in code
            raise ToolError(f"no booking {booking_id} for this patient")   # message reaches the model
        del data[booking_id]
        return f"Cancelled {booking_id}: {booking['when']} with {booking['doctor']}"

    @server.resource("clinic://policy")
    def cancellation_policy() -> str:
        """The clinic's cancellation policy."""
        return POLICY

    return server


mcp = make_server()

if __name__ == "__main__":
    mcp.run()          # stdio by default
