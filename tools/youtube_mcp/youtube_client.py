"""Wrapper around ``youtube_transcript_api`` with caching helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (  # type: ignore[attr-defined]
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    YouTubeRequestFailed,
)
from youtube_transcript_api._errors import (
    VideoUnavailable as YTVideoUnavailable,
)

from .cache import TranscriptCache
from .chunking import chunk_segments
from .errors import (
    NetworkError,
    NoCaptionsAvailable,
    PolicyRejected,
    RateLimited,
    VideoUnavailable,
)
from .models import CaptionTrack, TranscriptResponse, TranscriptSegment, VideoMetadata
from .settings import Settings, get_settings
from .utils import build_watch_url, hash_content, parse_video_id


@dataclass
class SelectedTranscript:
    """Internal helper describing a chosen transcript track."""

    transcript: Any
    track: CaptionTrack


class YouTubeTranscriptClient:
    """Thin convenience wrapper around ``youtube_transcript_api``."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.api = YouTubeTranscriptApi()

    def list_tracks(self, video_id: str) -> list[CaptionTrack]:
        transcripts = list(self._list_transcripts(video_id))
        tracks = [self._to_caption_track(transcript) for transcript in transcripts]
        manual = [track for track in tracks if not track.is_auto]
        auto = [track for track in tracks if track.is_auto]
        return manual + auto

    def select_transcript(
        self, video_id: str, lang: str | None, prefer_auto: bool
    ) -> SelectedTranscript:
        transcripts = list(self._list_transcripts(video_id))
        return self._select_transcript(transcripts, lang, prefer_auto)

    def fetch_selected_transcript(
        self, video_id: str, selected: SelectedTranscript
    ) -> list[TranscriptSegment]:
        try:
            raw_segments = selected.transcript.fetch()
        except CouldNotRetrieveTranscript as exc:  # pragma: no cover - network edge
            raise NetworkError("NetworkError", "Failed to retrieve transcript") from exc
        return self._normalise_segments(video_id, raw_segments)

    def fetch_transcript(
        self, video_id: str, lang: str | None, prefer_auto: bool
    ) -> tuple[CaptionTrack, list[TranscriptSegment]]:
        selected = self.select_transcript(video_id, lang, prefer_auto)
        segments = self.fetch_selected_transcript(video_id, selected)
        return selected.track, segments

    def fetch_metadata(self, video_id: str) -> VideoMetadata:
        url = build_watch_url(video_id)
        try:
            data = self._fetch_oembed(url)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 404:
                raise VideoUnavailable("VideoUnavailable", "Video not found") from exc
            if status in {401, 403}:
                if self.settings.reject_private_or_unlisted:
                    raise PolicyRejected(
                        "PolicyRejected", "Video is private or unlisted"
                    ) from exc
                return VideoMetadata(id=video_id, url=url)
            raise NetworkError("NetworkError", "Metadata request failed") from exc
        except httpx.HTTPError as exc:  # pragma: no cover - defensive
            raise NetworkError("NetworkError", "Metadata request failed") from exc
        return VideoMetadata(
            id=video_id,
            url=url,
            title=data.get("title"),
            channel=data.get("author_name"),
            published_at=None,
            duration=None,
        )

    def _list_transcripts(self, video_id: str) -> Iterable[Any]:
        try:
            return self.api.list(video_id)
        except YTVideoUnavailable as exc:
            raise VideoUnavailable("VideoUnavailable", "Video is unavailable") from exc
        except TranscriptsDisabled as exc:
            raise PolicyRejected("PolicyRejected", "Captions disabled by uploader") from exc
        except RequestBlocked as exc:
            raise RateLimited("RateLimited", "Rate limited by YouTube") from exc
        except YouTubeRequestFailed as exc:
            raise NetworkError("NetworkError", "YouTube request failed") from exc
        except NoTranscriptFound as exc:
            raise NoCaptionsAvailable("NoCaptionsAvailable", "No captions available") from exc

    def _to_caption_track(self, transcript: Any) -> CaptionTrack:
        return CaptionTrack(
            lang=getattr(transcript, "language_code", ""),
            is_auto=bool(getattr(transcript, "is_generated", False)),
            name=getattr(transcript, "name", None),
            track_id=getattr(transcript, "translation_language", None),
        )

    def _select_transcript(
        self, transcripts: Iterable[Any], lang: str | None, prefer_auto: bool
    ) -> SelectedTranscript:
        manual: list[SelectedTranscript] = []
        auto: list[SelectedTranscript] = []
        for transcript in transcripts:
            track = self._to_caption_track(transcript)
            selection = SelectedTranscript(transcript=transcript, track=track)
            if track.is_auto:
                auto.append(selection)
            else:
                manual.append(selection)

        lang_norm = lang.lower() if lang else None

        def matches(target: CaptionTrack) -> bool:
            if not lang_norm:
                return False
            target_code = target.lang.lower()
            return target_code == lang_norm or target_code.split("-")[0] == lang_norm.split("-")[0]

        if lang_norm:
            for candidate in manual:
                if matches(candidate.track):
                    return candidate
        if manual and not prefer_auto:
            return manual[0]

        allow_auto = prefer_auto or self.settings.allow_auto
        if allow_auto:
            if lang_norm:
                for candidate in auto:
                    if matches(candidate.track):
                        return candidate
            if auto:
                return auto[0]

        raise NoCaptionsAvailable("NoCaptionsAvailable", "No transcript tracks available")

    def _normalise_segments(
        self, video_id: str, raw_segments: list[dict[str, Any]]
    ) -> list[TranscriptSegment]:
        segments: list[TranscriptSegment] = []
        for index, item in enumerate(raw_segments):
            text = " ".join(item.get("text", "").split()).strip()
            if not text:
                continue
            start = float(item.get("start", 0.0))
            duration = float(item.get("duration") or item.get("dur") or 0.0)
            segment = TranscriptSegment(
                id=f"{video_id}_{index:05d}",
                text=text,
                start=start,
                dur=duration,
            )
            segments.append(segment)
        if not segments:
            raise NoCaptionsAvailable("NoCaptionsAvailable", "Transcript contained no text")
        return segments

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))
    def _fetch_oembed(self, url: str) -> dict:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                "https://www.youtube.com/oembed",
                params={"url": url, "format": "json"},
                headers={"User-Agent": "futuroptimist-ytmcp/1.0"},
            )
            response.raise_for_status()
            return response.json()


class YouTubeTranscriptService:
    """High level facade combining client, chunking, and caching."""

    def __init__(
        self,
        settings: Settings | None = None,
        cache: TranscriptCache | None = None,
        client: YouTubeTranscriptClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        cache_dir = self.settings.ensure_cache_dir()
        cache_path = cache_dir / "transcripts.sqlite3"
        self.cache = cache or TranscriptCache(cache_path)
        self.client = client or YouTubeTranscriptClient(self.settings)

    def get_metadata(self, url: str) -> VideoMetadata:
        video_id = parse_video_id(url)
        return self.client.fetch_metadata(video_id)

    def list_tracks(self, url: str) -> list[CaptionTrack]:
        video_id = parse_video_id(url)
        return self.client.list_tracks(video_id)

    def get_transcript(
        self, url: str, lang: str | None = None, prefer_auto: bool | None = None
    ) -> TranscriptResponse:
        video_id = parse_video_id(url)
        prefer_auto_flag = bool(prefer_auto) if prefer_auto is not None else False
        selected = self.client.select_transcript(video_id, lang, prefer_auto_flag)
        cache_key = TranscriptCache.make_key(
            video_id,
            selected.track.lang,
            "auto" if selected.track.is_auto else "manual",
            selected.track.track_id or "",
        )
        cached = self.cache.get(cache_key)
        if cached:
            return TranscriptResponse.model_validate(cached)
        segments = self.client.fetch_selected_transcript(video_id, selected)
        metadata = self.client.fetch_metadata(video_id)
        chunks = chunk_segments(video_id, segments)
        response = TranscriptResponse(
            video=metadata,
            captions=selected.track,
            segments=segments,
            chunks=chunks,
            hash=hash_content(
                {
                    "video": metadata.model_dump(),
                    "captions": selected.track.model_dump(),
                    "segments": [segment.model_dump() for segment in segments],
                }
            ),
        )
        self.cache.set(cache_key, response.model_dump(), self.settings.cache_ttl_days)
        return response


__all__ = ["SelectedTranscript", "YouTubeTranscriptClient", "YouTubeTranscriptService"]
