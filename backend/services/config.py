import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    app_env: str = "development"
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    upload_dir: Path = BASE_DIR / "uploads"
    chroma_dir: Path = BASE_DIR / "vectordb" / "chroma"
    model_cache_dir: Path = BASE_DIR / "vectordb" / "model_cache"
    metadata_path: Path = BASE_DIR / "vectordb" / "documents.json"
    metrics_path: Path = BASE_DIR / "vectordb" / "metrics.json"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = ""#cross-encoder/ms-marco-MiniLM-L-6-v2
    llm_temperature: float = 0.1
    llm_timeout_seconds: int = 120
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash-lite"
    chunk_size: int = 500
    chunk_overlap: int = 100
    max_upload_size_mb: int = 25
    max_upload_files: int = 10
    supported_extensions: set[str] = {".pdf", ".docx", ".txt", ".csv"}


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    settings.model_cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(settings.model_cache_dir / "huggingface"))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(settings.model_cache_dir / "transformers"))
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(settings.model_cache_dir / "sentence_transformers"))
    # os.environ.setdefault("HF_HUB_OFFLINE", "1")
    # os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    return settings


settings = get_settings()
