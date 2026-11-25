"""Tests for Episode 2. No API key: the LLM is a scripted fake.  Run:  pytest -q"""
import json
from types import SimpleNamespace

import pytest

import tools_agent as ta


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


def test_registry_builds_schemas_for_every_tool():
    names = {t.schema()["function"]["name"] for t in ta.REGISTRY.values()}
    assert names == {"get_time", "get_weather", "convert_currency"}
    params = ta.REGISTRY["convert_currency"].parameters
    assert params["required"] == ["amount", "from_currency", "to_currency"]
    assert params["additionalProperties"] is False


@pytest.mark.parametrize("args, problem", [
    ({"city": 42}, "city must be string"),
    ({}, "missing"),
    ({"city": "Tokyo", "unit": "F"}, "unexpected"),
])
def test_check_args_rejects_bad_input(args, problem):
    assert problem in ta.check_args(ta.REGISTRY["get_weather"], args)


def test_enum_and_bool_are_enforced():
    t = ta.REGISTRY["convert_currency"]
    assert "one of" in ta.check_args(t, {"amount": 5, "from_currency": "USD", "to_currency": "BTC"})
    assert "number" in ta.check_args(t, {"amount": True, "from_currency": "USD", "to_currency": "EUR"})


def test_dispatch_never_raises_and_uses_an_envelope():
    assert json.loads(ta.dispatch("get_weather", '{"city": "Tokyo"}')) == {
        "ok": True, "result": {"city": "Tokyo", "temp_c": 18, "conditions": "cloudy"}}
    assert json.loads(ta.dispatch("delete_db", "{}"))["ok"] is False
    assert json.loads(ta.dispatch("get_weather", "not json"))["ok"] is False
    assert "unknown city" in json.loads(ta.dispatch("get_time", '{"city": "Atlantis"}'))["error"]


def test_convert_currency_math():
    assert ta.convert_currency(50, "USD", "JPY") == {"amount": 7550.0, "currency": "JPY"}


def test_parallel_calls_each_get_their_own_tool_message():
    fake = FakeLLM(
        reply(calls=[("get_weather", {"city": "Tokyo"}),
                     ("convert_currency", {"amount": 50, "from_currency": "USD", "to_currency": "JPY"})]),
        reply("Tokyo is 18C and cloudy; 50 USD is 7550 JPY."))
    answer = ta.run("weather and money", client=fake, log=lambda _: None)
    assert answer.startswith("Tokyo is 18C")
    tool_msgs = [m for m in fake.requests[-1]["messages"] if isinstance(m, dict) and m["role"] == "tool"]
    assert [m["tool_call_id"] for m in tool_msgs] == ["call_0", "call_1"]
    assert json.loads(tool_msgs[1]["content"])["result"]["amount"] == 7550.0


def test_all_tools_are_sent_to_the_model():
    fake = FakeLLM(reply("hi"))
    ta.run("hello", client=fake, log=lambda _: None)
    assert len(fake.requests[0]["tools"]) == 3
