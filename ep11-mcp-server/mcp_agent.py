"""Episode 11: an agent (the "host") that gets its tools from an MCP server.

    pip install "mcp>=2.3" openai
    set OPENAI_API_KEY, then:  python mcp_agent.py "Am I booked on Thursday? Cancel it."

The loop is Ep01's, the tool format is Ep02's, the confirm step is Ep03's. What's new: the
tools aren't functions in this file any more. We discover them from a server at startup,
and we decide here, in the host, which ones may run without a human yes.
"""
from __future__ import annotations

import asyncio
import json
import os
import secrets
import sys
from collections.abc import Callable
from dataclasses import dataclass, field

from mcp import Client, StdioServerParameters
from mcp.types import CallToolResult, Tool

MODEL = os.environ.get("MODEL", "gpt-4o-mini")
MAX_ROUNDS = 5
# The host's allowlist. A server's readOnlyHint is a hint from code you may not control,
# so only tools we've checked ourselves run without asking.
AUTO_RUN = {"get_opening_hours", "list_bookings"}


def make_client():
    from openai import OpenAI
    return OpenAI()


def to_openai_tool(tool: Tool) -> dict:
    """An MCP tool description -> the Chat Completions tool format from Ep02."""
    return {"type": "function", "function": {
        "name": tool.name,
        "description": tool.description or "",
        "parameters": tool.input_schema}}


def to_envelope(result: CallToolResult) -> dict:
    """An MCP CallToolResult -> Ep02's {ok, result | error} envelope for the model."""
    text = "\n".join(c.text for c in result.content if getattr(c, "type", "") == "text")
    if result.is_error:
        return {"ok": False, "error": text, "hint": "Fix the call, or tell the user what went wrong."}
    structured = result.structured_content or {}
    if structured:
        return {"ok": True, "result": structured.get("result", structured)}
    try:
        return {"ok": True, "result": json.loads(text)}      # a dict sent back as JSON text
    except json.JSONDecodeError:
        return {"ok": True, "result": text}


@dataclass(frozen=True)
class Pending:
    token: str
    tool: str
    args: dict


@dataclass
class McpAgent:
    mcp: Client
    client: object = None
    model: str = MODEL
    tools: list = field(default_factory=list)
    pending: Pending | None = None
    log: Callable[[str], None] = print

    async def load_tools(self) -> list[dict]:
        listed = await self.mcp.list_tools()
        self.tools = [to_openai_tool(t) for t in listed.tools]
        return self.tools

    async def dispatch(self, name: str, raw: str) -> dict:
        known = {t["function"]["name"] for t in self.tools}
        if name not in known:
            return {"ok": False, "error": f"no tool named {name}"}
        try:
            args = json.loads(raw or "{}")
        except json.JSONDecodeError:
            return {"ok": False, "error": "arguments were not valid JSON"}
        if name not in AUTO_RUN:                       # Ep03's guard, now in the host
            self.pending = Pending(secrets.token_urlsafe(8), name, args)
            return {"ok": False, "status": "needs_confirmation",
                    "summary": f"{name}({json.dumps(args)})",
                    "next": "Ask the user to confirm. You cannot confirm it yourself."}
        return to_envelope(await self.mcp.call_tool(name, args))

    async def confirm(self, token: str) -> dict:
        p = self.pending
        if p is None or not secrets.compare_digest(p.token, token):
            return {"ok": False, "error": "nothing to confirm"}
        self.pending = None                            # one use only
        return to_envelope(await self.mcp.call_tool(p.tool, p.args))

    async def ask(self, text: str) -> str:
        if not self.tools:
            await self.load_tools()
        llm = self.client or make_client()
        messages: list = [
            {"role": "system", "content": "You help a patient with clinic bookings. Use the tools."},
            {"role": "user", "content": text}]
        for _ in range(MAX_ROUNDS):
            msg = llm.chat.completions.create(
                model=self.model, messages=messages, tools=self.tools).choices[0].message
            if not msg.tool_calls:
                return msg.content
            messages.append(msg)
            for call in msg.tool_calls:
                result = await self.dispatch(call.function.name, call.function.arguments)
                self.log(f"  mcp call: {call.function.name}({call.function.arguments}) -> {result}")
                messages.append({"role": "tool", "tool_call_id": call.id,
                                 "content": json.dumps(result)})
        return f"Stopped after {MAX_ROUNDS} tool rounds."


def server_params(user: str | None = None) -> StdioServerParameters:
    user = user or os.environ.get("CLINIC_USER", "sara")      # who is using this host
    here = os.path.dirname(os.path.abspath(__file__))
    return StdioServerParameters(command=sys.executable,
                                 args=[os.path.join(here, "clinic_server.py")],
                                 env={**os.environ, "CLINIC_USER": user})


async def main(question: str) -> None:
    async with Client(server_params()) as mcp:
        agent = McpAgent(mcp)
        names = [t["function"]["name"] for t in await agent.load_tools()]
        print(f"tools from the server: {', '.join(names)}")
        print(await agent.ask(question))
        if agent.pending:
            answer = input(f"\n[confirm] {agent.pending.tool}({agent.pending.args})? (yes/no) ")
            if answer.strip().lower() == "yes":
                print(await agent.confirm(agent.pending.token))
            else:
                agent.pending = None
                print("Okay, nothing was changed.")


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "Am I booked on Thursday? If so, cancel it."))
