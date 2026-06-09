import re

from rank_bm25 import BM25Okapi

from docmind.ingest.store import VectorStore
from docmind.types import Chunk, Passage

_TOKEN = re.compile(r"\w+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def keyword_search(query: str, store: VectorStore, k: int = 5) -> list[Passage]:
    """BM25 keyword ranking over chunk text — catches exact terms, names, codes
    that dense embeddings can blur.

    Builds the index per call: fine for the Phase-2 in-memory store; a persistent
    store would cache the index instead.
    """
    rows = store.all()
    if not rows:
        return []

    chunks: list[Chunk] = [chunk for chunk, _ in rows]
    bm25 = BM25Okapi([_tokenize(chunk.text) for chunk in chunks])
    scores = bm25.get_scores(_tokenize(query))

    order = sorted(range(len(chunks)), key=lambda i: -scores[i])[:k]
    return [Passage(chunk=chunks[i], score=float(scores[i])) for i in order]
