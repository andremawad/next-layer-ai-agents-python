# Episode 6: Keyword vs Vector vs Hybrid Search (Which One Wins?)

BM25 keyword search from scratch, cosine vector search, hybrid score fusion with an **explicit**
`alpha` (1.0 = pure vector, 0.0 = pure keyword, as in
[Weaviate's hybrid search](https://docs.weaviate.io/weaviate/concepts/search/hybrid-search)), and
reciprocal rank fusion.

Video: coming soon

Part of the course [AI Engineering: Build Real AI Agents in Python](../README.md) on [Next Layer](https://www.youtube.com/@NextLayerEng).

```bash
# one-time setup from the repo root: uv sync --group local-embeddings
# (pip: pip install -r requirements-local-embeddings.txt). First run downloads a small model.
uv run python hybrid_search.py "error E1042 when syncing"
uv run python hybrid_search.py "my files aren't syncing between laptop and phone"
```

Each run prints the top result for alpha 0.0, 1.0 and 0.5 side by side.

## Tests (no download, no key)

```bash
uv run pytest -q                 # pip: pytest -q (with the venv active)
```

A toy embedder maps a few words onto three "meaning" axes, so the tests can show keyword winning on
exact codes, vector winning on paraphrases, and hybrid keeping both.

`HybridSearch.search()` has no default `alpha` on purpose: write the decision down.

Exercises and quiz: [exercises.md](exercises.md), [quiz.md](quiz.md). Next: evals, testing your agent like real software.
