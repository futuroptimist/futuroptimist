from __future__ import annotations

from fastapi.testclient import TestClient

from tools.youtube_mcp import http_server
from tools.youtube_mcp.errors import NoCaptionsAvailable
from tools.youtube_mcp.models import CaptionTrack, Chunk, Segment, TranscriptResponse, VideoMetadata


class FakeService:
    def __init__(self) -> None:
        video = VideoMetadata(
            id="abcdefghijk",
            url="https://youtu.be/abcdefghijk",
            title="Title",
            channel="Channel",
            published_at=None,
            duration=None,
        )
        captions = CaptionTrack(lang="en", is_auto=False, name="English", track_id="track")
        segments = [Segment(id="seg_0000", text="hello", start=0.0, dur=1.0)]
        chunks = [
            Chunk(
                id="chunk_0001",
                text="hello",
                start=0.0,
                end=1.0,
                segment_ids=["seg_0000"],
                cite_url="https://www.youtube.com/watch?v=abcdefghijk&t=0s",
            )
        ]
        self.transcript_value = TranscriptResponse(
            video=video,
            captions=captions,
            segments=segments,
            chunks=chunks,
            hash="hash",
        )
        self.transcript_exc = None
        self.tracks_value = [captions]
        self.tracks_exc = None
        self.metadata_value = video
        self.metadata_exc = None

    def get_transcript(self, url: str, *, lang: str | None = None, prefer_auto: bool | None = None):
        if self.transcript_exc:
            raise self.transcript_exc
        return self.transcript_value

    def list_tracks(self, url: str):
        if self.tracks_exc:
            raise self.tracks_exc
        return self.tracks_value

    def get_metadata(self, url: str):
        if self.metadata_exc:
            raise self.metadata_exc
        return self.metadata_value


def test_transcript_endpoint_success(monkeypatch) -> None:
    fake_service = FakeService()
    monkeypatch.setattr(http_server, "_service", fake_service)
    client = TestClient(http_server.app)
    response = client.get("/transcript", params={"url": "abcdefghijk"})
    assert response.status_code == 200
    data = response.json()
    assert data["video"]["id"] == "abcdefghijk"


def test_transcript_endpoint_error(monkeypatch) -> None:
    fake_service = FakeService()
    fake_service.transcript_exc = NoCaptionsAvailable()
    monkeypatch.setattr(http_server, "_service", fake_service)
    client = TestClient(http_server.app)
    response = client.get("/transcript", params={"url": "abcdefghijk"})
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "NoCaptionsAvailable"


def test_tracks_endpoint(monkeypatch) -> None:
    fake_service = FakeService()
    monkeypatch.setattr(http_server, "_service", fake_service)
    client = TestClient(http_server.app)
    response = client.get("/tracks", params={"url": "abcdefghijk"})
    assert response.status_code == 200
    assert response.json()["tracks"][0]["lang"] == "en"


def test_metadata_endpoint(monkeypatch) -> None:
    fake_service = FakeService()
    monkeypatch.setattr(http_server, "_service", fake_service)
    client = TestClient(http_server.app)
    response = client.get("/metadata", params={"url": "abcdefghijk"})
    assert response.status_code == 200
    assert response.json()["url"].endswith("abcdefghijk")
