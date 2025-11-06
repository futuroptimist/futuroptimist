"""Pydantic models shared across interfaces."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class VideoMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="YouTube video identifier")
    url: str = Field(..., description="Canonical video URL")
    title: str | None = Field(default=None, description="Video title if known")
    channel: str | None = Field(default=None, description="Channel/author name")
    published_at: str | None = Field(default=None, description="ISO timestamp if known")
    duration: int | None = Field(default=None, description="Duration in seconds if known")


class CaptionTrack(BaseModel):
    model_config = ConfigDict(extra="ignore")

    lang: str = Field(..., description="BCP-47 language code")
    is_auto: bool = Field(..., description="True when auto-generated")
    name: str | None = Field(default=None, description="Track display name")
    track_id: str | None = Field(default=None, description="Internal track identifier")


class Segment(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    text: str
    start: float
    dur: float


class Chunk(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    text: str
    start: float
    end: float
    segment_ids: list[str] = Field(default_factory=list)
    cite_url: str


class TranscriptResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    video: VideoMetadata
    captions: CaptionTrack
    segments: list[Segment]
    chunks: list[Chunk]
    hash: str


class TranscriptRequest(BaseModel):
    url: str
    lang: str | None = None
    prefer_auto: bool | None = None


class TracksRequest(BaseModel):
    url: str


class TracksResponse(BaseModel):
    tracks: list[CaptionTrack]


class MetadataRequest(BaseModel):
    url: str


class HealthcheckResponse(BaseModel):
    ok: bool
    version: str


def dump_schema(model: type[BaseModel], path: Path) -> None:
    """Write the JSON schema for *model* into *path*."""

    path.write_text(json.dumps(model.model_json_schema(), indent=2))


def dump_schemas(target_dir: Path) -> None:
    """Write JSON schemas for the exposed tool models."""

    target_dir.mkdir(parents=True, exist_ok=True)
    dump_schema(TranscriptRequest, target_dir / "transcript.schema.json")
    dump_schema(TracksRequest, target_dir / "tracks.schema.json")
    dump_schema(MetadataRequest, target_dir / "metadata.schema.json")


__all__ = [
    "CaptionTrack",
    "Chunk",
    "HealthcheckResponse",
    "MetadataRequest",
    "Segment",
    "TracksRequest",
    "TracksResponse",
    "TranscriptRequest",
    "TranscriptResponse",
    "VideoMetadata",
    "dump_schemas",
]
