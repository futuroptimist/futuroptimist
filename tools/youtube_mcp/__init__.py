"""YouTube transcript MCP integration package."""

from __future__ import annotations

from .models import (
    CaptionTrackInfo,
    Chunk,
    HealthResponse,
    MetadataRequest,
    MetadataResponse,
    TracksRequest,
    TracksResponse,
    TranscriptRequest,
    TranscriptResponse,
    VideoInfo,
)
from .settings import Settings
from .youtube_client import YouTubeTranscriptService

__all__ = [
    "CaptionTrackInfo",
    "Chunk",
    "HealthResponse",
    "MetadataRequest",
    "MetadataResponse",
    "Settings",
    "TracksRequest",
    "TracksResponse",
    "TranscriptRequest",
    "TranscriptResponse",
    "VideoInfo",
    "YouTubeTranscriptService",
]

__version__ = "0.1.0"
