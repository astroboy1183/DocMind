from pathlib import Path

from docmind.config import settings
from docmind.ingest.chunker import chunk_text
from docmind.ingest.embedder import Embedder
from docmind.ingest.store import VectorStore


def ingest_file(path: str, embedder: Embedder, store: VectorStore) -> int:
    """Load → chunk → embed → store. Returns number of chunks stored."""
    text = Path(path).read_text(encoding="utf-8")
    doc_id = Path(path).stem

    chunks = chunk_text(
        text, doc_id=doc_id, size=settings.chunk_size, overlap=settings.chunk_overlap
    )
    vectors = embedder.embed([c.text for c in chunks])
    store.upsert(chunks, vectors)
    return len(chunks)
