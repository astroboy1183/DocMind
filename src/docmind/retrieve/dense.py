import numpy as np

from docmind.ingest.embedder import Embedder
from docmind.ingest.store import VectorStore
from docmind.types import Chunk, Passage


def dense_search(query: str, embedder: Embedder, store: VectorStore, k: int = 5) -> list[Passage]:
    """Embed the query, cosine-rank every stored chunk, return the top-k passages.

    Uses the SAME embedder the documents were ingested with — a query/doc model
    mismatch silently wrecks relevance, so callers must pass the ingest embedder.
    """
    rows = store.all()
    if not rows:
        return []

    chunks: list[Chunk] = [chunk for chunk, _ in rows]
    matrix = np.array([vec for _, vec in rows], dtype=np.float32)
    query_vec = np.array(embedder.embed([query])[0], dtype=np.float32)

    # full cosine (robust even if vectors aren't normalized — keeps fakes testable)
    denom = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query_vec)
    denom[denom == 0] = 1e-9
    scores = matrix @ query_vec / denom

    top = np.argsort(-scores)[:k]
    return [Passage(chunk=chunks[i], score=float(scores[i])) for i in top]
