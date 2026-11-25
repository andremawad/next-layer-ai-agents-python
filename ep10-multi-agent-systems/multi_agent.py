"""Episode 10: Multi-agent systems. When one agent isn't enough (and when it is).

    pip install openai
    set OPENAI_API_KEY, then:  python multi_agent.py "Move my Thursday visit and tell me the fee"

Two patterns from Anthropic's "Building effective agents":
  routing               one cheap call picks ONE specialist (like a router picking a page)
  orchestrator-workers  a planner splits the task, workers do parts, a final call merges
Frontend mental model: specialists are components with one job and their own props (prompt);
the orchestrator is the parent that composes them. Start with one component. Split only when
it gets too big to reason about.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Callable

MODEL = os.environ.get("MODEL", "gpt-4o-mini")
MAX_SUBTASKS = 4                      # a planner can't fan out forever (cost guard)

LLM = Callable[[list[dict]], str]     # messages in, text out


def make_llm(model: str = MODEL) -> LLM:
    from openai import OpenAI
    client = OpenAI()
    return lambda messages: client.chat.completions.create(
        model=model, messages=messages).choices[0].message.content


@dataclass(frozen=True)
class Specialist:
    name: str
    job: str                          # one line, used by the router
    prompt: str                       # the specialist's own system prompt

    def run(self, llm: LLM, task: str) -> str:
        return llm([{"role": "system", "content": self.prompt}, {"role": "user", "content": task}])


SPECIALISTS = {s.name: s for s in [
    Specialist("bookings", "create, move or cancel appointments",
               "You manage clinic appointments. Ask for any missing date or time."),
    Specialist("billing", "fees, invoices, insurance coverage",
               "You answer billing questions for a clinic. Late cancellations cost $50."),
    Specialist("faq", "opening hours, location, parking, general questions",
               "You answer general clinic questions. Open Sun-Thu 9-21, Sat 10-16, closed Fri."),
]}


def parse_json(text: str, fallback):
    """Models sometimes wrap JSON in prose or code fences. Take the outermost [...] or {...}
    (whichever matches the fallback's type) and return the fallback if it doesn't parse."""
    open_, close = ("[", "]") if isinstance(fallback, list) else ("{", "}")
    a, b = text.find(open_), text.rfind(close)
    if a == -1 or b <= a:
        return fallback
    try:
        value = json.loads(text[a:b + 1])
    except json.JSONDecodeError:
        return fallback
    return value if isinstance(value, type(fallback)) else fallback


# ---------------------------------------------------------------- pattern 1: routing
def route(llm: LLM, request: str) -> Specialist:
    menu = "\n".join(f"- {s.name}: {s.job}" for s in SPECIALISTS.values())
    raw = llm([{"role": "system", "content": f"Pick one specialist for the request.\n{menu}\n"
                                             'Reply as JSON: {"specialist": "<name>"}'},
               {"role": "user", "content": request}])
    name = parse_json(raw, {}).get("specialist")
    return SPECIALISTS.get(name, SPECIALISTS["faq"])          # unknown name: safe default


def routed(llm: LLM, request: str) -> tuple[str, str]:
    s = route(llm, request)
    return s.name, s.run(llm, request)


# ---------------------------------------------------------------- pattern 2: orchestrator-workers
def plan(llm: LLM, request: str) -> list[dict]:
    names = ", ".join(SPECIALISTS)
    raw = llm([{"role": "system", "content": f"Split the request into at most {MAX_SUBTASKS} "
                                             f"subtasks. Specialists: {names}. Reply as JSON: "
                                             '[{"specialist": "...", "task": "..."}]'},
               {"role": "user", "content": request}])
    steps = parse_json(raw, [])
    valid = [s for s in steps if isinstance(s, dict) and s.get("specialist") in SPECIALISTS
             and isinstance(s.get("task"), str)]
    return valid[:MAX_SUBTASKS] or [{"specialist": "faq", "task": request}]


def orchestrate(llm: LLM, request: str, log: Callable[[str], None] = print) -> str:
    steps = plan(llm, request)
    results = []
    for step in steps:
        out = SPECIALISTS[step["specialist"]].run(llm, step["task"])
        log(f"  [{step['specialist']}] {step['task']} -> {out[:70]}")
        results.append(f"{step['specialist']}: {out}")
    return llm([{"role": "system", "content": "Combine the specialists' answers into one short "
                                              "reply. Don't add facts they didn't give."},
                {"role": "user", "content": f"Request: {request}\n\n" + "\n".join(results)}])


# ---------------------------------------------------------------- the baseline you must beat
def single_agent(llm: LLM, request: str) -> str:
    prompt = " ".join(s.prompt for s in SPECIALISTS.values())
    return llm([{"role": "system", "content": prompt}, {"role": "user", "content": request}])


if __name__ == "__main__":
    request = " ".join(sys.argv[1:]) or "Move my Thursday visit to Saturday and tell me if there's a fee."
    llm = make_llm()
    print(f"> {request}\n\nsingle agent:\n{single_agent(llm, request)}\n")
    name, text = routed(llm, request)
    print(f"routed to {name}:\n{text}\n\norchestrator-workers:")
    print(orchestrate(llm, request))
