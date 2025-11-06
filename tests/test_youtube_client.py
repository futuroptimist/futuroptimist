from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from tools.youtube_mcp import youtube_client
from tools.youtube_mcp.cache import Cache
from tools.youtube_mcp.errors import NoCaptionsAvailable
from tools.youtube_mcp.settings import Settings
from tools.youtube_mcp.youtube_client import YouTubeTranscriptService


class DummyTranscript:
    def __init__(self, language_code: str, is_generated: bool, entries: List[dict[str, object]]) -> None:
        self.language_code = language_code
        self.is_generated = is_generated
        self.name = f"{language_code} track"
        self.transcript_id = f"{language_code}-{int(is_generated)}"
        self._entries = entries
        self.fetch_calls = 0

    def fetch(self) -> List[dict[str, object]]:
        self.fetch_calls += 1
        return list(self._entries)


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        cache_dir=tmp_path,
        cache_ttl_days=14,
        allow_auto=True,
        reject_private_or_unlisted=False,
        http_host="127.0.0.1",
        http_port=8765,
    )


def make_service(monkeypatch: pytest.MonkeyPatch, settings: Settings, transcripts: List[DummyTranscript]) -> YouTubeTranscriptService:
    cache = Cache(settings.cache_dir / "cache.sqlite3", settings.cache_ttl_days)

    def list_transcripts(_video_id: str) -> List[DummyTranscript]:
        return transcripts

    monkeypatch.setattr(youtube_client, "YouTubeTranscriptApi", type("Api", (), {"list_transcripts": staticmethod(list_transcripts)}))
    monkeypatch.setattr(YouTubeTranscriptService, "_fetch_oembed", lambda self, url: {"title": "Title", "author_name": "Channel"})
    return YouTubeTranscriptService(settings, cache)


def test_get_transcript_prefers_manual(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> None:
    manual = DummyTranscript("en", False, [{"text": "hello", "start": 0, "duration": 2}])
    auto = DummyTranscript("en", True, [{"text": "hi", "start": 0, "duration": 2}])
    service = make_service(monkeypatch, settings, [manual, auto])
    response = service.get_transcript("https://youtu.be/abcdefghijk")
    assert response.captions.is_auto is False
    assert response.segments[0].text == "hello"


def test_get_transcript_prefers_auto_when_requested(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> None:
    manual = DummyTranscript("fr", False, [{"text": "bonjour", "start": 0, "duration": 2}])
    auto = DummyTranscript("en", True, [{"text": "hello", "start": 0, "duration": 2}])
    service = make_service(monkeypatch, settings, [manual, auto])
    response = service.get_transcript("https://www.youtube.com/watch?v=abcdefghijk", prefer_auto=True, lang="en")
    assert response.captions.is_auto is True


def test_get_transcript_uses_cache(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> None:
    transcript = DummyTranscript("en", False, [{"text": "cached", "start": 0, "duration": 1}])
    service = make_service(monkeypatch, settings, [transcript])
    first = service.get_transcript("abcdefghijk")
    second = service.get_transcript("abcdefghijk")
    assert transcript.fetch_calls == 1
    assert first.hash == second.hash


def test_no_captions_raises(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> None:
    cache = Cache(settings.cache_dir / "cache.sqlite3", settings.cache_ttl_days)

    def list_transcripts(_video_id: str) -> list[DummyTranscript]:
        return []

    monkeypatch.setattr(youtube_client, "YouTubeTranscriptApi", type("Api", (), {"list_transcripts": staticmethod(list_transcripts)}))
    monkeypatch.setattr(YouTubeTranscriptService, "_fetch_oembed", lambda self, url: {"title": "Title", "author_name": "Channel"})
    service = YouTubeTranscriptService(settings, cache)

    with pytest.raises(NoCaptionsAvailable):
        service.get_transcript("abcdefghijk")


def test_list_tracks_sorted(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> None:
    manual = DummyTranscript("en", False, [])
    auto = DummyTranscript("en", True, [])

    def list_transcripts(_video_id: str) -> list[DummyTranscript]:
        return [auto, manual]

    monkeypatch.setattr(youtube_client, "YouTubeTranscriptApi", type("Api", (), {"list_transcripts": staticmethod(list_transcripts)}))
    service = make_service(monkeypatch, settings, [manual, auto])
    tracks = service.list_tracks("abcdefghijk")
    assert tracks[0].is_auto is False
    assert tracks[1].is_auto is True
