"""Wrapper around :mod:`youtube_transcript_api` with caching and chunking."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, cast

import httpx
from tenacity import RetryError, Retrying, stop_after_attempt, wait_exponential
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    NotTranslatable,
    TooManyRequests,
    TranscriptsDisabled,
)
from youtube_transcript_api._errors import (
    InvalidVideoId as YtInvalidVideoId,
)
from youtube_transcript_api._errors import (
    VideoUnavailable as YtVideoUnavailable,
)

from .cache import TranscriptCache
from .chunking import chunk_segments
from .errors import (
    BaseYtMcpError,
    InvalidArgument,
    NetworkError,
    NoCaptionsAvailable,
    PolicyRejected,
    RateLimited,
    VideoUnavailable,
)
from .models import CaptionTrackInfo, MetadataResponse, Segment, TracksResponse, TranscriptResponse
from .settings import Settings
from .utils import (
    InvalidVideoId,
    build_watch_url,
    hash_content,
    is_unlisted_or_private,
    parse_video_id,
)


def _create_retry() -> Retrying:
    """Build a retry configuration shared across HTTP and transcript calls."""

    return Retrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        reraise=True,
    )


class YouTubeTranscriptService:
    """High-level service orchestrating transcripts, metadata, and caching."""

    def __init__(
        self,
        settings: Settings,
        *,
        cache: TranscriptCache | None = None,
        transcript_api: Any = None,
        metadata_fetcher: Callable[[str], MetadataResponse] | None = None,
    ) -> None:
        self.settings = settings
        self.cache = cache or TranscriptCache(settings.cache_dir)
        self._api = transcript_api or YouTubeTranscriptApi
        self._metadata_fetcher = metadata_fetcher or self._default_metadata_fetcher
        self._transcript_retry = _create_retry()
        self._http_retry = _create_retry()

    def get_transcript(
        self,
        url: str,
        *,
        lang: str | None = None,
        prefer_auto: bool | None = None,
    ) -> TranscriptResponse:
        """Fetch a transcript response, consulting the cache when possible."""

        try:
            video_id = parse_video_id(url)
        except InvalidVideoId as exc:  # pragma: no cover - defensive guard
            raise InvalidArgument(str(exc)) from exc

        prefer_auto_final = bool(prefer_auto) if prefer_auto is not None else False
        watch_url = build_watch_url(video_id)

        metadata = self.get_metadata(watch_url)
        if self.settings.reject_private_or_unlisted and is_unlisted_or_private(
            metadata.model_dump()
        ):
            raise PolicyRejected("Video is private or unlisted")

        track = self._select_track(video_id, lang=lang, prefer_auto=prefer_auto_final)
        track_identifier = getattr(track, "id", None) or getattr(track, "language_code", "")
        cache_key = hash_content(
            {
                "video": video_id,
                "lang": getattr(track, "language_code", lang or ""),
                "is_auto": getattr(track, "is_generated", False),
                "track": track_identifier,
            }
        )

        cached = self.cache.get(cache_key)
        if cached:
            return TranscriptResponse(**cached)

        try:
            segments_raw = self._transcript_retry(self._fetch_track_segments, track)
        except RetryError as exc:  # pragma: no cover - network retries are hard to hit
            last_exc = exc.last_attempt.exception()
            if isinstance(last_exc, BaseYtMcpError):
                raise last_exc from exc
            if isinstance(last_exc, Exception):
                raise NetworkError("Failed to fetch transcript after retries") from last_exc
            raise NetworkError("Failed to fetch transcript after retries") from exc

        segments = self._normalise_segments(video_id, segments_raw)
        chunks = chunk_segments(video_id, segments)

        captions_info = CaptionTrackInfo(
            lang=getattr(track, "language_code", lang or ""),
            is_auto=bool(getattr(track, "is_generated", False)),
            track_name=getattr(track, "name", None),
        )
        payload: dict[str, Any] = {
            "video": metadata.model_dump(),
            "captions": captions_info.model_dump(),
            "segments": [segment.model_dump() for segment in segments],
            "chunks": [chunk.model_dump() for chunk in chunks],
        }
        payload_hash = hash_content(payload)
        payload["hash"] = payload_hash
        response = TranscriptResponse.model_validate(payload)
        self.cache.set(cache_key, response.model_dump(), self.settings.cache_ttl_days)
        return response

    def search_captions(self, url: str) -> TracksResponse:
        video_id = self._parse_for_tracks(url)
        tracks = [
            CaptionTrackInfo(
                lang=getattr(track, "language_code", getattr(track, "language", "")),
                is_auto=bool(getattr(track, "is_generated", False)),
                track_name=getattr(track, "name", None),
            )
            for track in self._list_transcripts(video_id)
        ]
        tracks.sort(key=lambda t: (t.is_auto, t.lang))
        return TracksResponse(tracks=tracks)

    def get_metadata(self, url: str) -> MetadataResponse:
        try:
            video_id = parse_video_id(url)
        except InvalidVideoId as exc:
            raise InvalidArgument(str(exc)) from exc
        return self._metadata_fetcher(video_id)

    # ------------------------------------------------------------------
    # Internal helpers

    def _parse_for_tracks(self, url: str) -> str:
        try:
            return parse_video_id(url)
        except InvalidVideoId as exc:
            raise InvalidArgument(str(exc)) from exc

    def _select_track(
        self,
        video_id: str,
        *,
        lang: str | None,
        prefer_auto: bool,
    ) -> Any:
        transcripts = self._list_transcripts(video_id)
        manual = [t for t in transcripts if not getattr(t, "is_generated", False)]
        auto = [t for t in transcripts if getattr(t, "is_generated", False)]

        def _match_language(items: Iterable[Any]) -> Any | None:
            if lang is None:
                return None
            lang_lower = lang.lower()
            for item in items:
                language_code = getattr(item, "language_code", "").lower()
                language = getattr(item, "language", "").lower()
                if lang_lower in {language_code, language}:
                    return item
            return None

        if prefer_auto and self.settings.allow_auto:
            candidate = _match_language(auto)
            if candidate:
                return candidate
            if lang is None and auto:
                return auto[0]

        candidate = _match_language(manual)
        if candidate:
            return candidate

        if manual:
            return manual[0]

        if self.settings.allow_auto:
            candidate = _match_language(auto)
            if candidate:
                return candidate
            if lang is None and auto:
                return auto[0]

        raise NoCaptionsAvailable()

    def _list_transcripts(self, video_id: str) -> list[Any]:
        try:
            transcripts_obj = self._transcript_retry(self._api.list_transcripts, video_id)
        except RetryError as exc:  # pragma: no cover
            last_exc = exc.last_attempt.exception()
            if isinstance(last_exc, Exception):
                raise self._map_transcript_error(last_exc) from last_exc
            raise NetworkError("Failed to list transcripts after retries") from exc
        except Exception as exc:  # pragma: no cover
            raise self._map_transcript_error(exc) from exc

        try:
            iterable = cast(Iterable[Any], transcripts_obj)
            return list(iterable)
        except TypeError:
            # Older versions of youtube_transcript_api return iterables without __iter__
            return [cast(Any, transcripts_obj)]

    def _fetch_track_segments(self, track: Any) -> list[dict[str, Any]]:
        try:
            data = track.fetch()
        except TooManyRequests as exc:
            raise RateLimited(str(exc)) from exc
        except (CouldNotRetrieveTranscript, NotTranslatable) as exc:
            raise NoCaptionsAvailable(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise NetworkError(str(exc)) from exc
        return cast(list[dict[str, Any]], data)

    def _normalise_segments(
        self, video_id: str, raw_segments: Iterable[dict[str, Any]]
    ) -> list[Segment]:
        segments: list[Segment] = []
        for index, raw in enumerate(raw_segments):
            text_raw = (raw.get("text") or "").strip()
            text = " ".join(text_raw.split())
            if not text:
                continue
            start = float(raw.get("start", 0.0))
            duration = float(raw.get("duration", raw.get("dur", 0.0)))
            segments.append(
                Segment(
                    id=f"{video_id}:{index}",
                    text=text,
                    start=start,
                    dur=duration,
                )
            )
        segments.sort(key=lambda item: item.start)
        return segments

    def _default_metadata_fetcher(self, video_id: str) -> MetadataResponse:
        url = build_watch_url(video_id)

        def _request() -> MetadataResponse:
            try:
                response = httpx.get(
                    "https://www.youtube.com/oembed",
                    params={"url": url, "format": "json"},
                    timeout=5.0,
                )
                if response.status_code == 404:
                    raise VideoUnavailable()
                if response.status_code in {401, 403}:
                    raise PolicyRejected("Metadata not accessible for this video")
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429:
                    raise RateLimited("Rate limited while fetching metadata") from exc
                raise NetworkError(str(exc)) from exc
            except httpx.RequestError as exc:
                raise NetworkError(str(exc)) from exc

            title = data.get("title") if isinstance(data, dict) else None
            channel = data.get("author_name") if isinstance(data, dict) else None
            metadata = MetadataResponse(
                id=video_id,
                url=url,
                title=title,
                channel=channel,
                published_at=None,
                duration=None,
            )
            return metadata

        try:
            return self._http_retry(_request)
        except RetryError as exc:  # pragma: no cover
            last_exc = exc.last_attempt.exception()
            if isinstance(last_exc, BaseYtMcpError):
                raise last_exc from exc
            if isinstance(last_exc, Exception):
                raise NetworkError("Failed to fetch metadata after retries") from last_exc
            raise NetworkError("Failed to fetch metadata after retries") from exc

    def _map_transcript_error(self, exc: Exception) -> BaseYtMcpError:
        if isinstance(exc, YtInvalidVideoId | InvalidVideoId):
            return InvalidArgument(str(exc))
        if isinstance(exc, YtVideoUnavailable):
            return VideoUnavailable(str(exc))
        if isinstance(exc, TranscriptsDisabled | NoTranscriptFound):
            return NoCaptionsAvailable(str(exc))
        if isinstance(exc, TooManyRequests):
            return RateLimited(str(exc))
        if isinstance(exc, CouldNotRetrieveTranscript):
            return NetworkError(str(exc))
        return NetworkError(str(exc))
