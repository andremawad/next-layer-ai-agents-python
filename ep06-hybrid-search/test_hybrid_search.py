"""Tests for Episode 6. No model download: a tiny 'meaning' embedder.  Run:  pytest -q"""
import pytest

from hybrid_search import BM25, DOCS, HybridSearch, min_max, rrf, tokenize

# hand-made "meaning" axes: sync problems, storage, account/profile
CONCEPTS = {
    "sync": 0, "syncing": 0, "updating": 0, "devices": 0, "laptop": 0, "phone": 0, "token": 0,
    "disk": 1, "space": 1, "full": 1, "upload": 1,
    "profile": 2, "photo": 2, "settings": 2, "sign": 2,
}


def fake_embed(texts):
    out = []
    for t in texts:
        v = [0.0, 0.0, 0.0]
        for w in tokenize(t):
            if w in CONCEPTS:
                v[CONCEPTS[w]] += 1
        out.append(v)
    return out


@pytest.fixture
def hs():
    return HybridSearch(DOCS, fake_embed)


def test_bm25_prefers_exact_rare_terms():
    scores = BM25(DOCS).scores("E1042")
    assert scores.index(max(scores)) == 0 and scores[2] == 0


def test_keyword_wins_on_exact_codes(hs):
    assert hs.search("E1042", alpha=0.0, k=1)[0][1].startswith("Error E1042")


def test_vector_wins_on_paraphrase(hs):
    q = "files not updating between laptop and phone"
    assert "re-authenticate" in hs.search(q, alpha=1.0, k=1)[0][1]


def test_hybrid_keeps_both_signals(hs):
    top2 = [d for _, d in hs.search("E1042 syncing devices", alpha=0.5, k=2)]
    assert any(d.startswith("Error E1042") for d in top2)
    assert any("re-authenticate" in d for d in top2)


def test_alpha_must_be_explicit_and_in_range(hs):
    with pytest.raises(TypeError):
        hs.search("E1042")                    # no default alpha, on purpose
    with pytest.raises(ValueError):
        hs.search("E1042", alpha=1.5)


def test_min_max_and_rrf():
    assert min_max([2, 4, 6]) == [0.0, 0.5, 1.0] and min_max([3, 3]) == [0.0, 0.0]
    assert rrf([[1, 2, 3], [3, 1, 2]])[0] == 1
