# Episode 11: MCP Explained: Build an MCP Server in Python for Your AI Agent

The clinic tools (fake data) move into an MCP server, and the agent becomes an MCP host that
discovers them at startup. The host still asks a human before anything that isn't on its own
allowlist, and the server still checks who's asking. Uses the official MCP Python SDK **v2**
(`MCPServer`; older tutorials call it `FastMCP`, which is the v1 name).

Video: TBD (the link is added when the episode is published)

Part of the course [AI Engineering: Build Real AI Agents in Python](../README.md) on [Next Layer](https://www.youtube.com/@NextLayerEng).

```bash
# one-time setup from the repo root: uv sync   (see ../README.md)
export OPENAI_API_KEY=...        # Windows PowerShell: $env:OPENAI_API_KEY="..."
uv run python mcp_agent.py "Am I booked on Thursday? If so, cancel it."
```

You don't start `clinic_server.py` yourself: the host launches it as a subprocess and talks to it
over stdin/stdout. To act as another patient: `CLINIC_USER=adam uv run python mcp_agent.py "Cancel B-102"`
(PowerShell: `$env:CLINIC_USER="adam"`).

Example session (the model's wording will differ):

```text
tools from the server: get_opening_hours, list_bookings, cancel_booking
  mcp call: list_bookings({}) -> {'ok': True, 'result': {'B-101': {...}, 'B-102': {...}}}
  mcp call: cancel_booking({"booking_id":"B-102"}) -> {'ok': False, 'status': 'needs_confirmation', ...}
You're booked Thursday at 16:30 with Dr. Omar. I've prepared the cancellation. Please confirm.

[confirm] cancel_booking({'booking_id': 'B-102'})? (yes/no) yes
{'ok': True, 'result': 'Cancelled B-102: Thu 16:30 with Dr. Omar'}
```

## Tests (no API key, no subprocess)

```bash
uv run pytest -q                 # pip: pytest -q (with the venv active)
```

`Client(make_server())` connects to the server in-process; the async tests use the `anyio` pytest
plugin that comes with the SDK.

| Frontend idea | Here |
|---|---|
| an API that ships its own OpenAPI spec | `list_tools` returns names, descriptions and JSON schemas |
| a client calling an endpoint | `call_tool(name, args)` |
| never trust the client | the server checks ownership; identity comes from the environment |
| never trust a third-party script | the host's `AUTO_RUN` allowlist, not the server's `readOnlyHint` |

Exercises and quiz: [exercises.md](exercises.md), [quiz.md](quiz.md). Next: structured outputs.
