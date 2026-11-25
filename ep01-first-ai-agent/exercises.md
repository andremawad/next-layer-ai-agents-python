# Ep01 exercises: Your first AI agent

Work in this folder. Run `pytest -q` after each exercise; the tests use a fake LLM, so no API key is
needed. Try each exercise before you open its solution.

## Exercise 1: a fourth city

Add Paris to `get_time`. Then write a test that proves it returns `HH:MM`.

<details><summary>Solution</summary>

Add `"paris": "Europe/Paris"` to `zones`, then:

```python
def test_paris(agent):
    assert re.fullmatch(r"\d\d:\d\d", agent.get_time("Paris"))
```
</details>

## Exercise 2: make the round cap a parameter

Change `run(question)` to `run(question, max_rounds=5)` and make this test pass:

```python
def test_custom_round_cap(agent, monkeypatch):
    stuck = [reply(calls=[("get_time", {"city": "Tokyo"})]) for _ in range(2)]
    monkeypatch.setattr(agent, "client", FakeLLM(*stuck))
    assert agent.run("loop", max_rounds=2) == "Stopped after 2 tool rounds."
```

<details><summary>Solution</summary>

```python
def run(question, max_rounds=5):
    messages = [{"role": "user", "content": question}]
    for _ in range(max_rounds):
        ...
    return f"Stopped after {max_rounds} tool rounds."
```
</details>

## Exercise 3: trace the messages (a reducer view)

Print `messages` after every round. Write down how the list grows for "What time is it in Tokyo?".
Frontend view: the message list is your app state, each round is a reducer step that appends.

<details><summary>Solution</summary>

1. `[user]`
2. `[user, assistant(tool_calls=[get_time])]` then `+ tool(tool_call_id=call_0, "21:04")`
3. Round 2 returns plain text, so nothing more is appended: the answer is returned.
</details>

## Exercise 4: return errors, validate arguments

The loop calls `get_time(**json.loads(...))` directly, so a malformed or unexpected tool call
crashes the agent. Write a `call_tool(call)` helper that returns errors to the model as text
instead, and use it in the loop. Make this test pass:

```python
def test_bad_arguments_are_returned_as_errors(agent):
    call = SimpleNamespace(function=SimpleNamespace(name="get_time", arguments='{"city": 42}'))
    assert agent.call_tool(call).startswith("Error:")
```

<details><summary>Solution</summary>

```python
def call_tool(call):
    try:
        args = json.loads(call.function.arguments)
        if call.function.name != "get_time" or not isinstance(args.get("city"), str):
            return f"Error: unexpected tool call {call.function.name}({args})"
        return get_time(args["city"])
    except Exception as e:                   # return errors to the model, never crash
        return f"Error: {e}"
```

Then in `run`: `result = call_tool(call)`.
</details>
