# Ep05 quiz: Vector databases

Answer from memory, then check. Try again in 3 days without rewatching.

## This episode

1. In one sentence, what is an embedding?
2. Why normalize vectors when you store them?
3. What does a metadata filter add to similarity search?
4. Why can't you compare vectors from two different embedding models?
5. What problem do approximate indexes like HNSW solve?
6. When is Postgres with pgvector enough?

## Spaced review

7. (Ep04) What are the four steps of RAG?
8. (Ep02) What does the model see of a tool?

---

<details><summary>Answers</summary>

1. A list of numbers for a text, where similar meanings land close together.
2. So a dot product equals cosine similarity (and cosine, dot and Euclidean all rank the same).
3. Hard rules (topic, user, date) next to the fuzzy similarity match.
4. Each model builds its own space; the numbers mean different things.
5. Speed at millions of vectors, by not comparing the query against every record.
6. When you already run Postgres and have up to a few million vectors without heavy write load.
7. Chunk, embed, retrieve, ground.
8. A name, a description and a JSON schema of its parameters.
</details>
