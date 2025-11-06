from fastapi.testclient import TestClient

from tools.youtube_mcp.errors import InvalidArgument, NoCaptionsAvailable
from tools.youtube_mcp.http_server import create_app
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
    def __init__(self) -> None:
        self.transcript_called = 0

    def get_transcript(
        self, url: str, *, lang=None, prefer_auto=None
    ) -> TranscriptResponse:
        self.transcript_called += 1
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
        raise NoCaptionsAvailable()


class MetadataErrorService(StubService):
    def get_metadata(self, url: str) -> MetadataResponse:
        raise InvalidArgument("bad url")


class TrackErrorService(StubService):
    def search_captions(self, url: str) -> TracksResponse:
        raise InvalidArgument("bad url")


def test_http_transcript_success():
    service = StubService()
    app = create_app(service=service)
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    response = client.get("/transcript", params={"url": "https://youtu.be/abc"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["video"]["title"] == "Example"
    assert service.transcript_called == 1


def test_http_transcript_error():
    app = create_app(service=ErrorService())
    client = TestClient(app)
    response = client.get("/transcript", params={"url": "https://youtu.be/abc"})
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "NoCaptionsAvailable"


def test_http_tracks_and_metadata():
    service = StubService()
    app = create_app(service=service)
    client = TestClient(app)
    tracks = client.get("/tracks", params={"url": "abc"})
    metadata = client.get("/metadata", params={"url": "abc"})
    assert tracks.status_code == 200
    assert metadata.json()["title"] == "Example"


def test_http_metadata_error():
    app = create_app(service=MetadataErrorService())
    client = TestClient(app)
    response = client.get("/metadata", params={"url": "bad"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "InvalidArgument"


def test_http_tracks_error():
    app = create_app(service=TrackErrorService())
    client = TestClient(app)
    response = client.get("/tracks", params={"url": "bad"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "InvalidArgument"


def test_http_run_sync_without_anyio(monkeypatch):
    from tools.youtube_mcp import http_server as server_module

    monkeypatch.setattr(server_module, "anyio", None)
    app = server_module.create_app(service=StubService())
    client = TestClient(app)
    response = client.get("/transcript", params={"url": "https://youtu.be/abc"})
    assert response.status_code == 200
