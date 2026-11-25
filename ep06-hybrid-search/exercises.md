# Ep06 exercises: Keyword vs vector vs hybrid

Work in this folder. `pytest -q` uses a toy embedder, so there's no model download and no key.

## Exercise 1 (in the video): sweep alpha

Query `"E1042 files not updating"`. For alpha from 0.0 to 1.0 in steps of 0.1, print the top 2.
Find the alphas where both the E1042 page and the re-authenticate page are in the top 2, then lock
it in with a test.

```python
def test_alpha_sweep_keeps_both_pages(hs):
    good = [a / 10 for a in range(11) if both_in_top2(hs, "E1042 files not updating", a / 10)]
    assert 0.5 in good
```

<details><summary>Solution</summary>

```python
def both_in_top2(hs, query, alpha):
    top2 = [d for _, d in hs.search(query, alpha=alpha, k=2)]
    return any(d.startswith("Error E1042") for d in top2) and any("re-authenticate" in d for d in top2)
```

With the toy embedder every alpha passes, because the query shares words with both pages. Run the
same sweep with `sbert_embedder()` and the range will be narrower and model-dependent. That's the
point: you only know your alpha after measuring it on your own data.
</details>

## Exercise 2: hybrid with RRF

Add `search_rrf(query, k=3)` to `HybridSearch`: rank documents by keyword score and by vector score
separately, then merge the two rankings with `rrf()`.

```python
def test_rrf_search_keeps_both(hs):
    top2 = hs.search_rrf("E1042 syncing devices", k=2)
    assert any(d.startswith("Error E1042") for d in top2)
    assert any("re-authenticate" in d for d in top2)
```

<details><summary>Solution</summary>

```python
    def search_rrf(self, query: str, k: int = 3) -> list[str]:
        def ranking(scores):
            return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        merged = rrf([ranking(self.keyword(query)), ranking(self.vector(query))])
        return [self.docs[i] for i in merged[:k]]
```

No alpha and no normalization: RRF only uses positions.
</details>

## Exercise 3: a tokenizer bug

Write a test showing that `"E-1042"` and `"E1042"` tokenize differently, then make `tokenize`
remove hyphens between a letter and a digit so they match.

<details><summary>Solution</summary>

```python
def test_hyphenated_codes_match():
    assert tokenize("E-1042") == tokenize("E1042") == ["e1042"]
```

```python
def tokenize(text: str) -> list[str]:
    text = re.sub(r"(?<=[A-Za-z])-(?=\d)", "", text)
    return re.findall(r"[a-z0-9]+", text.lower())
```
</details>
