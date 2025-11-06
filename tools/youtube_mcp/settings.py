"""Environment-driven configuration for the YouTube MCP tooling."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the transcript service.

    Values are read from environment variables prefixed with ``YTMCP_``.
    """

    cache_dir: Path = Field(default=Path(".ytmcp_cache"), alias="YTMCP_CACHE_DIR")
    cache_ttl_days: PositiveInt = Field(default=14, alias="YTMCP_CACHE_TTL_DAYS")
    allow_auto: bool = Field(default=True, alias="YTMCP_ALLOW_AUTO")
    reject_private_or_unlisted: bool = Field(
        default=True, alias="YTMCP_REJECT_PRIVATE_OR_UNLISTED"
    )
    http_host: str = Field(default="127.0.0.1", alias="YTMCP_HTTP_HOST")
    http_port: int = Field(default=8765, alias="YTMCP_HTTP_PORT")

    model_config = SettingsConfigDict(env_prefix="", populate_by_name=True)

    @classmethod
    @lru_cache(maxsize=1)
    def from_env(cls, **overrides: object) -> Settings:
        """Return settings using environment variables (cached)."""

        return cls(**overrides)

    def ensure_cache_dir(self) -> Path:
        """Ensure the cache directory exists and return it."""

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Convenience accessor used by module-level consumers."""

    return Settings.from_env()


__all__ = ["Settings", "get_settings"]
