"""Tests for Episode 11. No API key, no subprocess: the server runs in-process.  Run:  pytest -q"""
import json
from types import SimpleNamespace

import pytest
from mcp import Client

from clinic_server import demo_bookings, make_server
from mcp_agent import McpAgent, server_params, to_openai_tool


@pytest.fixture
def anyio_backend():
    return "asyncio"


class FakeLLM:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=self.replies.pop(0))])


def reply(content=None, calls=()):
    tool_calls = [SimpleNamespace(id=f"call_{i}", type="function",
                                  function=SimpleNamespace(name=n, arguments=json.dumps(a)))
                  for i, (n, a) in enumerate(calls)]
    return SimpleNamespace(role="assistant", content=content, tool_calls=tool_calls or None)


def tool_results(llm):
    """The tool messages the agent sent back to the model in its last request."""
    return [json.loads(m["content"]) for m in llm.requests[-1]["messages"]
            if isinstance(m, dict) and m.get("role") == "tool"]


@pytest.mark.anyio
async def test_server_tools_become_openai_tools():
    async with Client(make_server()) as mcp:
        tools = [to_openai_tool(t) for t in (await mcp.list_tools()).tools]
    by_name = {t["function"]["name"]: t for t in tools}
    assert set(by_name) == {"get_opening_hours", "list_bookings", "cancel_booking"}
    hours = by_name["get_opening_hours"]
    assert hours["type"] == "function"
    assert hours["function"]["parameters"]["required"] == ["day"]
    assert "weekday" in hours["function"]["description"]


@pytest.mark.anyio
async def test_read_only_tool_runs_through_mcp():
    llm = FakeLLM(reply(calls=[("get_opening_hours", {"day": "Sunday"})]),
                  reply("We're closed on Sundays."))
    async with Client(make_server()) as mcp:
        agent = McpAgent(mcp, client=llm, log=lambda _: None)
        assert await agent.ask("open sunday?") == "We're closed on Sundays."
    assert tool_results(llm) == [{"ok": True, "result": "closed"}]


@pytest.mark.anyio
async def test_destructive_tool_waits_for_a_human():
    data = demo_bookings()
    llm = FakeLLM(reply(calls=[("cancel_booking", {"booking_id": "B-102"})]), reply("Confirm?"))
    async with Client(make_server(data)) as mcp:
        agent = McpAgent(mcp, client=llm, log=lambda _: None)
        await agent.ask("cancel thursday")
        assert "B-102" in data and agent.pending is not None        # nothing deleted yet
        assert tool_results(llm)[0]["status"] == "needs_confirmation"
        token = agent.pending.token
        done = await agent.confirm(token)
        assert done["ok"] and "B-102" not in data
        assert (await agent.confirm(token))["ok"] is False          # single use


@pytest.mark.anyio
async def test_server_still_checks_ownership():
    data = demo_bookings()
    async with Client(make_server(data)) as mcp:
        result = await mcp.call_tool("cancel_booking", {"booking_id": "B-201"})  # adam's
    assert result.is_error and "B-201" in data
    assert "no booking B-201" in result.content[0].text      # a ToolError message gets through


@pytest.mark.anyio
async def test_bad_arguments_come_back_as_an_error_envelope():
    llm = FakeLLM(reply(calls=[("get_opening_hours", {"dayz": "sunday"})]), reply("Sorry."))
    async with Client(make_server()) as mcp:
        await McpAgent(mcp, client=llm, log=lambda _: None).ask("hours?")
    result = tool_results(llm)[0]
    assert result["ok"] is False and "day" in result["error"] and result["hint"]


@pytest.mark.anyio
async def test_unknown_tool_is_never_sent_to_the_server():
    llm = FakeLLM(reply(calls=[("delete_everything", {})]), reply("I can't do that."))
    async with Client(make_server()) as mcp:
        await McpAgent(mcp, client=llm, log=lambda _: None).ask("delete all")
    assert tool_results(llm) == [{"ok": False, "error": "no tool named delete_everything"}]


@pytest.mark.anyio
async def test_policy_resource_is_readable():
    async with Client(make_server()) as mcp:
        res = await mcp.read_resource("clinic://policy")
    assert "$50" in res.contents[0].text


def test_server_user_comes_from_the_host_environment(monkeypatch):
    monkeypatch.setenv("CLINIC_USER", "adam")
    assert server_params().env["CLINIC_USER"] == "adam"
    assert server_params("sara").env["CLINIC_USER"] == "sara"
