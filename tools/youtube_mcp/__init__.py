"""YouTube transcript MCP service."""
from __future__ import annotations

from importlib import metadata

try:
    __version__ = metadata.version("futuroptimist-youtube-mcp")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.0"

__all__ = ["__version__"]
