# Ep01 quiz: Your first AI agent

Answer from memory, then check. Try again in 3 days without rewatching.

1. What's the difference between a chatbot and an agent, in one sentence?
2. Name the four steps of the agent loop.
3. Who runs the tool: the model or your code?
4. What is `tool_call_id` for?
5. Why does `get_time` return "Unknown city" instead of raising?
6. Give the three mistakes from the video and their fixes.

---

<details><summary>Answers</summary>

1. A chatbot answers from memory; an agent can ask your code to run a tool and answer with the result.
2. Ask (messages + tools), decide (answer or request a tool), run (your code runs it), return (append the result, ask again).
3. Your code. The model only asks.
4. It pairs each tool result with the request it answers.
5. The model can read the message and react; an exception would crash the loop.
6. No round limit (cap the rounds), a crashed tool sent nothing back (return the error as the result), trusting model arguments (validate them).
</details>
