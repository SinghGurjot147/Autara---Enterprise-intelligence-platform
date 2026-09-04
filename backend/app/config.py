"""
Centralized settings, loaded once from environment variables / .env.
Reused by every module below instead of each one reading os.environ itself.
"""
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)

    # Gemini â€” reuse the same key/model your existing chat & RAG backend uses.
    gemini_api_key: str = ""
    google_api_key_1: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Optional free image provider (Pexels). If blank, the renderer falls back
    # to clean image-free layouts automatically â€” generation never fails for this reason.
    pexels_api_key: str = ""

    # CORS â€” comma-separated list of allowed frontend origins.
    cors_origins: str = "http://localhost:5173"

    # Storage for generated files. Only ever written with server-generated UUID names.
    presentations_dir: str = "generated/presentations"

    # Guardrails
    max_topic_length: int = 400
    min_slides: int = 3
    max_slides: int = 30

    # Integration seam for RAG mode. See services/rag_context.py.
    rag_query_url: str = ""

    @property
    def effective_gemini_api_key(self) -> str:
        """Reuse the existing project key; supports both names."""
        return self.gemini_api_key or self.google_api_key_1

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def presentations_path(self) -> Path:
        p = Path(self.presentations_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()

