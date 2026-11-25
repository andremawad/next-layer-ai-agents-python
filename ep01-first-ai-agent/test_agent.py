"""Tests for Episode 1. No API key and no network: the LLM is a fake.

Run:  pytest -q
agent.py creates its OpenAI client at import time, so we put a stub `openai`
module in sys.modules first. (Frontend parallel: mocking `fetch` before the
component under test is imported.)
"""
import json
import re
import sys
import types
from types import SimpleNamespace

import pytest


class FakeLLM:
    """Plays back scripted assistant messages and records every request."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=self.replies.pop(0))])


def reply(content=None, calls=()):
    tool_calls = [
        SimpleNamespace(id=f"call_{i}", type="function",
                        function=SimpleNamespace(name=name, arguments=json.dumps(args)))
        for i, (name, args) in enumerate(calls)
    ]
    return SimpleNamespace(role="assistant", content=content, tool_calls=tool_calls or None)


@pytest.fixture
def agent(monkeypatch):
    stub = types.ModuleType("openai")
    stub.OpenAI = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "openai", stub)
    monkeypatch.delitem(sys.modules, "agent", raising=False)
    import agent as module
    return module


def test_get_time_known_city_returns_hh_mm(agent):
    assert re.fullmatch(r"\d\d:\d\d", agent.get_time("Tokyo"))


def test_get_time_unknown_city_returns_message_not_exception(agent):
    assert agent.get_time("Atlantis") == "Unknown city: Atlantis"


def test_loop_runs_tool_then_returns_answer(agent, monkeypatch):
    fake = FakeLLM(reply(calls=[("get_time", {"city": "Tokyo"})]), reply("It's 21:04 in Tokyo."))
    monkeypatch.setattr(agent, "client", fake)
    assert agent.run("What time is it in Tokyo?") == "It's 21:04 in Tokyo."
    second = fake.requests[1]["messages"]
    tool_msg = second[-1]
    assert tool_msg["role"] == "tool" and tool_msg["tool_call_id"] == "call_0"


def test_loop_stops_after_five_rounds(agent, monkeypatch):
    stuck = [reply(calls=[("get_time", {"city": "Tokyo"})]) for _ in range(5)]
    monkeypatch.setattr(agent, "client", FakeLLM(*stuck))
    assert agent.run("loop forever") == "Stopped after 5 tool rounds."


def test_bad_arguments_are_returned_as_errors(agent):
    call = SimpleNamespace(function=SimpleNamespace(name="get_time", arguments='{"city": 42}'))
    assert agent.call_tool(call).startswith("Error:")
