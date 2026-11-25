"""Episode 2: Tool Calling Explained. Several tools, a registry, validation, parallel calls.

    pip install openai tzdata
    set OPENAI_API_KEY, then:  python tools_agent.py "Weather in Tokyo and 50 USD in JPY?"

Frontend mental model: the registry is a router, each tool is a typed route handler,
the JSON schema is its request type, and parallel tool calls are Promise.all.
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo

MODEL = os.environ.get("MODEL", "gpt-4o-mini")   # any model with tool calling
MAX_ROUNDS = 5


def make_client():
    """Create the OpenAI client only when we really call the API (tests never do)."""
    from openai import OpenAI
    return OpenAI()


# ---------------------------------------------------------------- the registry (a router)
@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict
    fn: Callable[..., Any]

    def schema(self) -> dict:
        return {"type": "function",
                "function": {"name": self.name, "description": self.description,
                             "parameters": self.parameters}}


REGISTRY: dict[str, Tool] = {}


def tool(description: str, **properties: dict):
    """Register a function as a tool. Every listed property is required."""
    def register(fn):
        REGISTRY[fn.__name__] = Tool(fn.__name__, description, {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        }, fn)
        return fn
    return register


# ---------------------------------------------------------------- the tools (fake, offline data)
ZONES = {"london": "Europe/London", "tokyo": "Asia/Tokyo", "new york": "America/New_York"}
WEATHER = {"london": (11, "rain"), "tokyo": (18, "cloudy"), "new york": (16, "sunny")}
RATES = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 151.0}   # fixed demo rates, not live


@tool("Current local time in a city. Use it when the user asks what time it is somewhere.",
      city={"type": "string", "description": "City name, for example Tokyo"})
def get_time(city: str) -> str:
    zone = ZONES.get(city.lower())
    if zone is None:
        raise ValueError(f"unknown city {city!r}; known: {', '.join(ZONES)}")
    return datetime.now(ZoneInfo(zone)).strftime("%H:%M")


@tool("Current weather in a city: temperature in Celsius and conditions.",
      city={"type": "string", "description": "City name, for example London"})
def get_weather(city: str) -> dict:
    if city.lower() not in WEATHER:
        raise ValueError(f"no weather for {city!r}; known: {', '.join(WEATHER)}")
    temp, sky = WEATHER[city.lower()]
    return {"city": city, "temp_c": temp, "conditions": sky}


@tool("Convert money between currencies using fixed demo rates.",
      amount={"type": "number", "description": "Amount to convert, for example 50"},
      from_currency={"type": "string", "enum": list(RATES)},
      to_currency={"type": "string", "enum": list(RATES)})
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    value = amount / RATES[from_currency] * RATES[to_currency]
    return {"amount": round(value, 2), "currency": to_currency}


# ---------------------------------------------------------------- validation (like zod.parse)
TYPES = {"string": str, "number": (int, float), "integer": int, "boolean": bool}


def check_args(t: Tool, args: Any) -> str | None:
    """Return a problem description, or None when the arguments match the schema."""
    if not isinstance(args, dict):
        return "arguments must be a JSON object"
    props, required = t.parameters["properties"], t.parameters["required"]
    missing = [k for k in required if k not in args]
    extra = [k for k in args if k not in props]
    if missing or extra:
        return f"missing {missing} / unexpected {extra}"
    for key, value in args.items():
        spec = props[key]
        if isinstance(value, bool) and spec["type"] != "boolean":
            return f"{key} must be {spec['type']}"
        if not isinstance(value, TYPES[spec["type"]]):
            return f"{key} must be {spec['type']}"
        if "enum" in spec and value not in spec["enum"]:
            return f"{key} must be one of {spec['enum']}"
    return None


def dispatch(name: str, raw_args: str) -> str:
    """Run one tool call. Always returns a JSON envelope the model can read: never raises."""
    t = REGISTRY.get(name)
    if t is None:
        return json.dumps({"ok": False, "error": f"no tool named {name}",
                           "hint": f"available: {', '.join(REGISTRY)}"})
    try:
        args = json.loads(raw_args or "{}")
    except json.JSONDecodeError:
        return json.dumps({"ok": False, "error": "arguments were not valid JSON"})
    problem = check_args(t, args)
    if problem:
        return json.dumps({"ok": False, "error": problem, "hint": "fix the arguments and retry"})
    try:
        return json.dumps({"ok": True, "result": t.fn(**args)})
    except Exception as e:                      # the model gets the error, the loop survives
        return json.dumps({"ok": False, "error": str(e)})


# ---------------------------------------------------------------- the loop, with parallel calls
def run(question: str, client=None, model: str = MODEL, log: Callable[[str], None] = print) -> str:
    client = client or make_client()
    messages: list = [{"role": "user", "content": question}]
    tools = [t.schema() for t in REGISTRY.values()]
    for _ in range(MAX_ROUNDS):
        msg = client.chat.completions.create(
            model=model, messages=messages, tools=tools).choices[0].message
        if not msg.tool_calls:
            return msg.content
        messages.append(msg)
        calls = msg.tool_calls
        with ThreadPoolExecutor() as pool:                 # Promise.all for tool calls
            results = list(pool.map(lambda c: dispatch(c.function.name, c.function.arguments), calls))
        for call, result in zip(calls, results):            # one tool message per call id
            log(f"  tool call: {call.function.name}({call.function.arguments}) -> {result}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return f"Stopped after {MAX_ROUNDS} tool rounds."


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What's the weather in Tokyo, and how much is 50 USD in JPY?"
    print(f"> {q}")
    print(run(q))
