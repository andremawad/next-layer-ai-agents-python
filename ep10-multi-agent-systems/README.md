# Episode 10: Multi-Agent Systems (When One Agent Isn't Enough)

Two patterns from Anthropic's
[Building effective agents](https://www.anthropic.com/research/building-effective-agents), built
from scratch: **routing** (one call picks one specialist, with a safe default) and
**orchestrator-workers** (a planner splits the task, capped at 4 subtasks, workers answer, a final
call merges). Plus the **single-agent baseline** you must beat before splitting.

Video: coming soon

Part of the course [AI Engineering: Build Real AI Agents in Python](../README.md) on [Next Layer](https://www.youtube.com/@NextLayerEng).

```bash
# one-time setup from the repo root: uv sync   (see ../README.md)
export OPENAI_API_KEY=...        # Windows PowerShell: $env:OPENAI_API_KEY="..."
uv run python multi_agent.py "Move my Thursday visit to Saturday and tell me if there's a fee."
```

It prints the single-agent answer, the routed answer and the orchestrated answer for the same request.

## Tests (no API key needed)

```bash
uv run pytest -q                 # pip: pytest -q (with the venv active)
```

A scripted fake LLM returns replies in order and records each call's system prompt.

| Frontend idea | Here |
|---|---|
| a component with one job and its props | `Specialist(name, job, prompt)` |
| a router picking one page | `route()` |
| a parent composing children | `orchestrate()` |
| validating an API response | `parse_json()` + the specialist check in `plan()` |

Try it yourself: combine Ep02-Ep08 into one deployed clinic assistant.
Exercises and quiz: [exercises.md](exercises.md), [quiz.md](quiz.md).
