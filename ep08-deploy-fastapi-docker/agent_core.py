"""Episode 8: the agent, with no web framework in it. app.py wraps it in an API.

Keeping the agent free of FastAPI is the same move as keeping business logic out of React
components: you can test it alone and swap the shell later.
"""
from __future__ import annotations

import json
import os
from collections.abc import Iterator
from datetime import datetime
from zoneinfo import ZoneInfo

MODEL = os.environ.get("MODEL", "gpt-4o-mini")
MAX_ROUNDS = 5
MAX_HISTORY = 20            # messages kept per session; old ones drop off

ZONES = {"london": "Europe/London", "tokyo": "Asia/Tokyo", "new york": "America/New_York"}
TOOLS = [{"type": "function", "function": {
    "name": "get_time", "description": "Current local time in a city",
    "parameters": {"type": "object", "properties": {"city": {"type": "string"}},
                   "required": ["city"], "additionalProperties": False}}}]


def make_client():
    from openai import OpenAI
    return OpenAI()


def get_time(city: str) -> str:
    zone = ZONES.get(str(city).lower())
    return datetime.now(ZoneInfo(zone)).strftime("%H:%M") if zone else f"Unknown city: {city}"


def call_tool(name: str, raw: str) -> str:
    try:
        args = json.loads(raw or "{}")
        if name != "get_time" or not isinstance(args.get("city"), str):
            return f"Error: unexpected tool call {name}({raw})"
        return get_time(args["city"])
    except Exception as e:
        return f"Error: {e}"


def answer(history: list[dict], client, model: str = MODEL) -> str:
    """Run the tool loop on a copy of the history; return the final text."""
    messages = list(history)
    for _ in range(MAX_ROUNDS):
        msg = client.chat.completions.create(model=model, messages=messages,
                                             tools=TOOLS).choices[0].message
        if not msg.tool_calls:
            return msg.content or ""
        messages.append(msg)
        for call in msg.tool_calls:
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": call_tool(call.function.name, call.function.arguments)})
    return f"Stopped after {MAX_ROUNDS} tool rounds."


def stream_sse(history: list[dict], client, model: str = MODEL) -> Iterator[str]:
    """Server-Sent Events: one `data:` line per token chunk, then [DONE]. No tools here."""
    stream = client.chat.completions.create(model=model, messages=history, stream=True)
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield f"data: {json.dumps({'token': chunk.choices[0].delta.content})}\n\n"
    yield "data: [DONE]\n\n"


class Sessions:
    """In-memory chat history per session id. Use Redis or a DB once you run 2+ containers."""

    def __init__(self, max_history: int = MAX_HISTORY):
        self.max_history, self.data = max_history, {}

    def history(self, session_id: str) -> list[dict]:
        return list(self.data.get(session_id, []))

    def add(self, session_id: str, role: str, content: str) -> None:
        msgs = self.data.setdefault(session_id, [])
        msgs.append({"role": role, "content": content})
        del msgs[:-self.max_history]
