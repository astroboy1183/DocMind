from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DOCMIND_", extra="ignore")

    # models (filled in properly in later phases)
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    llm_model: str = "claude-sonnet-4-6"
    anthropic_api_key: str | None = None

    # storage
    vector_db_path: str = "./.docmind/chroma"

    # chunking (Phase 1)
    chunk_size: int = 512
    chunk_overlap: int = 64

    # retrieval (Phase 2)
    retrieve_k: int = 30
    rerank_top_n: int = 5

    # ops
    log_level: str = "INFO"


settings = Settings()
