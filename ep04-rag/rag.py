"""Episode 4: RAG in Python. Make an AI answer from your own documents.

    pip install openai
    set OPENAI_API_KEY, then:  python rag.py "Can I cancel the same day?"

Four steps: chunk, embed, retrieve, ground. Frontend mental model: you wouldn't ship the
whole database to a component; you fetch only the rows it needs and pass them as props.
Retrieval is that fetch, and the prompt is the props.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

MODEL = os.environ.get("MODEL", "gpt-4o-mini")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
DOCS = Path(__file__).parent / "docs"
NOT_FOUND = "I couldn't find that in the documents."

Embedder = Callable[[Sequence[str]], list[list[float]]]


def make_client():
    from openai import OpenAI
    return OpenAI()


@dataclass(frozen=True)
class Chunk:
    source: str
    text: str


# ---------------------------------------------------------------- 1. chunk
def chunk(text: str, size: int = 80, overlap: int = 20) -> list[str]:
    """Split into windows of `size` words that overlap by `overlap` words."""
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    words = text.split()
    if not words:
        return []
    step = size - overlap
    return [" ".join(words[i:i + size]) for i in range(0, max(len(words) - overlap, 1), step)]


def load_chunks(folder: Path = DOCS, size: int = 80, overlap: int = 20) -> list[Chunk]:
    out = []
    for path in sorted(folder.glob("*.md")):
        for part in chunk(path.read_text(encoding="utf-8"), size, overlap):
            out.append(Chunk(path.name, part))
    return out


# ---------------------------------------------------------------- 2. embed
def openai_embedder(client=None, model: str = EMBED_MODEL) -> Embedder:
    def embed(texts: Sequence[str]) -> list[list[float]]:
        c = client or make_client()
        return [d.embedding for d in c.embeddings.create(model=model, input=list(texts)).data]
    return embed


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


# ---------------------------------------------------------------- 3. retrieve
class Index:
    def __init__(self, chunks: list[Chunk], embed: Embedder):
        self.chunks, self.embed = chunks, embed
        self.vectors = embed([c.text for c in chunks]) if chunks else []

    def search(self, query: str, k: int = 3, min_score: float = 0.3) -> list[tuple[float, Chunk]]:
        q = self.embed([query])[0]
        scored = sorted(((cosine(q, v), c) for v, c in zip(self.vectors, self.chunks)),
                        key=lambda sc: sc[0], reverse=True)
        return [(s, c) for s, c in scored[:k] if s >= min_score]


# ---------------------------------------------------------------- 4. ground
def build_messages(question: str, hits: list[tuple[float, Chunk]]) -> list[dict]:
    sources = "\n\n".join(f"[{i}] ({c.source}) {c.text}" for i, (_, c) in enumerate(hits, 1))
    system = ("Answer only from the numbered sources. Cite them like [1]. "
              f"If the sources don't contain the answer, reply exactly: {NOT_FOUND}")
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"Sources:\n{sources}\n\nQuestion: {question}"}]


def answer(question: str, index: Index, client=None, model: str = MODEL) -> tuple[str, list]:
    hits = index.search(question)
    if not hits:                      # nothing relevant: don't let the model improvise
        return NOT_FOUND, []
    c = client or make_client()
    msg = c.chat.completions.create(model=model, messages=build_messages(question, hits))
    return msg.choices[0].message.content, hits


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Can I cancel my appointment on the same day?"
    client = make_client()
    index = Index(load_chunks(), openai_embedder(client))
    text, hits = answer(q, index, client)
    print(f"> {q}")
    for score, c in hits:
        print(f"  retrieved {score:.2f}  {c.source}: {c.text[:60]}...")
    print(text)
