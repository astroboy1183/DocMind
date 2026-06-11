from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

PDF_PATH = Path(__file__).parent / "data" / "PDF-Guide-Node-Andrew-Mead-v3.pdf"

# ── Load ───────────────────────────────────────────────────────────────────────

loader = PyPDFLoader(str(PDF_PATH))
pages = loader.load()

print(f"Loaded {len(pages)} pages from '{PDF_PATH.name}'")

# ── Chunk ──────────────────────────────────────────────────────────────────────

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
)

chunks = splitter.split_documents(pages)

print(f"Split into {len(chunks)} chunks")

# ── Embed & store in Qdrant ────────────────────────────────────────────────────

print("Embedding chunks and uploading to Qdrant...")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    url="http://localhost:6333",
    collection_name="node_js_guide",
)

print("Done. Collection 'node_js_guide' is ready in Qdrant.")
