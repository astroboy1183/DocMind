"""Deterministic retrieval tests — no model downloads.

Dense ranking is checked with a stub embedder (hand-set vectors); BM25 and RRF
are pure/deterministic, so they run for real. The cross-encoder reranker needs a
model download, so it's exercised in the manual validation run, not here.
"""

from docmind.ingest.store import InMemoryStore
from docmind.retrieve.dense import dense_search
from docmind.retrieve.hybrid import reciprocal_rank_fusion
from docmind.retrieve.keyword import keyword_search
from docmind.retrieve.retriever import Retriever
from docmind.types import Chunk, Passage


class StubEmbedder:
    """Fixed phrase → fixed vector, so dense ranking is deterministic (no model)."""

    _table = {"cat query": [1.0, 0.0], "dog query": [0.0, 1.0]}

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._table[t] for t in texts]


def _store_with_two_chunks() -> InMemoryStore:
    store = InMemoryStore()
    chunks = [
        Chunk(chunk_id="d:0", doc_id="d", text="all about cats", metadata={"animal": "cat"}),
        Chunk(chunk_id="d:1", doc_id="d", text="all about dogs", metadata={"animal": "dog"}),
    ]
    store.upsert(chunks, [[1.0, 0.0], [0.0, 1.0]])  # cat-vec, dog-vec
    return store


def test_dense_search_ranks_by_cosine():
    results = dense_search("cat query", StubEmbedder(), _store_with_two_chunks(), k=2)
    assert results[0].chunk.chunk_id == "d:0"  # nearest the cat vector
    assert results[0].score > results[1].score  # ranked descending


def test_dense_search_empty_store_returns_empty():
    assert dense_search("cat query", StubEmbedder(), InMemoryStore(), k=5) == []


def test_keyword_search_finds_exact_term():
    # BM25 needs a non-degenerate corpus: a term in ~half the docs gets IDF≈0.
    store = InMemoryStore()
    texts = ["all about cats", "all about dogs", "all about birds", "all about fish"]
    chunks = [Chunk(chunk_id=f"d:{i}", doc_id="d", text=t) for i, t in enumerate(texts)]
    store.upsert(chunks, [[0.0]] * len(chunks))  # vectors irrelevant to keyword search

    results = keyword_search("dogs", store, k=4)
    assert results[0].chunk.chunk_id == "d:1"  # the chunk literally about dogs


def test_rrf_fuses_and_dedupes():
    a = Chunk(chunk_id="a", doc_id="d", text="a")
    b = Chunk(chunk_id="b", doc_id="d", text="b")
    list1 = [Passage(chunk=a, score=9.0), Passage(chunk=b, score=8.0)]
    list2 = [Passage(chunk=b, score=1.0), Passage(chunk=a, score=0.5)]

    fused = reciprocal_rank_fusion([list1, list2])

    assert {p.chunk.chunk_id for p in fused} == {"a", "b"}  # deduped
    assert fused[0].chunk.chunk_id == "a"  # rank-1 in list1 + rank-2 in list2 wins


def test_retriever_metadata_filter_excludes_nonmatching():
    retriever = Retriever(StubEmbedder(), _store_with_two_chunks())
    results = retriever.search("cat query", k=10, top_n=10, filters={"animal": "dog"})
    assert [p.chunk.chunk_id for p in results] == ["d:1"]


def test_retriever_facade_returns_ranked_passages():
    retriever = Retriever(StubEmbedder(), _store_with_two_chunks())
    results = retriever.search("dog query", k=10, top_n=1)
    assert len(results) == 1
    assert results[0].chunk.chunk_id == "d:1"
