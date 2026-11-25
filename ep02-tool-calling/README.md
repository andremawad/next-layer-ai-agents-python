# Episode 2: Tool Calling Explained (How LLMs Use Your Python Functions)

Several tools behind one registry, argument validation against the JSON schema, an error envelope
the model can recover from, and parallel tool calls. Plain Python, no framework.

Video: TBD (the link is added when the episode is published)

Part of the course [AI Engineering: Build Real AI Agents in Python](../README.md) on [Next Layer](https://www.youtube.com/@NextLayerEng).

```bash
# one-time setup from the repo root: uv sync   (see ../README.md)
export OPENAI_API_KEY=...        # Windows PowerShell: $env:OPENAI_API_KEY="..."
uv run python tools_agent.py "What's the weather in Tokyo, and how much is 50 USD in JPY?"
```

Example output (the weather and rates are fixed demo data):

```text
> What's the weather in Tokyo, and how much is 50 USD in JPY?
  tool call: get_weather({"city":"Tokyo"}) -> {"ok": true, "result": {"city": "Tokyo", "temp_c": 18, "conditions": "cloudy"}}
  tool call: convert_currency({"amount":50,"from_currency":"USD","to_currency":"JPY"}) -> {"ok": true, "result": {"amount": 7550.0, "currency": "JPY"}}
It's 18°C and cloudy in Tokyo, and 50 USD is about 7,550 JPY.
```

## Tests (no API key needed)

```bash
uv run pytest -q                 # pip: pytest -q (with the venv active)
```

The tests use a fake LLM that plays back scripted replies, so they're free and repeatable.

| Frontend idea | Here |
|---|---|
| router | `REGISTRY` + the `@tool` decorator |
| route handler | each tool function |
| request type / zod schema | the `parameters` JSON schema, checked by `check_args` |
| `{ data, error }` response | the `{"ok": ..., "result" / "error", "hint"}` envelope from `dispatch` |
| `Promise.all` | `ThreadPoolExecutor().map(...)` over the tool calls |

Exercises and quiz: [exercises.md](exercises.md), [quiz.md](quiz.md).
Next episode: stop your agent from doing dangerous things (a two-step confirm enforced in code).
