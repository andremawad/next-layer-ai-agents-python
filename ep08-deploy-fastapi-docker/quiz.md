# Ep08 quiz: Deploy with FastAPI and Docker

Answer from memory, then check. Try again in 3 days without rewatching.

## This episode

1. Why keep the agent out of `app.py`?
2. What does one Server-Sent Event look like on the wire, and how does the stream end?
3. How do the API tests avoid calling the real LLM?
4. Where does the API key live, and where must it never be?
5. Why do in-memory sessions break with two containers?
6. Why must `/health` never call the model?

## Spaced review

7. (Ep07) What does the eval gate return on a regression?
8. (Ep02) Why do tools return errors instead of raising?

---

<details><summary>Answers</summary>

1. So you can test and reuse it without the web framework (like logic outside components).
2. `data: {...}` followed by a blank line; ours ends with `data: [DONE]`.
3. `app.dependency_overrides[get_llm]` swaps the client for a fake.
4. In the environment at run time (or a secret store). Never in the image, the repo or a log.
5. Each container has its own memory; the next request may hit one that never saw the conversation.
6. A slow model would fail health checks, and the platform would restart healthy containers.
7. Exit code 1.
8. So the model can recover and the loop keeps running.
</details>
