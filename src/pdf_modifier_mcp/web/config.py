"""Pydantic Settings for web layer."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WebSettings(BaseSettings):
    """Web layer configuration."""

    model_config = SettingsConfigDict(
        env_prefix="WEB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    storage_dir: Path = Field(
        default=Path("storage"),
        description="Directory for storing uploaded PDFs",
    )
    max_file_size: int = Field(
        default=100 * 1024 * 1024,
        description="Maximum upload file size in bytes (default: 100 MB)",
    )
    session_ttl_seconds: int = Field(
        default=3600,
        description="Session TTL in seconds (default: 1 hour)",
    )
    log_level: str = Field(default="INFO", description="Logging level")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        description="Allowed CORS origins",
    )
