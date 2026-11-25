# Episode 5: Vector Databases Explained (With a Python Demo)

A tiny vector store in plain Python: normalize on insert (so dot product = cosine), upsert, delete,
top-k query with a metadata filter, and save/load to JSON. The demo uses free local embeddings from
[sentence-transformers](https://www.sbert.net/); no API key.

Video: coming soon

Part of the course [AI Engineering: Build Real AI Agents in Python](../README.md) on [Next Layer](https://www.youtube.com/@NextLayerEng).

```bash
# one-time setup from the repo root: uv sync --group local-embeddings
# (pip: pip install -r requirements-local-embeddings.txt). First run downloads a small model.
uv run python vector_store.py "my tooth hurts when I drink cold water"
```

Expected shape of the output (scores depend on the model version):

```text
> my tooth hurts when I drink cold water   (384 dimensions)
  0.5x  [dental] Sensitivity to cold drinks can mean worn enamel or a cavity.
  ...
```

## Tests (no download, no key)

```bash
uv run pytest -q                 # pip: pytest -q (with the venv active)
```

The tests use RGB colors as 3-D vectors: red is closest to crimson, and a `where` filter can force blue.

Real vector databases add approximate indexes (HNSW, IVF) for millions of vectors. The interface
(upsert, query, filter) stays the same.

Exercises and quiz: [exercises.md](exercises.md), [quiz.md](quiz.md). Next: keyword vs vector vs hybrid search.
