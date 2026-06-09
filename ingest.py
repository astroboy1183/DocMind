"""Ingest a document and print the stored chunks (uses real embeddings).

Usage:
    uv run python ingest.py [DOC_PATH]      # defaults to samples/hello.txt
"""

import sys

from docmind.ingest.embedder import SentenceTransformerEmbedder
from docmind.ingest.pipeline import ingest_file
from docmind.ingest.store import InMemoryStore


def main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else "samples/hello.txt"

    embedder = SentenceTransformerEmbedder()
    store = InMemoryStore()
    n = ingest_file(path, embedder, store)

    print(f"{n} chunks stored from {path}")
    for chunk, vector in store.all():
        print(f"  {chunk.chunk_id}  dim={len(vector)}  {chunk.text[:60]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
