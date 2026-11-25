# AI Engineering: Build Real AI Agents in Python

Code for the free YouTube course **AI Engineering: Build Real AI Agents in Python** on the
[Next Layer](https://www.youtube.com/@NextLayerEng) channel.

Build real AI agents in plain Python, one working piece per video. No agent framework: you write
the agent loop, tool calling, safety checks, RAG, search, evals, an API, voice, multi-agent
patterns and an MCP server yourself, so you understand what frameworks do for you.

Every episode uses the same small, fictional example: a booking assistant for a demo clinic. All data
in this repo is made up.

- Channel: https://www.youtube.com/@NextLayerEng
- Course playlist: TBD

## Episodes

Each folder is self-contained: the code, a README (what you build, how to run it), the
exercises with solutions, a short quiz, and tests that run without an API key.

| # | Episode | Folder | Video |
|---|---|---|---|
| 1 | Build Your First AI Agent in Python (No Framework) | [`ep01-first-ai-agent/`](ep01-first-ai-agent/) | TBD |
| 2 | Tool Calling Explained: How LLMs Use Your Python Functions | [`ep02-tool-calling/`](ep02-tool-calling/) | TBD |
| 3 | Stop Your AI Agent From Doing Dangerous Things | [`ep03-agent-safety-confirm/`](ep03-agent-safety-confirm/) | TBD |
| 4 | RAG in Python: Make an AI Answer From Your Own Documents | [`ep04-rag/`](ep04-rag/) | TBD |
| 5 | Vector Databases Explained (With a Python Demo) | [`ep05-vector-databases/`](ep05-vector-databases/) | TBD |
| 6 | Keyword vs Vector vs Hybrid Search: Which One Wins? | [`ep06-hybrid-search/`](ep06-hybrid-search/) | TBD |
| 7 | Test Your AI Agent Like Real Software (Evals in Python) | [`ep07-evals/`](ep07-evals/) | TBD |
| 8 | Deploy a Python AI Agent as an API (FastAPI + Docker) | [`ep08-deploy-fastapi-docker/`](ep08-deploy-fastapi-docker/) | TBD |
| 9 | Give Your AI Agent a Voice (Speech to Text + Text to Speech) | [`ep09-voice-agent/`](ep09-voice-agent/) | TBD |
| 10 | Multi-Agent Systems: When One Agent Isn't Enough | [`ep10-multi-agent-systems/`](ep10-multi-agent-systems/) | TBD |
| 11 | MCP Explained: Build an MCP Server in Python for Your AI Agent | [`ep11-mcp-server/`](ep11-mcp-server/) | TBD |

## Prerequisites

- Basic Python: functions, dicts, lists, classes.
- Python 3.11 or newer.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or pip.
- An OpenAI API key for the live demos (see below). Episodes 5 and 6 run on free local models,
  and **all the tests run without any key**.
- Optional: Docker, for Episode 8.

## Setup

### With uv (recommended)

```bash
git clone <this-repo-url>
cd next-layer-ai-agents-python
uv sync                       # creates .venv and installs the pinned dependencies
uv run pytest                 # every episode's tests, no API key needed
```

Episodes 5 and 6 use free local embeddings. They're a large download (PyTorch), so they're a
separate group:

```bash
uv sync --group local-embeddings
```

### With pip

```bash
python -m venv .venv
source .venv/bin/activate                 # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-local-embeddings.txt   # only for Episodes 5 and 6
pytest
```

With pip, drop `uv run` from the commands in the episode READMEs (`python agent.py` instead of
`uv run python agent.py`).

### Your API key

Copy `.env.example` to `.env` and put your key in it. `.env` is in `.gitignore`, so it never gets
committed. Then either pass the file to uv:

```bash
cd ep01-first-ai-agent
uv run --env-file ../.env python agent.py "What time is it in Tokyo?"
```

or set the variable in your shell:

```bash
export OPENAI_API_KEY=...            # macOS / Linux
$env:OPENAI_API_KEY="..."            # Windows PowerShell
```

## How to get API keys

- **OpenAI** (Episodes 1-4 and 7-11): create an account at https://platform.openai.com, add a
  payment method or credits under Billing, then create a key under API keys. Set a monthly usage
  limit in the billing settings so a bug in a loop can't run up a bill. The demos use small,
  cheap models; running every episode once costs very little.
- **Other providers:** the code uses the OpenAI Python SDK, which works with any
  OpenAI-compatible endpoint that supports tool calling. Set `OPENAI_BASE_URL` (and `MODEL`) in
  your `.env`. Check that your provider supports the features an episode uses (tool calling,
  embeddings, audio).
- **No key needed:** Episodes 5 and 6 download a small open model from Hugging Face on first
  run. The MCP server in Episode 11 runs locally.

Keep keys out of your code, your screen recordings and your commits. If a key leaks, revoke it in
the provider's dashboard right away and create a new one.

## Running the checks

```bash
uv run ruff check     # lint
uv run pytest         # all tests
uv run pytest ep04-rag   # one episode
```

The same checks run on GitHub Actions for every push and pull request
(`.github/workflows/ci.yml`).

## License

The code is released under the [MIT License](LICENSE).
