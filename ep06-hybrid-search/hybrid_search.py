"""Episode 6: Keyword vs vector vs hybrid search, side by side.

    pip install sentence-transformers
    python hybrid_search.py "error E1042 when syncing"

alpha is always set explicitly: 1.0 = pure vector, 0.0 = pure keyword (BM25).
Frontend mental model: keyword search is Ctrl+F (exact matches), vector search is
"similar products" (meaning), hybrid is a store search box that does both and merges.
"""
from __future__ import annotations

import math
import re
import sys
from collections import Counter
from typing import Callable, Sequence

Embedder = Callable[[Sequence[str]], list[list[float]]]


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


# ---------------------------------------------------------------- keyword: BM25 from scratch
class BM25:
    def __init__(self, docs: Sequence[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.toks = [tokenize(d) for d in docs]
        self.avgdl = sum(map(len, self.toks)) / max(len(self.toks), 1)
        df = Counter(t for doc in self.toks for t in set(doc))
        n = len(self.toks)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> list[float]:
        out = []
        for doc in self.toks:
            tf, s = Counter(doc), 0.0
            for t in tokenize(query):
                if t in tf:
                    f = tf[t]
                    s += self.idf[t] * f * (self.k1 + 1) / (
                        f + self.k1 * (1 - self.b + self.b * len(doc) / self.avgdl))
            out.append(s)
        return out


# ---------------------------------------------------------------- vector
def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def min_max(xs: Sequence[float]) -> list[float]:
    lo, hi = min(xs), max(xs)
    return [0.0] * len(xs) if hi == lo else [(x - lo) / (hi - lo) for x in xs]


# ---------------------------------------------------------------- hybrid
class HybridSearch:
    def __init__(self, docs: Sequence[str], embed: Embedder):
        self.docs, self.embed = list(docs), embed
        self.bm25 = BM25(self.docs)
        self.vectors = embed(self.docs)

    def keyword(self, query: str) -> list[float]:
        return self.bm25.scores(query)

    def vector(self, query: str) -> list[float]:
        q = self.embed([query])[0]
        return [cosine(q, v) for v in self.vectors]

    def search(self, query: str, alpha: float, k: int = 3) -> list[tuple[float, str]]:
        """Relative score fusion: normalize both to 0..1, then alpha * vector + (1 - alpha) * keyword."""
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1")
        kw, vec = min_max(self.keyword(query)), min_max(self.vector(query))
        fused = [alpha * v + (1 - alpha) * w for v, w in zip(vec, kw)]
        return sorted(zip(fused, self.docs), reverse=True)[:k]


def rrf(rankings: Sequence[Sequence[int]], k: int = 60) -> list[int]:
    """Reciprocal rank fusion: merge ranked lists of doc ids without comparing raw scores."""
    score: Counter = Counter()
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            score[doc_id] += 1 / (k + rank + 1)
    return [d for d, _ in score.most_common()]


DOCS = [
    "Error E1042: the sync token expired. Sign out and sign in again.",
    "If your files stop updating between devices, re-authenticate your account.",
    "Error E2001: disk full. Free some space and retry the upload.",
    "Change your profile photo from the account settings page.",
    "Uploads are slow on hotel wifi; try a wired connection.",
]


def sbert_embedder(model_name: str = "all-MiniLM-L6-v2") -> Embedder:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    return lambda texts: [list(map(float, v)) for v in model.encode(list(texts))]


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "my files aren't syncing between laptop and phone"
    hs = HybridSearch(DOCS, sbert_embedder())
    print(f"> {query}")
    for name, alpha in (("keyword (alpha=0.0)", 0.0), ("vector  (alpha=1.0)", 1.0),
                        ("hybrid  (alpha=0.5)", 0.5)):
        top = hs.search(query, alpha=alpha, k=1)[0]
        print(f"  {name}: {top[0]:.2f}  {top[1]}")
