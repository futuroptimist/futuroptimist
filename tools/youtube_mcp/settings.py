"""Environment-driven configuration for the service."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="YTMCP_", extra="ignore")

    cache_dir: Path = Field(
        default=Path(".ytmcp_cache"),
        description="Directory used for transcript cache storage.",
    )
    cache_ttl_days: int = Field(
        default=14,
        description="Number of days cached transcripts remain valid.",
        ge=1,
        le=90,
    )
    allow_auto: bool = Field(
        default=True,
        description="Allow fallback to auto-generated captions when manual ones are unavailable.",
    )
    reject_private_or_unlisted: bool = Field(
        default=True,
        description="Reject private or unlisted videos instead of attempting to fetch captions.",
    )
    http_host: str = Field(default="127.0.0.1", description="Default HTTP bind host.")
    http_port: int = Field(default=8765, description="Default HTTP port.", ge=1, le=65535)


def from_env() -> Settings:
    """Load :class:`Settings` from the current environment."""

    return Settings()
