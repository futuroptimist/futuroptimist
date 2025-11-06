"""Unit tests for the YouTube transcript client and service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tools.youtube_mcp.cache import TranscriptCache
from tools.youtube_mcp.errors import NoCaptionsAvailable, PolicyRejected
from tools.youtube_mcp.settings import Settings
from tools.youtube_mcp.youtube_client import YouTubeTranscriptClient, YouTubeTranscriptService


class StubTranscript:
    def __init__(
        self,
        language_code: str,
        text: list[dict[str, Any]],
        *,
        is_generated: bool = False,
    ) -> None:
        self.language_code = language_code
        self.is_generated = is_generated
        self.name = f"{language_code} {'auto' if is_generated else 'manual'}"
        self.translation_language = None
        self._text = text
        self.fetch_calls = 0

    def fetch(self) -> list[dict[str, Any]]:
        self.fetch_calls += 1
        return self._text


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(cache_dir=tmp_path / "cache")


def patch_transcripts(monkeypatch: pytest.MonkeyPatch, transcripts: list[StubTranscript]) -> None:
    monkeypatch.setattr(
        "tools.youtube_mcp.youtube_client.YouTubeTranscriptApi.list",
        lambda self, _video_id: transcripts,
    )


def patch_oembed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        YouTubeTranscriptClient,
        "_fetch_oembed",
        lambda self, url: {"title": "Demo", "author_name": "Channel"},
    )


def test_manual_track_preferred(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> None:
    manual = StubTranscript(
        "en",
        [
            {"text": "Hello world", "start": 0, "duration": 1.5},
            {"text": "Second line", "start": 1.5, "duration": 1.5},
        ],
    )
    auto = StubTranscript(
        "en",
        [
            {"text": "Auto hello", "start": 0, "duration": 1.5},
        ],
        is_generated=True,
    )
    patch_transcripts(monkeypatch, [manual, auto])
    patch_oembed(monkeypatch)

    cache = TranscriptCache(settings.ensure_cache_dir() / "test.sqlite3")
    client = YouTubeTranscriptClient(settings=settings)
    service = YouTubeTranscriptService(settings=settings, cache=cache, client=client)

    response = service.get_transcript(
        url="https://youtu.be/DEMO1234567", lang="en", prefer_auto=False
    )

    assert response.captions.lang == "en"
    assert not response.captions.is_auto
    assert len(response.segments) == 2
    assert response.hash

    # Second call should hit cache and avoid fetching segments again
    monkeypatch.setattr(
        client,
        "fetch_selected_transcript",
        lambda video_id, selected: (_ for _ in ()).throw(AssertionError("unexpected fetch")),
    )
    cached = service.get_transcript(
        url="https://youtu.be/DEMO1234567", lang="en", prefer_auto=False
    )
    assert cached.hash == response.hash


def test_auto_track_used_when_manual_missing(
    monkeypatch: pytest.MonkeyPatch, settings: Settings
) -> None:
    auto = StubTranscript(
        "en",
        [
            {"text": "Auto hello", "start": 0, "duration": 1.5},
        ],
        is_generated=True,
    )
    patch_transcripts(monkeypatch, [auto])
    patch_oembed(monkeypatch)

    client = YouTubeTranscriptClient(settings=settings)
    segments = client.fetch_transcript(
        "DEMO1234567", lang="en", prefer_auto=True
    )[1]
    assert segments[0].text == "Auto hello"


def test_no_segments_raises(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> None:
    empty = StubTranscript("en", [{"text": "   ", "start": 0, "duration": 1}])
    patch_transcripts(monkeypatch, [empty])
    patch_oembed(monkeypatch)

    client = YouTubeTranscriptClient(settings=settings)
    with pytest.raises(NoCaptionsAvailable):
        client.fetch_transcript("DEMO1234567", lang="en", prefer_auto=False)


def test_policy_rejected_on_private(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> None:
    patch_transcripts(monkeypatch, [])
    monkeypatch.setattr(
        YouTubeTranscriptClient,
        "_fetch_oembed",
        lambda self, url: (_ for _ in ()).throw(PolicyRejected("PolicyRejected", "private")),
    )
    client = YouTubeTranscriptClient(settings=settings)
    with pytest.raises(PolicyRejected):
        client.fetch_metadata("DEMO1234567")
