"""Ingest a document, then run hybrid retrieval over it and print ranked hits.

Usage:
    uv run python retrieval.py "your question" [DOC_PATH]

Note: InMemoryStore lives only for this process, so this script must ingest AND
retrieve in one run. Once the store is persistent (Chroma, later phase), a
separate ingest.py could populate the DB and this script just query it.
"""

import sys

from docmind.ingest.embedder import SentenceTransformerEmbedder
from docmind.ingest.pipeline import ingest_file
from docmind.ingest.store import InMemoryStore
from docmind.retrieve.rerank import CrossEncoderReranker
from docmind.retrieve.retriever import Retriever


def main(argv: list[str]) -> int:
    query = argv[1] if len(argv) > 1 else "How does the system avoid hallucinating answers?"
    path = argv[2] if len(argv) > 2 else "samples/hello.txt"

    embedder = SentenceTransformerEmbedder()  # SAME embedder for docs + query
    store = InMemoryStore()
    ingest_file(path, embedder, store)

    retriever = Retriever(embedder, store, reranker=CrossEncoderReranker())
    results = retriever.search(query, k=5, top_n=3)

    print(f"query: {query!r}\n")
    for rank, passage in enumerate(results, start=1):
        print(f"{rank}. score={passage.score:.3f}  {passage.chunk.chunk_id}")
        print(f"   {passage.chunk.text[:90]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
