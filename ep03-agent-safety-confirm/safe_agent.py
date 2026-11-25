"""Episode 3: Stop your AI agent from doing dangerous things. Two-step confirm, enforced in code.

    pip install openai
    set OPENAI_API_KEY, then:  python safe_agent.py

The model is an untrusted client, like a browser. A confirm modal is UX; the real guard is
on the server. Here the "server" is our Python: risky tools never run from a model request.
They become a pending action, and only a human "yes" (outside the model) can execute it.
"""
from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Callable

MODEL = os.environ.get("MODEL", "gpt-4o-mini")
MAX_ROUNDS = 5
PENDING_TTL = 120          # seconds a confirmation stays valid


def make_client():
    from openai import OpenAI
    return OpenAI()


# ---------------------------------------------------------------- fake data
def demo_bookings() -> dict[str, dict]:
    return {
        "B-101": {"owner": "sara", "when": "Tue 10:00", "doctor": "Dr. Lina"},
        "B-102": {"owner": "sara", "when": "Thu 16:30", "doctor": "Dr. Omar"},
        "B-201": {"owner": "adam", "when": "Wed 09:00", "doctor": "Dr. Lina"},
    }


TOOLS = [
    {"type": "function", "function": {
        "name": "list_bookings", "description": "List the current user's bookings.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {
        "name": "cancel_booking",
        "description": "Cancel one of the user's bookings. The user must confirm before it happens.",
        "parameters": {"type": "object", "properties": {"booking_id": {"type": "string"}},
                       "required": ["booking_id"], "additionalProperties": False}}},
]
RISKY = {"cancel_booking"}       # anything that changes or deletes data, pays or sends


@dataclass(frozen=True)
class Pending:
    token: str
    tool: str
    args: dict
    summary: str
    created: float


@dataclass
class Reply:
    text: str
    pending: Pending | None = None


@dataclass
class SafeAgent:
    user: str
    client: object = None
    model: str = MODEL
    bookings: dict = field(default_factory=demo_bookings)
    clock: Callable[[], float] = time.time
    pending: Pending | None = None
    log: Callable[[str], None] = print

    # ------------------------------------------------ safe tools run immediately
    def list_bookings(self) -> dict:
        mine = {k: v for k, v in self.bookings.items() if v["owner"] == self.user}
        return {"ok": True, "result": mine}

    # ------------------------------------------------ risky tools only prepare
    def prepare(self, tool: str, args: dict) -> dict:
        booking = self.bookings.get(args.get("booking_id", ""))
        if booking is None or booking["owner"] != self.user:   # authorization, in code
            return {"ok": False, "error": "no such booking for this user"}
        summary = f"Cancel {args['booking_id']}: {booking['when']} with {booking['doctor']}"
        self.pending = Pending(secrets.token_urlsafe(8), tool, dict(args), summary, self.clock())
        return {"ok": False, "status": "needs_confirmation", "summary": summary,
                "next": "Ask the user to confirm. You cannot confirm it yourself."}

    def dispatch(self, name: str, raw: str) -> dict:
        try:
            args = json.loads(raw or "{}")
        except json.JSONDecodeError:
            return {"ok": False, "error": "arguments were not valid JSON"}
        if name == "list_bookings":
            return self.list_bookings()
        if name in RISKY:
            return self.prepare(name, args)
        return {"ok": False, "error": f"no tool named {name}"}

    # ------------------------------------------------ the human step, outside the model
    def confirm(self, token: str) -> str:
        p = self.pending
        if p is None or not secrets.compare_digest(p.token, token):
            return "Nothing to confirm (wrong or used token)."
        self.pending = None                                   # one use only
        if self.clock() - p.created > PENDING_TTL:
            return "That confirmation expired. Ask again."
        del self.bookings[p.args["booking_id"]]
        return f"Done: {p.summary}."

    def reject(self) -> str:
        self.pending = None
        return "Okay, nothing was changed."

    # ------------------------------------------------ the loop (from Ep01 and Ep02)
    def ask(self, text: str) -> Reply:
        client = self.client or make_client()
        messages: list = [
            {"role": "system", "content": f"You help user {self.user} manage clinic bookings."},
            {"role": "user", "content": text}]
        for _ in range(MAX_ROUNDS):
            msg = client.chat.completions.create(
                model=self.model, messages=messages, tools=TOOLS).choices[0].message
            if not msg.tool_calls:
                return Reply(msg.content, self.pending)
            messages.append(msg)
            for call in msg.tool_calls:
                result = self.dispatch(call.function.name, call.function.arguments)
                self.log(f"  tool call: {call.function.name}({call.function.arguments}) -> {result}")
                messages.append({"role": "tool", "tool_call_id": call.id,
                                 "content": json.dumps(result)})
        return Reply(f"Stopped after {MAX_ROUNDS} tool rounds.", self.pending)


if __name__ == "__main__":
    agent = SafeAgent(user="sara")
    r = agent.ask("Cancel my Thursday appointment please.")
    print(r.text)
    if r.pending:
        answer = input(f"\n[confirm] {r.pending.summary}? (yes/no) ").strip().lower()
        print(agent.confirm(r.pending.token) if answer == "yes" else agent.reject())
