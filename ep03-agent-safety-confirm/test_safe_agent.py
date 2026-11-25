"""Tests for Episode 3. No API key: the LLM is a scripted fake.  Run:  pytest -q"""
import json
from types import SimpleNamespace

from safe_agent import PENDING_TTL, SafeAgent


class FakeLLM:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        return SimpleNamespace(choices=[SimpleNamespace(message=self.replies.pop(0))])


def reply(content=None, calls=()):
    tool_calls = [SimpleNamespace(id=f"call_{i}", type="function",
                                  function=SimpleNamespace(name=n, arguments=json.dumps(a)))
                  for i, (n, a) in enumerate(calls)]
    return SimpleNamespace(role="assistant", content=content, tool_calls=tool_calls or None)


def make(*replies, clock=lambda: 1000.0):
    return SafeAgent(user="sara", client=FakeLLM(*replies), clock=clock, log=lambda _: None)


def test_model_request_never_deletes_by_itself():
    agent = make(reply(calls=[("cancel_booking", {"booking_id": "B-102"})]),
                 reply("Please confirm: cancel Thursday 16:30 with Dr. Omar?"))
    r = agent.ask("cancel thursday")
    assert "B-102" in agent.bookings                 # still there
    assert r.pending is not None and "Thu 16:30" in r.pending.summary


def test_human_confirm_executes_once():
    agent = make(reply(calls=[("cancel_booking", {"booking_id": "B-102"})]), reply("Confirm?"))
    token = agent.ask("cancel").pending.token
    assert agent.confirm(token).startswith("Done")
    assert "B-102" not in agent.bookings
    assert agent.confirm(token).startswith("Nothing to confirm")   # token is single-use


def test_wrong_token_and_reject_change_nothing():
    agent = make(reply(calls=[("cancel_booking", {"booking_id": "B-101"})]), reply("Confirm?"))
    agent.ask("cancel")
    assert agent.confirm("guess").startswith("Nothing")
    assert agent.reject().startswith("Okay")
    assert "B-101" in agent.bookings and agent.pending is None


def test_cannot_cancel_someone_elses_booking():
    agent = make(reply(calls=[("cancel_booking", {"booking_id": "B-201"})]), reply("Sorry."))
    r = agent.ask("cancel adam's booking")
    assert r.pending is None and "B-201" in agent.bookings


def test_confirmation_expires():
    now = [1000.0]
    agent = make(reply(calls=[("cancel_booking", {"booking_id": "B-101"})]), reply("Confirm?"),
                 clock=lambda: now[0])
    token = agent.ask("cancel").pending.token
    now[0] += PENDING_TTL + 1
    assert "expired" in agent.confirm(token)
    assert "B-101" in agent.bookings


def test_safe_tool_runs_and_only_shows_own_bookings():
    agent = make()
    assert set(agent.dispatch("list_bookings", "{}")["result"]) == {"B-101", "B-102"}
    assert agent.dispatch("drop_tables", "{}")["ok"] is False
