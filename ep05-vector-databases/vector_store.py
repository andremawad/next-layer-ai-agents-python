"""Episode 5: Vector databases explained, by building a tiny one in plain Python.

    pip install sentence-transformers      (free, runs locally; first run downloads a small model)
    python vector_store.py "my tooth hurts when I drink cold water"

Frontend mental model: colors. In RGB space, #ff0000 and #ee1111 sit close together and look
alike. An embedding is the same idea for meaning: texts that mean similar things get
coordinates that sit close together. A vector database is an index for "what's nearest?".
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

Embedder = Callable[[Sequence[str]], list[list[float]]]


def normalize(v: Sequence[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v))
    if n == 0:
        raise ValueError("cannot store a zero vector")
    return [x / n for x in v]


@dataclass(frozen=True)
class Record:
    id: str
    text: str
    vector: tuple[float, ...]
    meta: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Hit:
    id: str
    text: str
    score: float
    meta: dict


class VectorStore:
    """In-memory store. Vectors are normalized on insert, so a dot product is cosine similarity."""

    def __init__(self, dim: int):
        self.dim = dim
        self.records: dict[str, Record] = {}

    def upsert(self, id: str, text: str, vector: Sequence[float], meta: dict | None = None) -> None:
        if len(vector) != self.dim:
            raise ValueError(f"expected {self.dim} dimensions, got {len(vector)}")
        self.records[id] = Record(id, text, tuple(normalize(vector)), dict(meta or {}))

    def delete(self, id: str) -> None:
        self.records.pop(id, None)

    def query(self, vector: Sequence[float], k: int = 3, where: dict | None = None) -> list[Hit]:
        q = normalize(vector)
        where = where or {}
        hits = [Hit(r.id, r.text, sum(a * b for a, b in zip(q, r.vector)), r.meta)
                for r in self.records.values()
                if all(r.meta.get(key) == val for key, val in where.items())]   # metadata filter
        return sorted(hits, key=lambda h: h.score, reverse=True)[:k]

    # brute force is O(n) per query. Real vector DBs use approximate indexes (HNSW, IVF)
    # to stay fast at millions of vectors; the interface stays the same.

    def save(self, path: Path) -> None:
        data = {"dim": self.dim, "records": [r.__dict__ | {"vector": list(r.vector)}
                                             for r in self.records.values()]}
        Path(path).write_text(json.dumps(data), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "VectorStore":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        store = cls(data["dim"])
        for r in data["records"]:
            store.records[r["id"]] = Record(r["id"], r["text"], tuple(r["vector"]), r["meta"])
        return store


def sbert_embedder(model_name: str = "all-MiniLM-L6-v2") -> Embedder:
    """Local, free embeddings with sentence-transformers (https://www.sbert.net/)."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    return lambda texts: [list(map(float, v)) for v in model.encode(list(texts))]


NOTES = [
    ("n1", "Sensitivity to cold drinks can mean worn enamel or a cavity.", {"topic": "dental"}),
    ("n2", "Book a cleaning once a year; most insurance plans cover it.", {"topic": "dental"}),
    ("n3", "The clinic is closed on Sundays and public holidays.", {"topic": "admin"}),
    ("n4", "A sprained ankle should be rested, iced and elevated.", {"topic": "physio"}),
    ("n5", "Late cancellations cost a fee of $50.", {"topic": "admin"}),
]


def build_store(embed: Embedder) -> VectorStore:
    vectors = embed([text for _, text, _ in NOTES])
    store = VectorStore(len(vectors[0]))
    for (id_, text, meta), v in zip(NOTES, vectors):
        store.upsert(id_, text, v, meta)
    return store


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "my tooth hurts when I drink cold water"
    embed = sbert_embedder()
    store = build_store(embed)
    print(f"> {question}   ({store.dim} dimensions)")
    for hit in store.query(embed([question])[0], k=3):
        print(f"  {hit.score:.2f}  [{hit.meta['topic']}] {hit.text}")
