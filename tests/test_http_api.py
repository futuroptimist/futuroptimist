from __future__ import annotations

from fastapi.testclient import TestClient

from tools.youtube_mcp.errors import NoCaptionsAvailable
from tools.youtube_mcp.http_server import create_app
from tools.youtube_mcp.models import (
    CaptionTrack,
    TranscriptChunk,
    TranscriptResponse,
    TranscriptSegment,
    VideoInfo,
)
from tools.youtube_mcp.settings import Settings


def _sample_response() -> TranscriptResponse:
    video = VideoInfo(
        id="video123",
        url="https://www.youtube.com/watch?v=video123",
        title="Example",
        channel="Channel",
        published_at=None,
        duration=None,
    )
    segments = [
        TranscriptSegment(id="seg-1", text="hello world", start=0.0, dur=3.0),
    ]
    chunks = [
        TranscriptChunk(
            id="video123-chunk-0001",
            text="hello world",
            start=0.0,
            end=3.0,
            segment_ids=["seg-1"],
            cite_url="https://www.youtube.com/watch?v=video123&t=0s",
        )
    ]
    return TranscriptResponse(
        video=video,
        captions=CaptionTrack(lang="en", is_auto=False, name="English"),
        segments=segments,
        chunks=chunks,
        hash="deadbeef",
    )


class DummyService:
    def __init__(self) -> None:
        self.settings = Settings()

    def get_transcript(self, url: str, lang: str | None = None, prefer_auto: bool | None = None) -> TranscriptResponse:
        return _sample_response()

    def list_tracks(self, url: str):
        return [CaptionTrack(lang="en", is_auto=False, name="English")]

    def get_metadata(self, url: str):
        return _sample_response().video


class ErrorService(DummyService):
    def get_transcript(self, url: str, lang: str | None = None, prefer_auto: bool | None = None) -> TranscriptResponse:
        raise NoCaptionsAvailable("No captions")


def test_http_transcript_success() -> None:
    app = create_app(DummyService())
    client = TestClient(app)
    response = client.get("/transcript", params={"url": "https://youtu.be/video123"})
    assert response.status_code == 200
    data = response.json()
    assert data["video"]["id"] == "video123"
    assert data["chunks"][0]["cite_url"].endswith("t=0s")


def test_http_transcript_error() -> None:
    app = create_app(ErrorService())
    client = TestClient(app)
    response = client.get("/transcript", params={"url": "https://youtu.be/video123"})
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "NoCaptionsAvailable"


def test_http_metadata() -> None:
    app = create_app(DummyService())
    client = TestClient(app)
    response = client.get("/metadata", params={"url": "https://youtu.be/video123"})
    assert response.status_code == 200
    assert response.json()["title"] == "Example"
