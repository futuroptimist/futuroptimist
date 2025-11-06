"""High level client that wraps ``youtube_transcript_api``."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, cast

import httpx
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_fixed
from youtube_transcript_api import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeRequestFailed,
    YouTubeTranscriptApi,
)
from youtube_transcript_api import (
    VideoUnavailable as YtVideoUnavailable,
)

from .cache import Cache
from .chunking import chunk_segments
from .errors import NetworkError, NoCaptionsAvailable, PolicyRejected, RateLimited, VideoUnavailable
from .models import CaptionTrack, Segment, TranscriptResponse, VideoMetadata
from .settings import Settings
from .utils import hash_content, is_unlisted_or_private, parse_video_id


def _as_float(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:  # pragma: no cover - defensive
            return 0.0
    return 0.0


@dataclass(slots=True)
class _SelectedTrack:
    transcript: Any
    info: CaptionTrack


class YouTubeTranscriptService:
    """End-to-end orchestration around caption retrieval."""

    def __init__(self, settings: Settings, cache: Cache | None = None) -> None:
        self.settings = settings
        cache_path = settings.cache_dir / "transcripts.sqlite3"
        self.cache = cache or Cache(cache_path, settings.cache_ttl_days)

    # Metadata -----------------------------------------------------------------
    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_fixed(0.3),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    def _fetch_oembed(self, video_url: str) -> dict[str, Any]:
        response = httpx.get(
            "https://www.youtube.com/oembed",
            params={"url": video_url, "format": "json"},
            timeout=5.0,
        )
        if response.status_code in {401, 403}:
            raise PolicyRejected()
        if response.status_code == 404:
            raise VideoUnavailable()
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise NetworkError("Unexpected metadata payload", details={"type": type(data).__name__})
        return cast(dict[str, Any], data)

    def _build_metadata(self, video_id: str) -> VideoMetadata:
        url = f"https://www.youtube.com/watch?v={video_id}"
        title = channel = None
        try:
            data = self._fetch_oembed(url)
        except PolicyRejected:
            if self.settings.reject_private_or_unlisted:
                raise
            data = {}
        except VideoUnavailable:
            raise
        except (httpx.HTTPError, RetryError) as exc:  # pragma: no cover - tenacity unwraps
            raise NetworkError("Failed to fetch metadata", details={"reason": str(exc)}) from exc
        else:
            title = data.get("title")
            channel = data.get("author_name")
        metadata_dict = {
            "id": video_id,
            "url": url,
            "title": title,
            "channel": channel,
            "published_at": None,
            "duration": None,
        }
        if self.settings.reject_private_or_unlisted and is_unlisted_or_private(metadata_dict):
            raise PolicyRejected()
        return VideoMetadata.model_validate(metadata_dict)

    # Tracks -------------------------------------------------------------------
    def list_tracks(self, url_or_id: str) -> list[CaptionTrack]:
        video_id = parse_video_id(url_or_id)
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)  # type: ignore[attr-defined]
        except (YtVideoUnavailable, CouldNotRetrieveTranscript) as exc:
            raise VideoUnavailable() from exc
        except (NoTranscriptFound, TranscriptsDisabled) as exc:
            raise NoCaptionsAvailable() from exc
        except YouTubeRequestFailed as exc:
            status = getattr(exc, "http_status", None)
            if isinstance(status, int) and status == 429:
                raise RateLimited() from exc
            raise NetworkError("Upstream request failed", details={"status": status}) from exc
        tracks: list[CaptionTrack] = []
        for transcript in transcript_list:
            track = CaptionTrack(
                lang=transcript.language_code,
                is_auto=transcript.is_generated,
                name=getattr(transcript, "name", None),
                track_id=getattr(transcript, "transcript_id", None),
            )
            tracks.append(track)
        tracks.sort(key=lambda t: (t.is_auto, t.lang))
        return tracks

    # Transcript ----------------------------------------------------------------
    def get_transcript(
        self,
        url_or_id: str,
        *,
        lang: str | None = None,
        prefer_auto: bool | None = None,
    ) -> TranscriptResponse:
        video_id = parse_video_id(url_or_id)
        metadata = self._build_metadata(video_id)
        prefer_auto = bool(prefer_auto)
        allow_auto = self.settings.allow_auto

        transcript_list = self._load_transcript_list(video_id)
        selected = self._select_track(transcript_list, lang, prefer_auto, allow_auto)
        if not selected:
            raise NoCaptionsAvailable()

        cache_key = hash_content(
            {
                "video_id": video_id,
                "lang": selected.info.lang,
                "is_auto": selected.info.is_auto,
                "track_id": selected.info.track_id,
            }
        )
        cached = self.cache.get(cache_key)
        if cached:
            return TranscriptResponse.model_validate(cached)

        try:
            entries = selected.transcript.fetch()
        except CouldNotRetrieveTranscript as exc:
            raise NetworkError("Failed to retrieve transcript", details={"reason": str(exc)}) from exc
        except YouTubeRequestFailed as exc:  # pragma: no cover - defensive
            status = getattr(exc, "http_status", None)
            if isinstance(status, int) and status == 429:
                raise RateLimited() from exc
            raise NetworkError("Upstream request failed", details={"status": status}) from exc

        segments = self._normalise_segments(entries)
        chunks = chunk_segments(video_id, segments)
        response = TranscriptResponse(
            video=metadata,
            captions=selected.info,
            segments=segments,
            chunks=chunks,
            hash=hash_content(
                {
                    "video": metadata.model_dump(),
                    "captions": selected.info.model_dump(),
                    "segments": [seg.model_dump() for seg in segments],
                    "chunks": [chunk.model_dump() for chunk in chunks],
                }
            ),
        )
        self.cache.set(cache_key, response.model_dump())
        return response

    def _load_transcript_list(self, video_id: str) -> Any:
        try:
            return YouTubeTranscriptApi.list_transcripts(video_id)  # type: ignore[attr-defined]
        except (YtVideoUnavailable, CouldNotRetrieveTranscript) as exc:
            raise VideoUnavailable() from exc
        except (NoTranscriptFound, TranscriptsDisabled) as exc:
            raise NoCaptionsAvailable() from exc
        except YouTubeRequestFailed as exc:
            status = getattr(exc, "http_status", None)
            if isinstance(status, int) and status == 429:
                raise RateLimited() from exc
            raise NetworkError("Upstream request failed", details={"status": status}) from exc

    def _select_track(
        self,
        transcript_list: Any,
        lang: str | None,
        prefer_auto: bool,
        allow_auto: bool,
    ) -> _SelectedTrack | None:
        manual: list[Any] = []
        auto: list[Any] = []
        for transcript in transcript_list:
            if transcript.is_generated:
                auto.append(transcript)
            else:
                manual.append(transcript)

        def pick(candidates: list[Any], languages: Iterable[str]) -> Any | None:
            for language in languages:
                if not language:
                    continue
                for transcript in candidates:
                    if transcript.language_code.lower() == language.lower():
                        return transcript
            return candidates[0] if candidates else None

        languages: list[str] = [lang] if lang else ["en"]
        if lang is None:
            languages.append("")

        chosen: Any | None = None
        if prefer_auto and allow_auto:
            chosen = pick(auto, languages)
            if not chosen:
                chosen = pick(manual, languages)
        else:
            chosen = pick(manual, languages)
            if not chosen and allow_auto:
                chosen = pick(auto, languages)

        if not chosen:
            return None
        caption_track = CaptionTrack(
            lang=chosen.language_code,
            is_auto=chosen.is_generated,
            name=getattr(chosen, "name", None),
            track_id=getattr(chosen, "transcript_id", None),
        )
        return _SelectedTrack(transcript=chosen, info=caption_track)

    def _normalise_segments(self, entries: Iterable[dict[str, object]]) -> list[Segment]:
        segments: list[Segment] = []
        for index, entry in enumerate(entries):
            text = str(entry.get("text", "")).strip()
            text = " ".join(text.split())
            if not text:
                continue
            start = _as_float(entry.get("start", 0.0))
            duration = _as_float(entry.get("duration", 0.0))
            seg_id = f"seg_{index:04d}"
            segments.append(Segment(id=seg_id, text=text, start=start, dur=duration))
        return segments

    # Public metadata ----------------------------------------------------------
    def get_metadata(self, url_or_id: str) -> VideoMetadata:
        video_id = parse_video_id(url_or_id)
        return self._build_metadata(video_id)


__all__ = ["YouTubeTranscriptService"]
