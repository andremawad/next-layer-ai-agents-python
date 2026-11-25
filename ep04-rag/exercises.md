# Ep04 exercises: RAG from scratch

Work in this folder. `pytest -q` uses a fake embedder and a fake LLM, so no API key is needed.

## Exercise 1 (in the video): show the sources

Add `sources(hits)` that returns the unique file names, best match first. Print them under the answer.

```python
def test_sources_are_unique_and_ordered():
    a, b = rag.Chunk("a.md", "x"), rag.Chunk("b.md", "y")
    assert rag.sources([(0.9, a), (0.8, b), (0.7, a)]) == ["a.md", "b.md"]
    assert rag.sources([]) == []
```

<details><summary>Solution</summary>

```python
def sources(hits: list[tuple[float, Chunk]]) -> list[str]:
    return list(dict.fromkeys(c.source for _, c in hits))   # dicts keep insertion order
```

In `__main__`: `print("Sources:", ", ".join(sources(hits)) or "none")`.
</details>

## Exercise 2: tune min_score with a tiny eval

Write 4 questions with the file that should answer them (and one that no file answers). For
`min_score` in `0.1, 0.2, ... 0.6`, count how many questions get the right first source or a correct
refusal. Do it with the fake embedder first, then with real embeddings if you have a key.

<details><summary>Solution</summary>

```python
CASES = [("Is there a fee to cancel?", "cancellation-policy.md"),
         ("When are you open?", "opening-hours.md"),
         ("Do you take my insurance card?", "insurance.md"),
         ("What's the capital of Peru?", None)]

def score(index, min_score):
    ok = 0
    for q, want in CASES:
        hits = index.search(q, min_score=min_score)
        got = hits[0][1].source if hits else None
        ok += got == want
    return ok

index = rag.Index(rag.load_chunks(), fake_embed)
for m in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
    print(m, score(index, m), "/", len(CASES))
```

Pick the lowest `min_score` that still refuses the Peru question. Episode 7 turns this into a real eval suite.
</details>

## Exercise 3: chunk by paragraph

Write `chunk_paragraphs(text, max_words=80)` that splits on blank lines first and only uses
`chunk()` for paragraphs longer than `max_words`.

<details><summary>Solution</summary>

```python
def chunk_paragraphs(text: str, max_words: int = 80) -> list[str]:
    out = []
    for para in (p.strip() for p in text.split("\n\n")):
        if not para:
            continue
        out += [para] if len(para.split()) <= max_words else chunk(para, max_words, max_words // 4)
    return out
```

```python
def test_chunk_paragraphs():
    text = "short one\n\nshort two\n\n" + " ".join(["w"] * 100)
    parts = rag.chunk_paragraphs(text, max_words=80)
    assert parts[:2] == ["short one", "short two"] and len(parts) >= 3
```
</details>
