# Ep02 exercises: Tool calling

Work in this folder. Run `pytest -q` after each exercise; no API key needed. Try each one before you
open its solution. Writing the code yourself is the point.

## Exercise 1 (in the video): a forecast tool with a range check

Add `get_forecast(city, days)` to the registry. `days` is an integer from 1 to 5. Teach
`check_args` to read `minimum` and `maximum` from the schema.

Paste this test into `test_tools_agent.py`. It fails until you're done:

```python
def test_forecast_tool_checks_range():
    t = ta.REGISTRY["get_forecast"]
    assert ta.check_args(t, {"city": "Tokyo", "days": 3}) is None
    assert "between 1 and 5" in ta.check_args(t, {"city": "Tokyo", "days": 9})
    assert "integer" in ta.check_args(t, {"city": "Tokyo", "days": 2.5})
    assert json.loads(ta.dispatch("get_forecast", '{"city": "Tokyo", "days": 2}'))["ok"] is True
```

<details><summary>Solution</summary>

```python
@tool("Weather forecast for the next few days in a city.",
      city={"type": "string", "description": "City name, for example Tokyo"},
      days={"type": "integer", "minimum": 1, "maximum": 5, "description": "1 to 5"})
def get_forecast(city: str, days: int) -> dict:
    temp, sky = WEATHER[city.lower()]
    return {"city": city, "days": [{"day": i + 1, "temp_c": temp + i, "conditions": sky}
                                   for i in range(days)]}
```

In `check_args`, after the enum check:

```python
        lo, hi = spec.get("minimum"), spec.get("maximum")
        if (lo is not None and value < lo) or (hi is not None and value > hi):
            return f"{key} must be between {lo} and {hi}"
```

The `integer` type already rejects `2.5`, because `TYPES["integer"]` is `int`.
Remember to update `test_registry_builds_schemas_for_every_tool`, which lists the tool names.
</details>

## Exercise 2: see the parallel speed-up

Make `get_weather` slow with `time.sleep(1)`, ask a question that needs weather for three cities
with a fake LLM, and time `run()`. Then replace the thread pool with a plain `for` loop and time it again.

<details><summary>Solution</summary>

With the pool, three 1-second tools take about 1 second; with a plain loop, about 3. Same idea as
`await Promise.all([...])` vs three `await`s in a row. Remove the sleep afterwards.

A scratch script (`scratch_timing.py`, not a test: timing tests are flaky in CI):

```python
import time
from test_tools_agent import FakeLLM, reply
import tools_agent as ta

fake = FakeLLM(reply(calls=[("get_weather", {"city": c}) for c in ("Tokyo", "London", "New York")]),
               reply("done"))
t0 = time.perf_counter()
ta.run("weather x3", client=fake, log=lambda _: None)
print(f"{time.perf_counter() - t0:.2f}s")
```
</details>

## Exercise 3: an unknown-tool test

Write a test where the fake model calls `send_email` (not registered). Assert that the loop keeps
going and the tool message says which tools exist.

<details><summary>Solution</summary>

```python
def test_unknown_tool_gets_a_hint():
    fake = FakeLLM(reply(calls=[("send_email", {"to": "x"})]), reply("I can't send email."))
    assert ta.run("email bob", client=fake, log=lambda _: None) == "I can't send email."
    tool_msg = fake.requests[-1]["messages"][-1]
    assert "available: get_time" in json.loads(tool_msg["content"])["hint"]
```
</details>
