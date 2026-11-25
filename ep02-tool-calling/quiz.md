# Ep02 quiz: Tool calling

Answer from memory first, then check. Come back to it in 3 days without rewatching: that second
try is where most of the learning happens.

## This episode

1. What does the model receive about your Python function?
2. Why does `dispatch` return an error envelope instead of raising?
3. In a reply with two tool calls, how does each result find the call it belongs to?
4. Why `"additionalProperties": False` in every tool schema?
5. `isinstance(True, int)` is `True` in Python. Why does that matter for `check_args`?
6. What's the frontend equivalent of running tool calls with a thread pool?

## Spaced review (Ep01)

7. Name the four steps of the agent loop.
8. Why does the loop have a round cap?

---

<details><summary>Answers</summary>

1. Only its name, the description, and the JSON schema of its parameters. Never the code.
2. So the model can read the problem and fix it on the next round, and the loop keeps running instead of crashing.
3. By `tool_call_id`: each tool message carries the id of the call it answers. Every id needs an answer or the API rejects the next request.
4. So the model can't invent extra arguments; `check_args` rejects them as "unexpected".
5. A model could send `true` for a number field and Python would accept it. `check_args` rejects booleans unless the schema asks for one.
6. `Promise.all`: start all the calls, wait for all of them, keep the order.
7. Ask (send messages and tools), decide (model answers or requests a tool), run (your code runs it), return (append the result and ask again).
8. A confused model can request tools forever, and every round costs money and time.
</details>
