"""Pydantic models for the YouTube MCP service."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CaptionTrack(BaseModel):
    """Caption track metadata."""

    model_config = ConfigDict(extra="forbid")

    lang: str = Field(..., description="IETF language code for the caption track.")
    is_auto: bool = Field(..., description="Whether the track is auto-generated.")
    name: Optional[str] = Field(
        default=None,
        description="Track display name provided by YouTube, when available.",
    )


class VideoInfo(BaseModel):
    """Metadata about a YouTube video."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Canonical YouTube video identifier.")
    url: str = Field(..., description="Public watch URL for the video.")
    title: Optional[str] = Field(default=None, description="Video title, if known.")
    channel: Optional[str] = Field(
        default=None, description="Channel/author name for the video, if known."
    )
    published_at: Optional[str] = Field(
        default=None, description="ISO 8601 publication date, if available."
    )
    duration: Optional[int] = Field(
        default=None,
        description="Duration of the video in seconds, if available without extra auth.",
    )


class TranscriptSegment(BaseModel):
    """Normalized caption segment."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Deterministic identifier for the segment.")
    text: str = Field(..., description="Normalized text content of the segment.")
    start: float = Field(..., description="Start time (seconds) of the segment.")
    dur: float = Field(..., description="Duration (seconds) of the segment.")


class TranscriptChunk(BaseModel):
    """Chunk of transcript segments sized for retrieval."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Deterministic identifier for the chunk.")
    text: str = Field(..., description="Concatenated text for the chunk.")
    start: float = Field(..., description="Chunk start time (seconds).")
    end: float = Field(..., description="Chunk end time (seconds).")
    segment_ids: List[str] = Field(
        ..., description="Ordered list of segment identifiers contained in the chunk."
    )
    cite_url: str = Field(
        ..., description="YouTube watch URL with a timestamp for citation provenance."
    )


class TranscriptResponse(BaseModel):
    """Full transcript response including metadata and chunking."""

    model_config = ConfigDict(extra="forbid")

    video: VideoInfo
    captions: CaptionTrack
    segments: List[TranscriptSegment]
    chunks: List[TranscriptChunk]
    hash: str = Field(
        ..., description="SHA-256 hash of normalized transcript content and metadata."
    )


class TracksResponse(BaseModel):
    """Response describing available caption tracks for a video."""

    model_config = ConfigDict(extra="forbid")

    tracks: List[CaptionTrack]


class MetadataResponse(VideoInfo):
    """Alias for returning video metadata via HTTP/MCP."""

    pass


class HealthResponse(BaseModel):
    """Healthcheck payload for HTTP and MCP endpoints."""

    model_config = ConfigDict(extra="forbid")

    ok: bool
    version: str


class TranscriptRequest(BaseModel):
    """Input payload for transcript retrieval."""

    model_config = ConfigDict(extra="forbid")

    url: str
    lang: Optional[str] = None
    prefer_auto: Optional[bool] = None


class TracksRequest(BaseModel):
    """Input payload for listing caption tracks."""

    model_config = ConfigDict(extra="forbid")

    url: str


class MetadataRequest(BaseModel):
    """Input payload for metadata retrieval."""

    model_config = ConfigDict(extra="forbid")

    url: str


def write_schemas(base_path: Path) -> None:
    """Write JSON schemas for MCP tooling to ``base_path``."""

    base_path.mkdir(parents=True, exist_ok=True)
    schemas = {
        "transcript.schema.json": {
            "input": TranscriptRequest.model_json_schema(),
            "output": TranscriptResponse.model_json_schema(),
        },
        "tracks.schema.json": {
            "input": TracksRequest.model_json_schema(),
            "output": TracksResponse.model_json_schema(),
        },
        "metadata.schema.json": {
            "input": MetadataRequest.model_json_schema(),
            "output": MetadataResponse.model_json_schema(),
        },
    }
    for name, schema in schemas.items():
        path = base_path / name
        path.write_text(
            json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
