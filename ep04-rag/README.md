# Episode 4: RAG in Python (Make an AI Answer From Your Own Documents)

Retrieval-augmented generation from scratch: chunk with overlap, embed, retrieve with top-k and a
minimum score, answer from numbered sources with citations, and refuse without calling the model
when nothing matches. No LangChain. The `docs/` folder is a fictional clinic.

Video: TBD (the link is added when the episode is published)

Part of the course [AI Engineering: Build Real AI Agents in Python](../README.md) on [Next Layer](https://www.youtube.com/@NextLayerEng).

```bash
# one-time setup from the repo root: uv sync   (see ../README.md)
export OPENAI_API_KEY=...        # Windows PowerShell: $env:OPENAI_API_KEY="..."
uv run python rag.py "Can I cancel my appointment on the same day?"
uv run python rag.py "What's the capital of Peru?"      # -> I couldn't find that in the documents.
```

Set `MODEL` / `EMBED_MODEL` to change models. To embed for free locally, pass any function with the
`Embedder` shape (a list of texts in, a list of vectors out), for example sentence-transformers (Ep05).

## Tests (no API key needed)

```bash
uv run pytest -q                 # pip: pytest -q (with the venv active)
```

The tests use a tiny bag-of-words embedder and a fake LLM.

| Frontend idea | Here |
|---|---|
| fetch only the rows a component needs | `Index.search(question, k=3, min_score=0.3)` |
| props | the numbered sources in `build_messages` |
| empty state instead of a crash | `NOT_FOUND`, returned before any model call |

Exercises and quiz: [exercises.md](exercises.md), [quiz.md](quiz.md). Next: vector databases, built from scratch.
