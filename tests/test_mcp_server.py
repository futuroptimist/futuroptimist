from tools.youtube_mcp.errors import NoCaptionsAvailable
from tools.youtube_mcp.mcp_server import MCPServer
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


def test_tools_list_includes_expected_methods():
    server = MCPServer(StubService())
    response = server.handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "tools.list"}
    )
    names = {tool["name"] for tool in response["result"]["tools"]}
    assert "youtube.get_transcript" in names
    assert "youtube.get_metadata" in names
    assert "youtube.healthcheck" in names


def test_tools_call_executes_transcript():
    server = MCPServer(StubService())
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools.call",
        "params": {
            "name": "youtube.get_transcript",
            "arguments": {"url": "https://youtu.be/abc"},
        },
    }
    response = server.handle_request(request)
    assert response["result"]["video"]["id"] == "abc"


def test_tools_call_unknown_tool():
    server = MCPServer(StubService())
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools.call",
        "params": {"name": "youtube.unknown", "arguments": {"url": "abc"}},
    }
    response = server.handle_request(request)
    assert response["error"]["data"]["code"] == "InvalidArgument"


def test_tools_call_error_response():
    class ErrorService(StubService):
        def get_transcript(
            self, url: str, *, lang=None, prefer_auto=None
        ) -> TranscriptResponse:
            raise NoCaptionsAvailable()

    server = MCPServer(ErrorService())
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools.call",
        "params": {
            "name": "youtube.get_transcript",
            "arguments": {"url": "abc"},
        },
    }
    response = server.handle_request(request)
    assert response["error"]["data"]["code"] == "NoCaptionsAvailable"


def test_method_not_found():
    server = MCPServer(StubService())
    response = server.handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "does.not.exist"}
    )
    assert response["error"]["code"] == -32601
