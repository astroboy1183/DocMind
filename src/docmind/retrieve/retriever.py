from docmind.config import settings
from docmind.ingest.embedder import Embedder
from docmind.ingest.store import VectorStore
from docmind.retrieve.dense import dense_search
from docmind.retrieve.hybrid import reciprocal_rank_fusion
from docmind.retrieve.keyword import keyword_search
from docmind.retrieve.rerank import CrossEncoderReranker
from docmind.types import Passage


def _matches(metadata: dict, filters: dict) -> bool:
    """A chunk passes if every filter key equals the chunk's metadata value."""
    return all(metadata.get(key) == value for key, value in filters.items())


class Retriever:
    """Hybrid retrieval facade.

    Pipeline: embed query → dense + keyword → RRF fuse → metadata filter →
    (optional) cross-encoder rerank → top-n. Every stage sits behind this one
    search() shape so strategies stay swappable.
    """

    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        reranker: CrossEncoderReranker | None = None,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._reranker = reranker

    def search(
        self,
        query: str,
        k: int | None = None,
        top_n: int | None = None,
        filters: dict | None = None,
    ) -> list[Passage]:
        k = k or settings.retrieve_k
        top_n = top_n or settings.rerank_top_n

        dense = dense_search(query, self._embedder, self._store, k=k)
        keyword = keyword_search(query, self._store, k=k)
        fused = reciprocal_rank_fusion([dense, keyword])

        if filters:
            fused = [p for p in fused if _matches(p.chunk.metadata, filters)]

        # Rerank the wide candidate set down to top_n when a reranker is wired;
        # otherwise just take the top_n fused hits.
        if self._reranker is not None:
            return self._reranker.rerank(query, fused[:k], top_n=top_n)
        return fused[:top_n]
