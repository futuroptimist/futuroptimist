from __future__ import annotations

from tools.youtube_mcp import mcp_server
from tools.youtube_mcp.errors import NoCaptionsAvailable
from tools.youtube_mcp.models import CaptionTrack, Chunk, Segment, TranscriptResponse, VideoMetadata


class FakeService:
    def __init__(self) -> None:
        video = VideoMetadata(id="abcdefghijk", url="https://youtu.be/abcdefghijk", title="Title", channel="Channel", published_at=None, duration=None)
        captions = CaptionTrack(lang="en", is_auto=False, name="English", track_id="track")
        segments = [Segment(id="seg_0000", text="hello", start=0.0, dur=1.0)]
        chunks = [Chunk(id="chunk_0001", text="hello", start=0.0, end=1.0, segment_ids=["seg_0000"], cite_url="https://www.youtube.com/watch?v=abcdefghijk&t=0s")]
        self.response = TranscriptResponse(video=video, captions=captions, segments=segments, chunks=chunks, hash="hash")
        self.error: Exception | None = None

    def get_transcript(self, url: str, *, lang: str | None = None, prefer_auto: bool | None = None):
        if self.error:
            raise self.error
        return self.response

    def list_tracks(self, url: str):
        return [self.response.captions]

    def get_metadata(self, url: str):
        return self.response.video


def test_tools_list(monkeypatch) -> None:
    monkeypatch.setattr(mcp_server, "service", FakeService())
    result = mcp_server._handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools.list"})
    tool_names = [tool["name"] for tool in result["result"]["tools"]]
    assert "youtube.get_transcript" in tool_names


def test_tools_call_success(monkeypatch) -> None:
    monkeypatch.setattr(mcp_server, "service", FakeService())
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools.call",
        "params": {"name": "youtube.get_transcript", "arguments": {"url": "abcdefghijk"}},
    }
    response = mcp_server._handle_request(payload)
    assert response["result"]["content"]["video"]["id"] == "abcdefghijk"


def test_tools_call_error(monkeypatch) -> None:
    fake_service = FakeService()
    fake_service.error = NoCaptionsAvailable()
    monkeypatch.setattr(mcp_server, "service", fake_service)
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools.call",
        "params": {"name": "youtube.get_transcript", "arguments": {"url": "abcdefghijk"}},
    }
    response = mcp_server._handle_request(payload)
    assert response["error"]["data"]["code"] == "NoCaptionsAvailable"
