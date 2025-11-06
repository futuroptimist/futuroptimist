import json
from typing import Any

import pytest

from tools.youtube_mcp import cli
from tools.youtube_mcp.errors import InvalidArgument
from tools.youtube_mcp.models import (
    CaptionTrackInfo,
    Chunk,
    MetadataResponse,
    Segment,
    TracksResponse,
    TranscriptResponse,
    VideoInfo,
)


class StubService:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def get_transcript(
        self, url: str, *, lang=None, prefer_auto=None
    ) -> TranscriptResponse:
        return TranscriptResponse(
            video=VideoInfo(id="abc", url=url, title="Example", channel="Channel"),
            captions=CaptionTrackInfo(lang="en", is_auto=False, track_name="English"),
            segments=[Segment(id="abc:0", text="hello", start=0.0, dur=1.0)],
            chunks=[
                Chunk(
                    id="abc:chunk:0",
                    text="hello",
                    start=0.0,
                    end=1.0,
                    segment_ids=["abc:0"],
                    cite_url="https://www.youtube.com/watch?v=abc&t=0s",
                )
            ],
            hash="hash",
        )

    def search_captions(self, url: str) -> TracksResponse:
        return TracksResponse(
            tracks=[CaptionTrackInfo(lang="en", is_auto=False, track_name="English")]
        )

    def get_metadata(self, url: str) -> MetadataResponse:
        return MetadataResponse(id="abc", url=url, title="Example", channel="Channel")


class ErrorService(StubService):
    def get_transcript(
        self, url: str, *, lang=None, prefer_auto=None
    ) -> TranscriptResponse:
        raise InvalidArgument("bad url")


@pytest.fixture(autouse=True)
def patch_service(monkeypatch):
    monkeypatch.setattr(cli, "YouTubeTranscriptService", StubService)


def test_cli_transcript_success(monkeypatch, capsys):
    exit_code = cli.main(
        [
            "transcript",
            "--url",
            "https://youtu.be/abc",
        ]
    )
    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["video"]["id"] == "abc"


def test_cli_tracks(monkeypatch, capsys):
    exit_code = cli.main(["tracks", "--url", "abc"])
    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["tracks"][0]["lang"] == "en"


def test_cli_error(monkeypatch, capsys):
    monkeypatch.setattr(cli, "YouTubeTranscriptService", ErrorService)
    exit_code = cli.main(["transcript", "--url", "bad"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "InvalidArgument" in captured.err
