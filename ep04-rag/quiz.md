# Ep04 quiz: RAG from scratch

Answer from memory, then check. Try again in 3 days without rewatching.

## This episode

1. Name the four steps of RAG.
2. Why do chunks overlap?
3. What does `min_score` protect against?
4. Why does `answer` skip the model entirely when nothing matches?
5. Why should retrieved text be treated as data, not instructions?
6. When would you choose fine-tuning over RAG?

## Spaced review

7. (Ep03) Why is there no `confirm` tool the model can call?
8. (Ep01) Who runs a tool: the model or your code?

---

<details><summary>Answers</summary>

1. Chunk, embed, retrieve, ground.
2. So a sentence crossing a boundary stays whole in at least one chunk.
3. Answering from loosely related text: a confident wrong answer.
4. With no sources it could only guess, and the call costs money.
5. Documents can be outdated, contradictory, or contain text written to manipulate the model.
6. To teach a style, format or narrow skill. For facts that change, use RAG.
7. It could approve its own risky request.
8. Your code. The model only asks.
</details>
