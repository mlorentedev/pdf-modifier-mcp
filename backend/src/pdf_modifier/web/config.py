"""Pydantic Settings for web layer."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FeatureFlags(BaseSettings):
    """Feature flags for enabling/disabling capabilities."""

    model_config = SettingsConfigDict(
        env_prefix="FEATURE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    vision_enabled: bool = Field(
        default=False,
        description="Enable Vision/OCR features (requires NaN API key)",
    )
    ocr_enabled: bool = Field(
        default=False,
        description="Enable OCR endpoint (requires vision_enabled)",
    )
    signature_detection_enabled: bool = Field(
        default=False,
        description="Enable signature detection (requires vision_enabled)",
    )
    pdf_comparison_enabled: bool = Field(
        default=False,
        description="Enable PDF comparison (requires vision_enabled)",
    )

    @property
    def vision_available(self) -> bool:
        """Check if vision features are available."""
        return self.vision_enabled

    @property
    def ocr_available(self) -> bool:
        """Check if OCR is available."""
        return self.vision_enabled and self.ocr_enabled

    @property
    def signature_detection_available(self) -> bool:
        """Check if signature detection is available."""
        return self.vision_enabled and self.signature_detection_enabled

    @property
    def pdf_comparison_available(self) -> bool:
        """Check if PDF comparison is available."""
        return self.vision_enabled and self.pdf_comparison_enabled


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
        gt=0,
        description="Maximum upload file size in bytes (default: 100 MB)",
    )
    session_ttl_seconds: int = Field(
        default=3600,
        gt=0,
        description="Session TTL in seconds (default: 1 hour)",
    )
    log_level: str = Field(default="INFO", description="Logging level")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        description="Allowed CORS origins",
    )
