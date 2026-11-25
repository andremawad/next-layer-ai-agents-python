# Episode 8: Deploy a Python AI Agent as an API (FastAPI + Docker)

The agent core (`agent_core.py`, no web framework inside), a thin FastAPI layer (`app.py`) with
`GET /health`, `POST /chat` and `POST /chat/stream` (Server-Sent Events), a browser client for the
stream (`stream_client.js`), and a Dockerfile that follows the
[FastAPI Docker docs](https://fastapi.tiangolo.com/deployment/docker/).

Video: TBD (the link is added when the episode is published)

Part of the course [AI Engineering: Build Real AI Agents in Python](../README.md) on [Next Layer](https://www.youtube.com/@NextLayerEng).

## Run locally

```bash
# one-time setup from the repo root: uv sync   (see ../README.md)
export OPENAI_API_KEY=...        # Windows PowerShell: $env:OPENAI_API_KEY="..."
uv run fastapi dev app.py               # docs at http://localhost:8000/docs
```

## Run in Docker (the key is passed at run time, never baked into the image)

```bash
docker build -t agent-api .
docker run -p 8000:80 -e OPENAI_API_KEY agent-api
curl -X POST localhost:8000/chat -H "content-type: application/json" -d '{"message": "Time in Tokyo?"}'
curl -N -X POST localhost:8000/chat/stream -H "content-type: application/json" -d '{"message": "Say hi"}'
```

## Tests (no API key needed)

```bash
uv run pytest -q                 # pip: pytest -q (with the venv active)
```

`app.dependency_overrides[get_llm]` swaps the OpenAI client for a fake, like mocking `fetch` with MSW.
Without FastAPI installed, the 4 HTTP tests are skipped and the 4 core tests still run.

Before going online: sessions in Redis or a DB (in-memory breaks with 2+ containers), rate limits
and a cost cap per user, timeouts on model calls, CORS only for your own origins, and the Ep07 evals
in the same pipeline.

Exercises and quiz: [exercises.md](exercises.md), [quiz.md](quiz.md). Next: give the agent a voice.
