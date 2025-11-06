"""Tests for the MCP stdio server."""

from __future__ import annotations

from tools.youtube_mcp.errors import NoCaptionsAvailable
from tools.youtube_mcp.mcp_server import McpServer
from tools.youtube_mcp.models import (
    CaptionTrack,
    TranscriptChunk,
    TranscriptResponse,
    TranscriptSegment,
    VideoMetadata,
)


class StubService:
    def __init__(self) -> None:
        self.response = TranscriptResponse(
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

    def get_transcript(self, **kwargs):
        return self.response

    def list_tracks(self, **kwargs):
        return [self.response.captions]

    def get_metadata(self, **kwargs):
        return self.response.video


def test_tools_list_contains_expected_entries() -> None:
    server = McpServer(service=StubService())
    names = [tool["name"] for tool in server.tools_list()["tools"]]
    assert "youtube.get_transcript" in names
    assert "youtube.healthcheck" in names


def test_tools_call_transcript() -> None:
    server = McpServer(service=StubService())
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools.call",
            "params": {"name": "youtube.get_transcript", "arguments": {"url": "DEMO1234567"}},
        }
    )
    assert response["result"]["video"]["id"] == "DEMO1234567"


def test_tools_call_error(monkeypatch) -> None:
    server = McpServer(service=StubService())

    def failing(*args, **kwargs):
        raise NoCaptionsAvailable("NoCaptionsAvailable", "none")

    server.service.get_transcript = failing  # type: ignore[assignment]
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools.call",
            "params": {"name": "youtube.get_transcript", "arguments": {"url": "DEMO1234567"}},
        }
    )
    assert response["error"]["data"]["code"] == "NoCaptionsAvailable"
