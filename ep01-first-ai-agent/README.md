# Episode 1: Build your first AI agent in Python (no framework)

A working tool-calling agent in plain Python, about 40 lines: one tool (`get_time`), the agent
loop and a round limit. No LangChain or agent framework needed. Exercise 4 adds the error handling
and argument checks from the video's "three mistakes" section.

Video: coming soon

Part of the course [AI Engineering: Build Real AI Agents in Python](../README.md) on [Next Layer](https://www.youtube.com/@NextLayerEng).

```bash
# one-time setup from the repo root: uv sync   (see ../README.md)
export OPENAI_API_KEY=...        # Windows PowerShell: $env:OPENAI_API_KEY="..."
uv run python agent.py
```

Example output (your time will differ):

```text
> What time is it in Tokyo right now?
  tool call: get_time({"city":"Tokyo"}) -> 14:32
It's 14:32 in Tokyo right now.
```

Works with any OpenAI-compatible endpoint that supports tool calling (set `MODEL` and the
client's `base_url`).

## Tests (no API key needed)

```bash
uv run pytest -q                 # pip: pytest -q (with the venv active)
```

The tests swap the OpenAI client for a fake LLM that plays back scripted replies.

Exercises and quiz: [exercises.md](exercises.md), [quiz.md](quiz.md).
Next episode: tool calling in depth (several tools, parallel calls, descriptions the model follows).
