"""Tests for the FastAPI HTTP server endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tools.youtube_mcp.errors import NoCaptionsAvailable
from tools.youtube_mcp.http_server import app
from tools.youtube_mcp.models import (
    CaptionTrack,
    TranscriptChunk,
    TranscriptResponse,
    TranscriptSegment,
    VideoMetadata,
)


class DummyService:
    def __init__(self) -> None:
        self.transcript = TranscriptResponse(
            video=VideoMetadata(id="DEMO1234567", url="https://www.youtube.com/watch?v=DEMO1234567"),
            captions=CaptionTrack(lang="en", is_auto=False, name="English"),
            segments=[TranscriptSegment(id="s1", text="Hello", start=0.0, dur=1.0)],
            chunks=[
                TranscriptChunk(
                    id="demo_chunk_0",
                    text="Hello",
                    start=0.0,
                    end=1.0,
                    segment_ids=["s1"],
                    cite_url="https://www.youtube.com/watch?v=DEMO1234567&t=0s",
                )
            ],
            hash="hash",
        )

    def get_transcript(
        self,
        url: str,
        lang: str | None = None,
        prefer_auto: bool | None = None,
    ) -> TranscriptResponse:
        return self.transcript

    def list_tracks(self, url: str):
        return [self.transcript.captions]

    def get_metadata(self, url: str):
        return self.transcript.video


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_transcript_endpoint(monkeypatch) -> None:
    service = DummyService()
    monkeypatch.setattr(
        "tools.youtube_mcp.http_server.YouTubeTranscriptService.get_transcript",
        lambda self, **_: service.transcript,
    )
    response = client.get("/transcript", params={"url": "https://youtu.be/DEMO1234567"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["video"]["id"] == "DEMO1234567"
    assert payload["chunks"][0]["cite_url"].endswith("t=0s")


def test_transcript_error(monkeypatch) -> None:
    def failing_service(*_args, **_kwargs):
        raise NoCaptionsAvailable("NoCaptionsAvailable", "none")

    monkeypatch.setattr(
        "tools.youtube_mcp.http_server.YouTubeTranscriptService.get_transcript",
        failing_service,
    )
    response = client.get("/transcript", params={"url": "DEMO1234567"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NoCaptionsAvailable"
