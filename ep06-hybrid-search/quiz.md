# Ep06 quiz: Keyword vs vector vs hybrid

Answer from memory, then check. Try again in 3 days without rewatching.

## This episode

1. Where does keyword search beat vector search? And the reverse?
2. Name the three ideas inside BM25.
3. Why normalize scores before mixing them?
4. What do alpha 0, 0.5 and 1 mean?
5. Why does `search()` have no default alpha?
6. What does reciprocal rank fusion use instead of scores?

## Spaced review

7. (Ep05) Why normalize vectors on insert?
8. (Ep04) What does `min_score` protect against?

---

<details><summary>Answers</summary>

1. Keyword: exact strings like error codes, names, SKUs. Vector: paraphrases and vague questions.
2. Rare words count more (IDF), repeats help with diminishing returns (k1), long documents get a small penalty (b).
3. They're on different scales; raw BM25 would drown cosine.
4. Pure keyword, an even mix, pure vector.
5. Defaults differ between libraries and versions; an explicit alpha is a written decision.
6. Positions in each ranked list (1 / (k + rank)).
7. So a dot product equals cosine similarity.
8. Answering from loosely related text.
</details>
