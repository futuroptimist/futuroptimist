"""Environment-driven configuration for the YouTube MCP service."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the transcript service."""

    cache_dir: Path = Field(default=Path(".ytmcp_cache"))
    cache_ttl_days: int = Field(default=14, ge=1, le=90)
    allow_auto: bool = Field(default=True)
    reject_private_or_unlisted: bool = Field(default=True)
    http_host: str = Field(default="127.0.0.1")
    http_port: int = Field(default=8765)

    model_config = SettingsConfigDict(env_prefix="YTMCP_", case_sensitive=False)

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings by reading the host environment."""

        return cls()
