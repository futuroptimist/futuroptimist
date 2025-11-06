"""High-level client for fetching and caching YouTube transcripts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional

import httpx
from tenacity import RetryError, Retrying, stop_after_attempt, wait_exponential
from youtube_transcript_api import (  # type: ignore
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)
from youtube_transcript_api import (
    VideoUnavailable as YtVideoUnavailable,
)
from youtube_transcript_api._errors import (  # type: ignore
    InvalidVideoId,
    RequestBlocked,
)

from .cache import TranscriptCache
from .chunking import chunk_segments
from .errors import (
    InvalidArgument,
    NetworkError,
    NoCaptionsAvailable,
    PolicyRejected,
    RateLimited,
    VideoUnavailable,
)
from .models import CaptionTrack, TranscriptResponse, TranscriptSegment, VideoInfo
from .settings import Settings
from .utils import build_watch_url, hash_content, is_unlisted_or_private, parse_video_id


@dataclass
class TranscriptSelection:
    """Details about the selected caption track."""

    transcript: Any
    track_id: str
    lang: str
    is_auto: bool
    track_name: Optional[str]


class YouTubeTranscriptService:
    """Encapsulates transcript fetching, normalization, and caching."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        cache: Optional[TranscriptCache] = None,
        api: Optional[YouTubeTranscriptApi] = None,
    ) -> None:
        self.settings = settings or Settings()
        cache_path = self.settings.cache_dir / "transcripts.sqlite3"
        self.cache = cache or TranscriptCache(cache_path)
        self._api = api or YouTubeTranscriptApi()
        self._retry = Retrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.5, max=4),
            reraise=True,
        )

    # Public API -----------------------------------------------------------------
    def list_tracks(self, url: str) -> List[CaptionTrack]:
        video_id = parse_video_id(url)
        transcripts = self._list_transcripts(video_id)
        tracks: List[CaptionTrack] = []
        for transcript in transcripts:
            tracks.append(
                CaptionTrack(
                    lang=transcript.language_code,
                    is_auto=transcript.is_generated,
                    name=getattr(transcript, "name", None),
                )
            )
        tracks.sort(key=lambda t: (t.is_auto, t.lang))
        return tracks

    def get_metadata(self, url: str) -> VideoInfo:
        video_id = parse_video_id(url)
        watch_url = build_watch_url(video_id)
        metadata = VideoInfo(
            id=video_id,
            url=watch_url,
            title=None,
            channel=None,
            published_at=None,
            duration=None,
        )
        try:
            response = httpx.get(
                "https://www.youtube.com/oembed",
                params={"url": watch_url, "format": "json"},
                timeout=10,
            )
        except httpx.TimeoutException as exc:  # pragma: no cover - network failure branch
            raise NetworkError("Timed out fetching video metadata.") from exc
        except httpx.HTTPError as exc:  # pragma: no cover
            raise NetworkError("HTTP error fetching video metadata.") from exc

        if response.status_code in {401, 403}:
            if self.settings.reject_private_or_unlisted:
                raise PolicyRejected("Video is private or unlisted.")
            return metadata
        if response.status_code == 404:
            raise VideoUnavailable("Video not found.")
        if response.status_code >= 500:
            raise NetworkError("Upstream error fetching video metadata.")
        if response.status_code >= 400:
            raise InvalidArgument("Failed to fetch video metadata.")

        data = response.json()
        metadata.title = data.get("title")
        metadata.channel = data.get("author_name")
        return metadata

    def get_transcript(
        self,
        url: str,
        *,
        lang: Optional[str] = None,
        prefer_auto: Optional[bool] = None,
    ) -> TranscriptResponse:
        video_id = parse_video_id(url)
        metadata = self.get_metadata(url)
        if self.settings.reject_private_or_unlisted and is_unlisted_or_private(metadata):
            raise PolicyRejected("Video is private or unlisted.")

        transcripts = self._list_transcripts(video_id)
        selection = self._select_transcript(transcripts, lang, prefer_auto)
        cache_key = hash_content(
            {
                "video_id": video_id,
                "track_id": selection.track_id,
                "lang": selection.lang,
                "auto": selection.is_auto,
            }
        )
        cached = self.cache.get(cache_key)
        if cached:
            return TranscriptResponse.model_validate(cached)

        segments = self._fetch_segments(video_id, selection.transcript)
        chunks = chunk_segments(video_id, segments)
        response = TranscriptResponse(
            video=metadata,
            captions=CaptionTrack(
                lang=selection.lang,
                is_auto=selection.is_auto,
                name=selection.track_name,
            ),
            segments=segments,
            chunks=chunks,
            hash="",  # placeholder until computed
        )
        response_hash = hash_content(response.model_dump(exclude={"hash"}))
        response.hash = response_hash
        payload = response.model_dump()
        self.cache.set(cache_key, payload, self.settings.cache_ttl_days)
        return response

    # Internal helpers -----------------------------------------------------------
    def _list_transcripts(self, video_id: str) -> Iterable[Any]:
        try:
            transcripts: Optional[list[Any]] = None
            for attempt in self._retry:
                with attempt:
                    transcripts = list(self._api.list(video_id))
                    break
            if transcripts is None:
                raise NetworkError("Failed to list transcripts after retries.")
            return transcripts
        except RetryError as exc:  # pragma: no cover - defensive
            raise NetworkError("Failed to list transcripts after retries.") from exc
        except (TranscriptsDisabled, NoTranscriptFound) as exc:
            raise NoCaptionsAvailable("Captions are not available for this video.") from exc
        except RequestBlocked as exc:
            raise RateLimited("Rate limited by YouTube.") from exc
        except YtVideoUnavailable as exc:
            raise VideoUnavailable("The requested video is unavailable.") from exc
        except InvalidVideoId as exc:
            raise InvalidArgument("Invalid YouTube video identifier.") from exc
        except CouldNotRetrieveTranscript as exc:
            raise NetworkError("Network error retrieving transcripts.") from exc

    def _select_transcript(
        self,
        transcripts: Iterable[Any],
        lang: Optional[str],
        prefer_auto: Optional[bool],
    ) -> TranscriptSelection:
        prefer_auto = bool(prefer_auto)
        manual: List[Any] = []
        auto: List[Any] = []
        for transcript in transcripts:
            (auto if transcript.is_generated else manual).append(transcript)
        manual.sort(key=lambda t: t.language_code)
        auto.sort(key=lambda t: t.language_code)

        def find_candidate(items: List[Any]) -> Optional[Any]:
            if not items:
                return None
            if lang:
                lowered = lang.lower()
                for t in items:
                    code = t.language_code.lower()
                    if code == lowered:
                        return t
                    prefix = code.split("-")[0]
                    if prefix == lowered:
                        return t
            return items[0]

        search_order: List[tuple[List[Any], bool]] = []
        if prefer_auto and self.settings.allow_auto:
            search_order.append((auto, True))
            search_order.append((manual, False))
        else:
            search_order.append((manual, False))
            if self.settings.allow_auto:
                search_order.append((auto, True))

        for pool, is_auto in search_order:
            candidate = find_candidate(pool)
            if candidate is not None:
                return TranscriptSelection(
                    transcript=candidate,
                    track_id=self._track_identifier(candidate),
                    lang=candidate.language_code,
                    is_auto=is_auto,
                    track_name=getattr(candidate, "name", None),
                )

        raise NoCaptionsAvailable("No suitable caption tracks were found.")

    def _fetch_segments(self, video_id: str, transcript: Any) -> List[TranscriptSegment]:
        try:
            for attempt in self._retry:
                with attempt:
                    raw_segments = transcript.fetch()
                    break
        except RetryError as exc:  # pragma: no cover - defensive
            raise NetworkError("Failed to fetch transcript after retries.") from exc
        except RequestBlocked as exc:
            raise RateLimited("Rate limited by YouTube.") from exc
        except CouldNotRetrieveTranscript as exc:
            raise NetworkError("Could not retrieve transcript segments.") from exc

        normalized_segments: List[TranscriptSegment] = []
        for index, item in enumerate(raw_segments):
            text = " ".join(item.get("text", "").split())
            if not text:
                continue
            start = float(item.get("start", 0.0))
            dur = float(item.get("duration", item.get("dur", 0.0)))
            seg_id = f"{video_id}-seg-{index:04d}"
            normalized_segments.append(
                TranscriptSegment(id=seg_id, text=text, start=start, dur=dur)
            )
        return normalized_segments

    @staticmethod
    def _track_identifier(transcript: Any) -> str:
        data = getattr(transcript, "_data", {})
        track_id: Optional[str] = None
        if isinstance(data, dict):
            raw_id = data.get("id")
            if raw_id:
                track_id = str(raw_id)
        if not track_id:
            track_id = getattr(transcript, "language_code", "unknown")
        return track_id


__all__ = ["YouTubeTranscriptService"]
