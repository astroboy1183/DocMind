from pathlib import Path

import anthropic
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Generation runs on Claude. Swap to claude-opus-4-8 (most capable) or
# claude-haiku-4-5 (cheapest/fastest) by changing this one line.
CLAUDE_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

# Embeddings stay on OpenAI (text-embedding-3-small) — must match index.py,
# or retrieval silently breaks (query/doc embedding-model mismatch).
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_db = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    url="http://localhost:6333",
    collection_name="node_js_guide",
)


def process_query(query: str) -> str:
    search_results = vector_db.similarity_search_with_score(query=query, k=8)

    # Filter out low relevance chunks (score < 0.3)
    relevant = [(doc, score) for doc, score in search_results if score >= 0.3]

    if not relevant:
        relevant = search_results[:3]

    context = "\n\n".join([
        f"Page Content: {doc.page_content}\n"
        f"Page Number: {doc.metadata.get('page_label', doc.metadata.get('page', '?'))}\n"
        f"Relevance Score: {score:.2f}"
        for doc, score in relevant
    ])

    SYSTEM_PROMPT = f"""You are a helpful AI Assistant answering questions about a Node.js guide PDF.

Use the context below to answer the user's question as thoroughly as possible.
Always cite the page number(s) where the information was found.
If the context covers the topic partially, answer what you can and mention what is covered.
Only say you don't know if the topic is completely absent from the context.

Context:
{context}"""

    # Claude differs from OpenAI: system prompt is a top-level param (not a
    # message), max_tokens is required, and the reply is a list of content
    # blocks rather than choices[0].message.
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": query}],
    )

    return "".join(block.text for block in response.content if block.type == "text")
