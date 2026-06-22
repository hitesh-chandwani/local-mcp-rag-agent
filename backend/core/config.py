"""
Application settings loaded from environment variables and .env file.
Supports OpenAI, Anthropic, Grok, and Ollama providers out-of-the-box.
"""
from functools import lru_cache
from typing import List, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────
    app_name: str = "local-mcp-rag-agent"
    app_version: str = "0.1.0"
    environment: Literal["development", "production"] = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ── LLM Provider ─────────────────────────────────────────────────────
    llm_provider: Literal["openai", "anthropic", "grok", "ollama"] = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048

    # Provider API keys (only the relevant one is required at runtime)
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    grok_api_key: Optional[str] = Field(default=None)

    # Ollama (local LLM – no key needed)
    ollama_base_url: str = "http://localhost:11434"

    # ── RAG ──────────────────────────────────────────────────────────────
    vector_db: Literal["chroma", "lancedb"] = "chroma"
    chroma_persist_dir: str = "./data/chroma"
    lancedb_uri: str = "./data/lancedb"
    collection_name: str = "documents"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    chunk_size: int = 800
    chunk_overlap: int = 150
    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.35

    # ── MCP ──────────────────────────────────────────────────────────────
    mcp_config_path: str = "./mcp_servers.json"
    mcp_timeout: int = 30

    # ── Security ─────────────────────────────────────────────────────────
    api_key: Optional[str] = Field(default=None, description="Optional bearer token to protect the API")
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
