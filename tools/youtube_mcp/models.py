"""Pydantic models used by the YouTube MCP tool."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Base model enforcing repository-wide validation defaults."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class VideoInfo(StrictModel):
    """Basic metadata about a YouTube video."""

    id: str
    url: str
    title: str | None = None
    channel: str | None = Field(default=None, description="Channel or author name")
    published_at: str | None = Field(
        default=None,
        description="ISO-8601 timestamp when the video was published, if available.",
    )
    duration: int | None = Field(
        default=None,
        description="Approximate video duration in seconds, if available.",
    )


class CaptionTrackInfo(StrictModel):
    """Details about an available caption track."""

    lang: str
    is_auto: bool = Field(description="Whether the captions were auto-generated.")
    track_name: str | None = Field(
        default=None,
        description="Human-readable track name when supplied by YouTube.",
    )


class Segment(StrictModel):
    """Single caption segment as returned by YouTube."""

    id: str
    text: str
    start: float
    dur: float


class Chunk(StrictModel):
    """Normalized chunk suitable for retrieval workflows."""

    id: str
    text: str
    start: float
    end: float
    segment_ids: list[str]
    cite_url: str = Field(description="URL anchored to the chunk start time.")


class TranscriptResponse(StrictModel):
    """Full transcript payload returned by the service."""

    video: VideoInfo
    captions: CaptionTrackInfo
    segments: list[Segment]
    chunks: list[Chunk]
    hash: str = Field(description="Stable sha256 hash of metadata and transcript text.")


class TranscriptRequest(StrictModel):
    """Input model for transcript fetch requests."""

    url: str
    lang: str | None = Field(default=None, description="Preferred BCP47 language code.")
    prefer_auto: bool | None = Field(
        default=None,
        description="If true, prefer auto-generated captions when available.",
    )


class TracksRequest(StrictModel):
    """Input model for caption track discovery."""

    url: str


class MetadataRequest(StrictModel):
    """Input model for metadata fetch requests."""

    url: str


class TracksResponse(StrictModel):
    """Caption track listing response."""

    tracks: list[CaptionTrackInfo]


class MetadataResponse(StrictModel):
    """Video metadata response."""

    id: str
    url: str
    title: str | None = None
    channel: str | None = None
    published_at: str | None = None
    duration: int | None = None


class HealthResponse(StrictModel):
    """Healthcheck payload."""

    ok: bool
    version: str
