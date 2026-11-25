# pip install openai tzdata
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import OpenAI

client = OpenAI()        # reads OPENAI_API_KEY from the environment
MODEL = "gpt-4o-mini"    # any current model with tool calling

def get_time(city: str) -> str:
    zones = {"london": "Europe/London",
             "tokyo": "Asia/Tokyo",
             "new york": "America/New_York"}
    zone = zones.get(city.lower())
    if zone is None:
        return f"Unknown city: {city}"
    return datetime.now(ZoneInfo(zone)).strftime("%H:%M")

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_time",
        "description": "Current local time in a city",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}]

def run(question):
    messages = [{"role": "user", "content": question}]
    for _ in range(5):                       # never loop forever
        msg = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS).choices[0].message
        if not msg.tool_calls:
            return msg.content               # plain answer: done
        messages.append(msg)
        for call in msg.tool_calls:
            result = get_time(**json.loads(call.function.arguments))
            print(f"  tool call: {call.function.name}({call.function.arguments}) -> {result}")
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": result})
    return "Stopped after 5 tool rounds."

if __name__ == "__main__":
    print("> What time is it in Tokyo right now?")
    print(run("What time is it in Tokyo right now?"))
