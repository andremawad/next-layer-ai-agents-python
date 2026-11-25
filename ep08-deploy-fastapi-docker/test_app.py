"""Tests for Episode 8. No API key: the LLM is a fake.  Run:  pytest -q

agent_core tests always run. The HTTP tests need fastapi + httpx installed
(pip install -r requirements.txt) and are skipped otherwise.
"""
import json
from types import SimpleNamespace

import pytest

import agent_core


class FakeLLM:
    def __init__(self, *replies, tokens=("Hel", "lo")):
        self.replies, self.tokens = list(replies), tokens
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, stream=False, **kwargs):
        if stream:
            return iter(SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=t))])
                        for t in self.tokens)
        return SimpleNamespace(choices=[SimpleNamespace(message=self.replies.pop(0))])


def text(content):
    return SimpleNamespace(role="assistant", content=content, tool_calls=None)


def tool_call(city):
    return SimpleNamespace(role="assistant", content=None, tool_calls=[SimpleNamespace(
        id="c1", function=SimpleNamespace(name="get_time", arguments=json.dumps({"city": city})))])


# ---------------------------------------------------------------- core (always runs)
def test_answer_runs_the_tool_loop():
    assert agent_core.answer([{"role": "user", "content": "t?"}],
                             FakeLLM(tool_call("Tokyo"), text("It's late."))) == "It's late."


def test_bad_tool_args_become_errors():
    assert agent_core.call_tool("get_time", '{"city": 1}').startswith("Error")
    assert agent_core.call_tool("rm_rf", "{}").startswith("Error")


def test_sse_format():
    events = list(agent_core.stream_sse([], FakeLLM()))
    assert events == ['data: {"token": "Hel"}\n\n', 'data: {"token": "lo"}\n\n', "data: [DONE]\n\n"]


def test_sessions_keep_only_recent_messages():
    s = agent_core.Sessions(max_history=3)
    for i in range(5):
        s.add("a", "user", str(i))
    assert [m["content"] for m in s.history("a")] == ["2", "3", "4"] and s.history("b") == []


# ---------------------------------------------------------------- HTTP layer (needs fastapi)
@pytest.fixture
def client():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    import app as app_module
    fake = FakeLLM(text("Hi there."), text("Second answer."))
    app_module.app.dependency_overrides[app_module.get_llm] = lambda: fake
    app_module.sessions.data.clear()
    yield TestClient(app_module.app)
    app_module.app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_chat_remembers_the_session(client):
    r = client.post("/chat", json={"message": "hello", "session_id": "s1"})
    assert r.status_code == 200 and r.json() == {"answer": "Hi there.", "session_id": "s1"}
    client.post("/chat", json={"message": "again", "session_id": "s1"})
    import app as app_module
    assert len(app_module.sessions.history("s1")) == 4


def test_chat_validates_input(client):
    assert client.post("/chat", json={"message": ""}).status_code == 422


def test_stream_endpoint_sends_sse(client):
    r = client.post("/chat/stream", json={"message": "hi"})
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.text.endswith("data: [DONE]\n\n")
