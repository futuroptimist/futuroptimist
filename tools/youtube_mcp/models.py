"""Pydantic models for the YouTube MCP transcript tooling."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    id: str
    url: str
    title: str | None = None
    channel: str | None = None
    published_at: str | None = None
    duration: int | None = None


class CaptionTrack(BaseModel):
    lang: str
    is_auto: bool = Field(default=False)
    name: str | None = None
    track_id: str | None = None


class TranscriptSegment(BaseModel):
    id: str
    text: str
    start: float
    dur: float


class TranscriptChunk(BaseModel):
    id: str
    text: str
    start: float
    end: float
    segment_ids: list[str]
    cite_url: str


class TranscriptResponse(BaseModel):
    video: VideoMetadata
    captions: CaptionTrack
    segments: list[TranscriptSegment]
    chunks: list[TranscriptChunk]
    hash: str


class TracksResponse(BaseModel):
    tracks: list[CaptionTrack]


class MetadataResponse(VideoMetadata):
    pass


class HealthResponse(BaseModel):
    ok: bool
    version: str


SCHEMA_FILES = {
    "transcript.schema.json": TranscriptResponse,
    "tracks.schema.json": TracksResponse,
    "metadata.schema.json": MetadataResponse,
}


def write_schemas(schema_dir: Path) -> None:
    """Write JSON Schema representations for the exposed tool payloads."""

    schema_dir.mkdir(parents=True, exist_ok=True)
    for filename, model in SCHEMA_FILES.items():
        schema_path = schema_dir / filename
        schema_path.write_text(
            json.dumps(model.model_json_schema(mode="validation"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


__all__ = [
    "CaptionTrack",
    "HealthResponse",
    "MetadataResponse",
    "TracksResponse",
    "TranscriptChunk",
    "TranscriptResponse",
    "TranscriptSegment",
    "VideoMetadata",
    "write_schemas",
]
