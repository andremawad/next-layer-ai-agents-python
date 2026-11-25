# Ep03 quiz: Make your agent ask first

Answer from memory, then check. Try again in 3 days without rewatching.

## This episode

1. Why isn't "always confirm before cancelling" in the system prompt a real guard?
2. Why is there no `confirm` tool in the tool list?
3. Name four properties that make the confirmation token safe.
4. Where is ownership of a booking checked, and why there?
5. What is prompt injection, and why does today's guard still hold against it?
6. Which kinds of tools should be in `RISKY`?

## Spaced review

7. (Ep02) What does `dispatch` return when the model sends bad arguments?
8. (Ep01) Why does the loop have a round cap?

---

<details><summary>Answers</summary>

1. The model can skip it, or be talked out of it by the user or by text in a document.
2. If the model could call it, it could approve its own risky request.
3. Random (`secrets.token_urlsafe`), single use (cleared before acting), it expires (TTL), compared with `compare_digest`.
4. In `prepare`, in code, like a server checking the session: the model's arguments are untrusted input.
5. Instructions hidden in text the model reads. The guard holds because no text can press the human's confirm button.
6. Anything that changes or deletes data, spends money, books, or sends a message. If unsure, make it risky.
7. An error envelope `{"ok": false, "error": ..., "hint": ...}` the model can read and fix.
8. To stop a confused model from requesting tools forever and running up cost.
</details>
