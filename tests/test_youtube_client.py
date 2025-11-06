import httpx
import pytest
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    TooManyRequests,
    TranscriptsDisabled,
)
from youtube_transcript_api._errors import (
    VideoUnavailable as YTVideoUnavailable,
)

from tools.youtube_mcp.cache import TranscriptCache
from tools.youtube_mcp.errors import (
    InvalidArgument,
    NetworkError,
    NoCaptionsAvailable,
    PolicyRejected,
    RateLimited,
    VideoUnavailable,
)
from tools.youtube_mcp.models import MetadataResponse
from tools.youtube_mcp.settings import Settings
from tools.youtube_mcp.utils import InvalidVideoId
from tools.youtube_mcp.youtube_client import YouTubeTranscriptService

MANUAL_VIDEO_ID = "vid123abcde"
AUTO_VIDEO_ID = "vid456abcde"
RAW_VIDEO_ID = "vid789abcde"
AUTO_ONLY_ID = "auto123abcd"


class FakeTranscript:
    def __init__(
        self,
        language_code: str,
        is_generated: bool,
        name: str | None,
        segments,
        *,
        exc: Exception | None = None,
    ):
        self.language_code = language_code
        self.language = language_code
        self.is_generated = is_generated
        self.name = name
        self._segments = segments
        self.fetch_count = 0
        self._exc = exc

    def fetch(self):
        self.fetch_count += 1
        if self._exc:
            raise self._exc
        return self._segments


class FakeApi:
    def __init__(self, transcripts):
        self._transcripts = transcripts

    def list_transcripts(self, video_id: str):
        return list(self._transcripts)


def metadata_stub(video_id: str) -> MetadataResponse:
    return MetadataResponse(
        id=video_id,
        url=f"https://www.youtube.com/watch?v={video_id}",
        title="Test",
        channel="Channel",
        published_at=None,
        duration=None,
    )


@pytest.fixture()
def service(tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    manual = FakeTranscript(
        "en",
        False,
        "English",
        [{"text": "hello", "start": 0.0, "duration": 1.0}],
    )
    auto = FakeTranscript(
        "en",
        True,
        "English (auto)",
        [{"text": "auto hello", "start": 0.0, "duration": 1.0}],
    )
    api = FakeApi([manual, auto])
    svc = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=api,
        metadata_fetcher=metadata_stub,
    )
    return svc, manual, auto


def test_get_transcript_prefers_manual(service):
    svc, manual, _ = service
    response = svc.get_transcript(f"https://www.youtube.com/watch?v={MANUAL_VIDEO_ID}")
    assert response.captions.is_auto is False
    assert response.video.title == "Test"
    assert response.segments[0].text == "hello"

    cached = svc.get_transcript(f"https://www.youtube.com/watch?v={MANUAL_VIDEO_ID}")
    assert cached.hash == response.hash
    assert manual.fetch_count == 1


def test_auto_fallback(tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache", allow_auto=True)
    cache = TranscriptCache(settings.cache_dir)
    auto = FakeTranscript(
        "en",
        True,
        "English (auto)",
        [{"text": "auto hello", "start": 0.0, "duration": 1.0}],
    )
    api = FakeApi([auto])
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=api,
        metadata_fetcher=metadata_stub,
    )
    response = service.get_transcript(
        f"https://youtu.be/{AUTO_VIDEO_ID}", prefer_auto=True
    )
    assert response.captions.is_auto is True


def test_no_captions(tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache", allow_auto=False)
    cache = TranscriptCache(settings.cache_dir)
    api = FakeApi([])
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=api,
        metadata_fetcher=metadata_stub,
    )
    with pytest.raises(NoCaptionsAvailable):
        service.get_transcript(RAW_VIDEO_ID)


def test_search_tracks_orders_manual_first(service):
    svc, _, _ = service
    tracks = svc.search_captions(MANUAL_VIDEO_ID)
    assert tracks.tracks[0].is_auto is False
    assert tracks.tracks[1].is_auto is True


def test_default_metadata_fetcher(monkeypatch, tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    api = FakeApi([])
    service = YouTubeTranscriptService(
        settings=settings, cache=cache, transcript_api=api
    )

    class DummyResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"title": "Example", "author_name": "Channel"}

    monkeypatch.setattr(httpx, "get", lambda *a, **k: DummyResponse())
    metadata = service.get_metadata("https://youtu.be/abc123def45")
    assert metadata.title == "Example"


def test_metadata_rate_limited(monkeypatch, tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    api = FakeApi([])
    service = YouTubeTranscriptService(
        settings=settings, cache=cache, transcript_api=api
    )

    def raising_get(*args, **kwargs):
        request = httpx.Request("GET", "https://www.youtube.com/oembed")
        response = httpx.Response(429, request=request)
        raise httpx.HTTPStatusError("429", request=request, response=response)

    monkeypatch.setattr(httpx, "get", raising_get)
    with pytest.raises(RateLimited):
        service.get_metadata("https://youtu.be/abc123def45")


def test_map_transcript_error_rate_limited(tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    transcript = FakeTranscript("en", False, "English", [], exc=TooManyRequests("429"))
    api = FakeApi([transcript])
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=api,
        metadata_fetcher=metadata_stub,
    )
    with pytest.raises(RateLimited):
        service.get_transcript("https://youtu.be/abc123def45", prefer_auto=True)


def test_fetch_track_segments_could_not_translate(tmp_path):
    from youtube_transcript_api._errors import NotTranslatable

    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    transcript = FakeTranscript("en", False, "English", [], exc=NotTranslatable("nope"))
    api = FakeApi([transcript])
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=api,
        metadata_fetcher=metadata_stub,
    )
    with pytest.raises(NoCaptionsAvailable):
        service.get_transcript("https://youtu.be/abc123def45")


def test_policy_rejected_when_unlisted(monkeypatch, tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    transcript = FakeTranscript(
        "en",
        False,
        "English",
        [{"text": "hello", "start": 0.0, "duration": 1.0}],
    )
    api = FakeApi([transcript])
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=api,
        metadata_fetcher=metadata_stub,
    )
    monkeypatch.setattr(
        "tools.youtube_mcp.youtube_client.is_unlisted_or_private",
        lambda data: True,
    )
    with pytest.raises(PolicyRejected):
        service.get_transcript("https://youtu.be/abc123def45")


def test_get_metadata_invalid_argument(tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=FakeApi([]),
        metadata_fetcher=metadata_stub,
    )
    with pytest.raises(InvalidArgument):
        service.get_metadata("https://example.com/not-a-video")


def test_search_captions_invalid_argument(tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=FakeApi([]),
        metadata_fetcher=metadata_stub,
    )
    with pytest.raises(InvalidArgument):
        service.search_captions("invalid id")


def test_language_preference_selects_manual(service):
    svc, _, _ = service
    response = svc.get_transcript(
        f"https://www.youtube.com/watch?v={MANUAL_VIDEO_ID}", lang="EN"
    )
    assert response.captions.is_auto is False


def test_allow_auto_false_blocks_auto(tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache", allow_auto=False)
    cache = TranscriptCache(settings.cache_dir)
    auto = FakeTranscript(
        "en",
        True,
        "English (auto)",
        [{"text": "auto", "start": 0.0, "duration": 1.0}],
    )
    api = FakeApi([auto])
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=api,
        metadata_fetcher=metadata_stub,
    )
    with pytest.raises(NoCaptionsAvailable):
        service.get_transcript(f"https://youtu.be/{AUTO_ONLY_ID}")


def test_auto_selected_when_manual_missing(tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache", allow_auto=True)
    cache = TranscriptCache(settings.cache_dir)
    auto = FakeTranscript(
        "en",
        True,
        "English (auto)",
        [{"text": "auto", "start": 0.0, "duration": 1.0}],
    )
    api = FakeApi([auto])
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=api,
        metadata_fetcher=metadata_stub,
    )
    response = service.get_transcript(f"https://youtu.be/{AUTO_ONLY_ID}")
    assert response.captions.is_auto is True


def test_non_iterable_transcripts(tmp_path):
    class NonIterableTranscript:
        language_code = "en"
        language = "en"
        is_generated = False
        name = "English"

        def fetch(self):
            return [{"text": "hello", "start": 0.0, "duration": 1.0}]

    class NonIterableApi:
        def list_transcripts(self, video_id: str):
            return NonIterableTranscript()

    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=NonIterableApi(),
        metadata_fetcher=metadata_stub,
    )
    tracks = service.search_captions("https://youtu.be/abc123def45")
    assert tracks.tracks[0].lang == "en"


def test_normalise_segments_skips_blank(tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    transcript = FakeTranscript(
        "en",
        False,
        "English",
        [
            {"text": "   ", "start": 0.0, "duration": 1.0},
            {"text": "hello", "start": 1.0, "duration": 1.0},
        ],
    )
    api = FakeApi([transcript])
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=api,
        metadata_fetcher=metadata_stub,
    )
    response = service.get_transcript("https://youtu.be/abc123def45")
    assert len(response.segments) == 1


def test_metadata_fetcher_404(monkeypatch, tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=FakeApi([]),
    )

    class Response:
        status_code = 404

        def raise_for_status(self):
            pass

        def json(self):
            return {}

    monkeypatch.setattr(httpx, "get", lambda *a, **k: Response())
    with pytest.raises(VideoUnavailable):
        service.get_metadata("https://youtu.be/abc123def45")


def test_metadata_fetcher_403(monkeypatch, tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=FakeApi([]),
    )

    class Response:
        status_code = 403

        def raise_for_status(self):
            pass

        def json(self):
            return {}

    monkeypatch.setattr(httpx, "get", lambda *a, **k: Response())
    with pytest.raises(PolicyRejected):
        service.get_metadata("https://youtu.be/abc123def45")


def test_metadata_fetcher_network_error(monkeypatch, tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    service = YouTubeTranscriptService(
        settings=settings, cache=cache, transcript_api=FakeApi([])
    )

    def raising_get(*args, **kwargs):
        raise httpx.RequestError(
            "boom", request=httpx.Request("GET", "https://example.com")
        )

    monkeypatch.setattr(httpx, "get", raising_get)
    with pytest.raises(NetworkError):
        service.get_metadata("https://youtu.be/abc123def45")


def test_metadata_fetcher_http_error(monkeypatch, tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    service = YouTubeTranscriptService(
        settings=settings, cache=cache, transcript_api=FakeApi([])
    )

    class Response:
        status_code = 200

        def raise_for_status(self):
            resp = httpx.Response(
                500, request=httpx.Request("GET", "https://youtube.com")
            )
            raise httpx.HTTPStatusError("500", request=resp.request, response=resp)

        def json(self):
            return {}

    monkeypatch.setattr(httpx, "get", lambda *a, **k: Response())
    with pytest.raises(NetworkError):
        service.get_metadata("https://youtu.be/abc123def45")


def test_map_transcript_error_mappings(tmp_path):
    settings = Settings(cache_dir=tmp_path / "cache")
    cache = TranscriptCache(settings.cache_dir)
    service = YouTubeTranscriptService(
        settings=settings,
        cache=cache,
        transcript_api=FakeApi([]),
        metadata_fetcher=metadata_stub,
    )
    assert isinstance(
        service._map_transcript_error(YTVideoUnavailable("err")), VideoUnavailable
    )
    assert isinstance(
        service._map_transcript_error(InvalidVideoId("err")), InvalidArgument
    )
    assert isinstance(
        service._map_transcript_error(TranscriptsDisabled("err")), NoCaptionsAvailable
    )
    assert isinstance(
        service._map_transcript_error(TooManyRequests("err")), RateLimited
    )
    assert isinstance(
        service._map_transcript_error(CouldNotRetrieveTranscript("err")), NetworkError
    )
    assert isinstance(service._map_transcript_error(ValueError("err")), NetworkError)
