from __future__ import annotations

from tools.youtube_mcp.errors import NoCaptionsAvailable
from tools.youtube_mcp.mcp_server import McpServer
from tools.youtube_mcp.models import (
    CaptionTrack,
    TranscriptChunk,
    TranscriptResponse,
    TranscriptSegment,
    VideoInfo,
)
from tools.youtube_mcp.settings import Settings


class StubService:
    def __init__(self) -> None:
        self.settings = Settings()

    def get_transcript(self, url: str, lang: str | None = None, prefer_auto: bool | None = None) -> TranscriptResponse:
        video = VideoInfo(id="vid", url="url", title=None, channel=None, published_at=None, duration=None)
        segment = TranscriptSegment(id="seg", text="hello", start=0.0, dur=1.0)
        chunk = TranscriptChunk(
            id="vid-chunk-0001",
            text="hello",
            start=0.0,
            end=1.0,
            segment_ids=["seg"],
            cite_url="url&t=0s",
        )
        return TranscriptResponse(
            video=video,
            captions=CaptionTrack(lang="en", is_auto=False, name="English"),
            segments=[segment],
            chunks=[chunk],
            hash="hash",
        )

    def list_tracks(self, url: str):
        return [CaptionTrack(lang="en", is_auto=False, name="English")]

    def get_metadata(self, url: str):
        return VideoInfo(id="vid", url="url", title=None, channel=None, published_at=None, duration=None)


class ErrorStubService(StubService):
    def get_transcript(self, url: str, lang: str | None = None, prefer_auto: bool | None = None) -> TranscriptResponse:
        raise NoCaptionsAvailable("no captions")


def test_tools_list() -> None:
    server = McpServer(service=StubService())
    response = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools.list"})
    assert "tools" in response["result"]
    assert any(tool["name"] == "youtube.get_transcript" for tool in response["result"]["tools"])


def test_call_transcript() -> None:
    class SimpleStub(StubService):
        def get_transcript(self, url: str, lang: str | None = None, prefer_auto: bool | None = None) -> TranscriptResponse:
            video = VideoInfo(id="vid", url="url", title=None, channel=None, published_at=None, duration=None)
            segment = TranscriptSegment(id="seg", text="hello", start=0.0, dur=1.0)
            chunk = TranscriptChunk(
                id="vid-chunk-0001",
                text="hello",
                start=0.0,
                end=1.0,
                segment_ids=["seg"],
                cite_url="url&t=0s",
            )
            return TranscriptResponse(
                video=video,
                captions=CaptionTrack(lang="en", is_auto=False, name="English"),
                segments=[segment],
                chunks=[chunk],
                hash="hash",
            )

    server = McpServer(service=SimpleStub())
    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools.call",
            "params": {"name": "youtube.get_transcript", "arguments": {"url": "https://youtu.be/vid"}},
        }
    )
    assert "result" in response
    assert response["result"]["video"]["id"] == "vid"


def test_call_missing_url() -> None:
    server = McpServer(service=StubService())
    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools.call",
            "params": {"name": "youtube.get_transcript", "arguments": {}},
        }
    )
    assert response["error"]["code"] == "InvalidArgument"


def test_call_error_response() -> None:
    server = McpServer(service=ErrorStubService())
    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools.call",
            "params": {"name": "youtube.get_transcript", "arguments": {"url": "x"}},
        }
    )
    assert response["error"]["code"] == "NoCaptionsAvailable"
