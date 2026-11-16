from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./storage/edusphere.db"
    llm_provider: str = "mock"
    groq_api_key: SecretStr | None = None
    groq_model: str = "openai/gpt-oss-120b"
    gemini_use_vertex: bool = False
    gemini_api_key: str | None = None
    gemini_text_model: str = "gemini-3.8-flash"
    gemini_json_model: str = "gemini-3.8-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    groq_base_url: str = "https://api.groq.com"
    vertex_project: str | None = Field(default=None, validation_alias=AliasChoices("GOOGLE_CLOUD_PROJECT", "VERTEX_PROJECT"))
    vertex_location: str = Field(default="global", validation_alias=AliasChoices("GOOGLE_CLOUD_LOCATION", "VERTEX_LOCATION"))
    vertex_text_model: str = "gemini-3.8-flash"
    vertex_json_model: str = "gemini-3.8-flash"
    vertex_embedding_model: str = "gemini-embedding-001"
    google_application_credentials: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    retrieval_min_similarity: float = 0.55
    storage_dir: str = "storage"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    log_level: str = "INFO"
    app_version: str = "0.1.0"
    # Test/dev convenience only. Real databases are created by `make migrate` (Alembic).
    auto_create_tables: bool = False

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
