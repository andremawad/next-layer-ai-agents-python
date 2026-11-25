# Episode 7: Test Your AI Agent Like Real Software (Evals in Python)

An eval harness in plain Python: cases in `cases.jsonl`, code-based graders, k runs per case,
pass@k vs pass^k, a baseline in `baseline.json`, and a gate that exits with code 1 on a regression,
so it can fail a CI job. The agent under test is the Ep01 time agent.

Video: coming soon

Part of the course [AI Engineering: Build Real AI Agents in Python](../README.md) on [Next Layer](https://www.youtube.com/@NextLayerEng).

```bash
# one-time setup from the repo root: uv sync   (see ../README.md)
export OPENAI_API_KEY=...        # Windows PowerShell: $env:OPENAI_API_KEY="..."
uv run python evals.py --k 3                    # exit code 1 if the pass rate drops below the baseline
uv run python evals.py --k 3 --update-baseline  # after an intentional improvement
```

Example output (yours will differ run to run; that's why k > 1):

```text
  PASS  time-tokyo             3/3
  FAIL  unknown-city           2/3  answer has none of [...]
pass rate 93% (baseline 80%)  pass@3 100%  pass^3 80%
```

## Tests for the harness (no API key needed)

```bash
uv run pytest -q                 # pip: pytest -q (with the venv active)
```

The harness itself is tested with fake agents: a flaky one, one that crashes, one that's always wrong.

Further reading: Hamel Husain, *Your AI product needs evals*: https://hamel.dev/blog/posts/evals/

Exercises and quiz: [exercises.md](exercises.md), [quiz.md](quiz.md). Next: deploy the agent as an API with FastAPI and Docker.
