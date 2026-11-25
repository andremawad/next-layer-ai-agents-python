# Ep05 exercises: Build a vector store

Work in this folder. `pytest -q` uses hand-made vectors, so there's no model download and no key.

## Exercise 1 (in the video): query by text

Give `VectorStore` an optional embedder and add `query_text(text, k=3, where=None)`.

```python
def test_query_text_embeds_for_you():
    s = VectorStore(dim=3, embed=lambda texts: [[250, 10, 10] for _ in texts])
    s.upsert("red", "red", [255, 0, 0])
    s.upsert("blue", "blue", [0, 0, 255])
    assert s.query_text("anything reddish", k=1)[0].id == "red"


def test_query_text_without_embedder_fails_clearly():
    with pytest.raises(ValueError):
        VectorStore(dim=3).query_text("x")
```

<details><summary>Solution</summary>

```python
    def __init__(self, dim: int, embed: Embedder | None = None):
        self.dim, self.embed = dim, embed
        self.records: dict[str, Record] = {}

    def query_text(self, text: str, k: int = 3, where: dict | None = None) -> list[Hit]:
        if self.embed is None:
            raise ValueError("this store has no embedder; pass embed= or use query(vector)")
        return self.query(self.embed([text])[0], k, where)
```

`load()` creates the store with `cls(data["dim"])`, so loaded stores have no embedder until you set
`store.embed = ...`. That's deliberate: the file doesn't know which model made the vectors.
</details>

## Exercise 2: remember which model made the vectors

Add a `model` field to the store, save it in the JSON, and make `load(path, expect_model=...)` raise
if the saved model differs. (This is the "mixed vectors from two models" mistake from the video.)

<details><summary>Solution</summary>

```python
    def __init__(self, dim: int, model: str = "unknown"):
        self.dim, self.model = dim, model
        ...
    # save: data = {"dim": self.dim, "model": self.model, "records": [...]}

    @classmethod
    def load(cls, path, expect_model: str | None = None):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if expect_model and data.get("model") != expect_model:
            raise ValueError(f"store was built with {data.get('model')}, not {expect_model}")
        store = cls(data["dim"], data.get("model", "unknown"))
        ...
```
</details>

## Exercise 3: see the 384 numbers

With sentence-transformers installed, embed "cat", "kitten" and "car". Print the three cosine
similarities. Which pair is closest? Then try two sentences with the same words in a different order.

<details><summary>Solution</summary>

```python
from vector_store import sbert_embedder, normalize
embed = sbert_embedder()
cat, kitten, car = (normalize(v) for v in embed(["cat", "kitten", "car"]))
dot = lambda a, b: sum(x * y for x, y in zip(a, b))
print(dot(cat, kitten), dot(cat, car), dot(kitten, car))
```

Cat and kitten should be closest. "dog bites man" and "man bites dog" score very high together,
which shows embeddings capture topic more than exact meaning. Your numbers depend on the model.
</details>
