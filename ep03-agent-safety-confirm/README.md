# Episode 3: Stop Your AI Agent From Doing Dangerous Things

A clinic booking agent (fake data) whose risky tool can't run from a model request: it prepares a
pending action, and only a human "yes" in your own code runs it, with a one-time token that expires
and an ownership check. Plain Python, no framework.

Video: coming soon

Part of the course [AI Engineering: Build Real AI Agents in Python](../README.md) on [Next Layer](https://www.youtube.com/@NextLayerEng).

```bash
# one-time setup from the repo root: uv sync   (see ../README.md)
export OPENAI_API_KEY=...        # Windows PowerShell: $env:OPENAI_API_KEY="..."
uv run python safe_agent.py
```

Example session (the model's wording will differ):

```text
  tool call: list_bookings({}) -> {'ok': True, 'result': {...}}
  tool call: cancel_booking({"booking_id":"B-102"}) -> {'ok': False, 'status': 'needs_confirmation', ...}
I've prepared the cancellation of your Thursday 16:30 visit with Dr. Omar. Please confirm.

[confirm] Cancel B-102: Thu 16:30 with Dr. Omar? (yes/no) yes
Done: Cancel B-102: Thu 16:30 with Dr. Omar.
```

## Tests (no API key needed)

```bash
uv run pytest -q                 # pip: pytest -q (with the venv active)
```

| Frontend idea | Here |
|---|---|
| the browser is an untrusted client | the model's tool calls are untrusted requests |
| "Are you sure?" modal | the model asking the user (UX only) |
| server-side authorization | the ownership check in `prepare` |
| CSRF / one-time token | `Pending.token`: random, single use, expires after `PENDING_TTL` |

Exercises and quiz: [exercises.md](exercises.md), [quiz.md](quiz.md). Next: RAG, answering from your own documents.
