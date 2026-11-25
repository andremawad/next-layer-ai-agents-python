"""Tests for Episode 5. No model download: hand-made vectors.  Run:  pytest -q"""
import math

import pytest

from vector_store import NOTES, VectorStore, build_store, normalize


def colors():
    """RGB colors as 3-D 'embeddings': the frontend intuition from the video."""
    s = VectorStore(dim=3)
    s.upsert("red", "red", [255, 0, 0], {"warm": True})
    s.upsert("crimson", "crimson", [220, 20, 60], {"warm": True})
    s.upsert("blue", "blue", [0, 0, 255], {"warm": False})
    return s


def test_normalize_gives_unit_length():
    assert math.isclose(sum(x * x for x in normalize([3, 4])), 1.0)
    with pytest.raises(ValueError):
        normalize([0, 0])


def test_nearest_neighbour_is_the_similar_color():
    hits = colors().query([250, 10, 10], k=2)
    assert [h.id for h in hits] == ["red", "crimson"]
    assert hits[0].score > 0.99


def test_metadata_filter_runs_with_similarity():
    hits = colors().query([255, 0, 0], k=3, where={"warm": False})
    assert [h.id for h in hits] == ["blue"]


def test_dimension_mismatch_is_rejected():
    with pytest.raises(ValueError):
        colors().upsert("bad", "bad", [1, 2])


def test_upsert_replaces_and_delete_removes():
    s = colors()
    s.upsert("red", "red v2", [255, 0, 0])
    assert s.records["red"].text == "red v2" and len(s.records) == 3
    s.delete("red")
    assert "red" not in s.records


def test_save_and_load_round_trip(tmp_path):
    s = colors()
    s.save(tmp_path / "store.json")
    loaded = VectorStore.load(tmp_path / "store.json")
    assert [h.id for h in loaded.query([0, 0, 200])] == [h.id for h in s.query([0, 0, 200])]


def test_build_store_with_fake_embedder():
    fake = lambda texts: [[1.0 + i, float(len(t)), 1.0] for i, t in enumerate(texts)]
    store = build_store(fake)
    assert store.dim == 3 and len(store.records) == len(NOTES)
