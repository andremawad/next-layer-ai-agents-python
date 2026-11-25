"""Tests for Episode 4. No API key: a bag-of-words fake embedder and a fake LLM.  Run:  pytest -q"""
import math
import re
from types import SimpleNamespace

import pytest

import rag

VOCAB = ["cancel", "fee", "hours", "open", "insurance", "card", "parking", "sunday"]


def fake_embed(texts):
    """Counts of a few words: enough to make similar texts point the same way."""
    out = []
    for t in texts:
        words = re.findall(r"[a-z]+", t.lower())
        out.append([float(sum(w.startswith(v) for w in words)) for v in VOCAB])
    return out


class FakeLLM:
    def __init__(self, text):
        self.text, self.requests = text, []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.text))])


def test_chunk_windows_overlap():
    text = " ".join(f"w{i}" for i in range(10))
    parts = rag.chunk(text, size=4, overlap=2)
    assert parts[0] == "w0 w1 w2 w3" and parts[1] == "w2 w3 w4 w5"
    assert parts[-1].endswith("w9")


def test_chunk_rejects_bad_overlap():
    with pytest.raises(ValueError):
        rag.chunk("a b c", size=2, overlap=2)


def test_cosine_basics():
    assert rag.cosine([1, 0], [1, 0]) == pytest.approx(1.0)
    assert rag.cosine([1, 0], [0, 1]) == pytest.approx(0.0)
    assert rag.cosine([0, 0], [1, 1]) == 0.0
    assert rag.cosine([1, 1], [2, 2]) == pytest.approx(1.0) and not math.isnan(rag.cosine([1], [1]))


def test_retrieval_finds_the_right_document():
    index = rag.Index(rag.load_chunks(), fake_embed)
    hits = index.search("Is there a fee if I cancel?")
    assert hits and hits[0][1].source == "cancellation-policy.md"


def test_answer_is_grounded_and_cites_sources():
    index = rag.Index(rag.load_chunks(), fake_embed)
    llm = FakeLLM("Same-day cancellations cost $50 [1].")
    text, hits = rag.answer("cancel fee?", index, client=llm)
    prompt = llm.requests[0]["messages"]
    assert "Answer only from the numbered sources" in prompt[0]["content"]
    assert "[1] (cancellation-policy.md)" in prompt[1]["content"]
    assert "[1]" in text


def test_no_relevant_chunk_means_no_llm_call():
    index = rag.Index(rag.load_chunks(), fake_embed)
    llm = FakeLLM("should not be called")
    text, hits = rag.answer("What's the capital of Peru?", index, client=llm)
    assert text == rag.NOT_FOUND and hits == [] and llm.requests == []
