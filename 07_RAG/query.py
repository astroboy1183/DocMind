from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from openai import OpenAI

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

client = OpenAI()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_db = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    url="http://localhost:6333",
    collection_name="node_js_guide",
)

print("RAG Query — Node.js Guide  (type 'quit' to exit)\n")

while True:
    user_query = input("Ask something: ").strip()

    if not user_query or user_query.lower() in ("quit", "exit"):
        break

    # Relevant chunks from the vector db
    search_results = vector_db.similarity_search(query=user_query)

    context = "\n\n".join([
        f"Page Content: {result.page_content}\n"
        f"Page Number: {result.metadata.get('page_label', result.metadata.get('page', '?'))}\n"
        f"File Location: {result.metadata.get('source', 'N/A')}"
        for result in search_results
    ])

    SYSTEM_PROMPT = f"""You are a helpful AI Assistant who answers user queries based on the
available context retrieved from a PDF file along with page contents and page numbers.

Context:
{context}

Always mention the page number when referencing information from the document.
If the answer is not in the context, say you don't know."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ],
    )

    print(f"\nAssistant: {response.choices[0].message.content}\n")
