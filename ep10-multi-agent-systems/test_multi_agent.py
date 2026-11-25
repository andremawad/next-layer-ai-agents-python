"""Tests for Episode 10. No API key: a scripted fake LLM.  Run:  pytest -q"""
import json

import pytest

import multi_agent as ma


class ScriptedLLM:
    """Returns replies in order and records which system prompt each call had."""

    def __init__(self, *replies):
        self.replies, self.systems = list(replies), []

    def __call__(self, messages):
        self.systems.append(messages[0]["content"])
        return self.replies.pop(0)


def test_router_picks_the_named_specialist():
    llm = ScriptedLLM('Sure! {"specialist": "billing"}', "It costs $50.")
    assert ma.routed(llm, "is there a fee?") == ("billing", "It costs $50.")
    assert "billing questions" in llm.systems[1]


@pytest.mark.parametrize("bad", ["no json here", '{"specialist": "hacker"}', "{broken"])
def test_router_falls_back_safely(bad):
    assert ma.route(ScriptedLLM(bad), "hi").name == "faq"


def test_plan_filters_and_caps_subtasks():
    steps = [{"specialist": "bookings", "task": f"t{i}"} for i in range(9)]
    steps.insert(0, {"specialist": "unknown", "task": "x"})
    planned = ma.plan(ScriptedLLM(json.dumps(steps)), "big request")
    assert len(planned) == ma.MAX_SUBTASKS and all(s["specialist"] == "bookings" for s in planned)


def test_plan_falls_back_to_one_step():
    assert ma.plan(ScriptedLLM("I can't"), "hello") == [{"specialist": "faq", "task": "hello"}]


def test_orchestrator_runs_workers_then_merges():
    llm = ScriptedLLM(
        '```json\n[{"specialist": "bookings", "task": "move Thu to Sat"},'
        ' {"specialist": "billing", "task": "fee for moving?"}]\n```',
        "Moved to Saturday 10:00.",
        "No fee if moved 24h ahead.",
        "Done: you're on Saturday at 10:00, and there's no fee.")
    out = ma.orchestrate(llm, "move and fee?", log=lambda _: None)
    assert out.startswith("Done")
    assert len(llm.systems) == 4 and "Combine" in llm.systems[-1]


def test_single_agent_baseline_is_one_call():
    llm = ScriptedLLM("answer")
    assert ma.single_agent(llm, "q") == "answer" and len(llm.systems) == 1
