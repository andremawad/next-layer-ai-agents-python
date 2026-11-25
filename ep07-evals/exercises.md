# Ep07 exercises: Evals in Python

Work in this folder. `pytest -q` tests the harness with fake agents; no key needed. Running
`python evals.py` against the real model needs `OPENAI_API_KEY`.

## Exercise 1 (in the video): a new case and a length grader

1. Add a case to `cases.jsonl` with id `unknown-city-mars` for "What time is it in Mars City?" that
   must call `get_time` and must admit it doesn't know.
2. Add `max_chars: int | None = None` to `Case`, and a grader that fails answers longer than it.

```python
def test_max_chars_grader():
    case = Case("t", "q", max_chars=20)
    assert grade(case, Result("short")) == []
    assert "too long" in grade(case, Result("x" * 21))[0]


def test_mars_case_exists():
    assert any(c.id == "unknown-city-mars" for c in load_cases())
```

`test_cases_file_loads` expects 5 cases: change it to 6.

<details><summary>Solution</summary>

```json
{"id": "unknown-city-mars", "question": "What time is it in Mars City?", "must_call": "get_time", "contains_any": ["unknown", "don't know", "not sure", "couldn't", "can't"]}
```

```python
    max_chars: int | None = None          # in Case

    # in grade(), before `return fails`
    if case.max_chars is not None and len(r.answer) > case.max_chars:
        fails.append(f"answer too long ({len(r.answer)} > {case.max_chars} chars)")
```
</details>

## Exercise 2: put it in CI

Write a CI step that runs the suite and fails the job on a regression. Use GitHub Actions or any CI.
Keep the API key in the CI's secret store.

<details><summary>Solution (GitHub Actions)</summary>

```yaml
name: evals
on: [pull_request]
jobs:
  evals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install openai tzdata pytest
      - run: pytest -q                          # free: the harness tests
      - run: python evals.py --k 3              # paid: exits 1 on a regression
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

Run the paid step on pull requests that touch prompts or tools, not on every commit.
</details>

## Exercise 3: a pass^k gate

Critical cases (anything that books or cancels) should pass every run. Add `"critical": true` to a
case and fail the suite if any critical case has a failed run, whatever the overall pass rate.

<details><summary>Solution</summary>

```python
    critical: bool = False                # in Case

def critical_failures(report: Report, cases: list[Case]) -> list[str]:
    crit = {c.id for c in cases if c.critical}
    return [r["id"] for r in report.rows if r["id"] in crit and not all(r["runs"])]
```

In `main`, return 1 when `critical_failures(...)` is non-empty, and print their ids.
</details>
