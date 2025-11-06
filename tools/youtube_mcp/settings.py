"""Environment driven settings for the YouTube MCP service."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration derived from environment variables."""

    cache_dir: Path = Field(default=Path(".ytmcp_cache"), description="Directory for cache database")
    cache_ttl_days: int = Field(default=14, ge=1, le=90, description="Cache TTL in days")
    allow_auto: bool = Field(default=True, description="Allow auto-generated captions")
    reject_private_or_unlisted: bool = Field(default=True, description="Reject private or unlisted videos")
    http_host: str = Field(default="127.0.0.1", description="HTTP server host")
    http_port: int = Field(default=8765, ge=1, le=65535, description="HTTP server port")

    model_config = SettingsConfigDict(env_prefix="YTMCP_", extra="ignore")

    @classmethod
    def from_env(cls) -> Settings:
        """Load settings using environment variables."""

        return cls()
