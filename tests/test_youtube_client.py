from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pytest

from tools.youtube_mcp.errors import NoCaptionsAvailable, PolicyRejected
from tools.youtube_mcp.models import VideoInfo
from tools.youtube_mcp.settings import Settings
from tools.youtube_mcp.youtube_client import YouTubeTranscriptService

VIDEO_ID = "dQw4w9WgXcQ"
WATCH_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"
SHORT_URL = f"https://youtu.be/{VIDEO_ID}"


@dataclass
class FakeTranscript:
    language_code: str
    is_generated: bool
    segments: list[dict[str, Any]]
    name: str | None = None
    track_id: str | None = None

    def fetch(self) -> list[dict[str, Any]]:
        return self.segments

    @property
    def _data(self) -> dict[str, Any]:
        return {"id": self.track_id} if self.track_id else {}


def fake_transcripts() -> list[FakeTranscript]:
    return [
        FakeTranscript(
            language_code="en",
            is_generated=False,
            track_id="track-manual",
            segments=[
                {"text": " Hello  world ", "start": 0.0, "duration": 4.0},
                {"text": "second line", "start": 4.0, "duration": 2.0},
            ],
        ),
        FakeTranscript(
            language_code="en",
            is_generated=True,
            track_id="track-auto",
            segments=[{"text": "auto caption", "start": 0.0, "duration": 4.0}],
        ),
    ]


class FakeTranscriptApi:
    def __init__(self, transcripts: list[FakeTranscript] | None = None) -> None:
        self.transcripts = transcripts or []

    def list(self, video_id: str) -> list[FakeTranscript]:  # pragma: no cover - simple proxy
        assert video_id == VIDEO_ID
        return list(self.transcripts)


@pytest.fixture
def transcript_api() -> FakeTranscriptApi:
    return FakeTranscriptApi(fake_transcripts())


@pytest.fixture
def service(
    tmp_path, transcript_api: FakeTranscriptApi, monkeypatch: pytest.MonkeyPatch
) -> YouTubeTranscriptService:
    settings = Settings(cache_dir=tmp_path)
    svc = YouTubeTranscriptService(settings=settings, api=transcript_api)

    metadata = VideoInfo(
        id=VIDEO_ID,
        url=WATCH_URL,
        title="Example",
        channel="Channel",
        published_at=None,
        duration=None,
    )
    monkeypatch.setattr(YouTubeTranscriptService, "get_metadata", lambda self, url: metadata)
    return svc


def test_get_transcript_prefers_manual(service: YouTubeTranscriptService) -> None:
    result = service.get_transcript(SHORT_URL)
    assert result.captions.lang == "en"
    assert result.captions.is_auto is False
    assert result.segments[0].text == "Hello world"
    assert result.chunks
    cached = service.get_transcript(SHORT_URL)
    assert cached.hash == result.hash


def test_get_transcript_allows_auto(
    service: YouTubeTranscriptService, transcript_api: FakeTranscriptApi
) -> None:
    transcript_api.transcripts = [fake_transcripts()[1]]
    result = service.get_transcript(VIDEO_ID, prefer_auto=True)
    assert result.captions.is_auto is True


def test_list_tracks_sorted(service: YouTubeTranscriptService) -> None:
    tracks = service.list_tracks(VIDEO_ID)
    assert [t.is_auto for t in tracks] == [False, True]


def test_get_metadata_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(cache_dir=Path("."))
    svc = YouTubeTranscriptService(settings=settings)

    def fake_get(url: str, params: dict[str, Any], timeout: int, **_: Any) -> httpx.Response:
        return httpx.Response(403)

    monkeypatch.setattr("tools.youtube_mcp.youtube_client.httpx.get", fake_get)
    with pytest.raises(PolicyRejected):
        svc.get_metadata(SHORT_URL)


def test_transcript_error_when_no_tracks(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    settings = Settings(cache_dir=tmp_path)
    svc = YouTubeTranscriptService(settings=settings, api=FakeTranscriptApi([]))
    metadata = VideoInfo(
        id=VIDEO_ID,
        url=WATCH_URL,
        title=None,
        channel=None,
        published_at=None,
        duration=None,
    )
    monkeypatch.setattr(YouTubeTranscriptService, "get_metadata", lambda self, url: metadata)

    with pytest.raises(NoCaptionsAvailable):
        svc.get_transcript(VIDEO_ID)
