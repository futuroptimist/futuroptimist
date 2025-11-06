"""FastAPI application exposing the transcript service."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query

from . import __version__
from .cache import Cache
from .errors import BaseYtMcpError
from .models import HealthcheckResponse, TracksResponse, TranscriptResponse, VideoMetadata
from .settings import Settings
from .youtube_client import YouTubeTranscriptService

_settings = Settings.from_env()
_cache = Cache(_settings.cache_dir / "transcripts.sqlite3", _settings.cache_ttl_days)
_service = YouTubeTranscriptService(_settings, _cache)


def get_service() -> YouTubeTranscriptService:
    return _service


app = FastAPI(title="YouTube Transcript Service", version=__version__)


@app.get("/health", response_model=HealthcheckResponse)
def health() -> HealthcheckResponse:
    return HealthcheckResponse(ok=True, version=__version__)


@app.get("/transcript", response_model=TranscriptResponse)
def transcript(
    url: str = Query(..., description="YouTube video URL or ID"),
    lang: str | None = Query(None, description="Preferred language code"),
    prefer_auto: bool | None = Query(False, description="Prefer auto captions"),
    service: YouTubeTranscriptService = Depends(get_service),  # noqa: B008
) -> TranscriptResponse:
    try:
        return service.get_transcript(url, lang=lang, prefer_auto=prefer_auto)
    except BaseYtMcpError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.to_dict()) from exc


@app.get("/tracks", response_model=TracksResponse)
def tracks(
    url: str = Query(..., description="YouTube video URL or ID"),
    service: YouTubeTranscriptService = Depends(get_service),  # noqa: B008
) -> TracksResponse:
    try:
        track_list = service.list_tracks(url)
    except BaseYtMcpError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.to_dict()) from exc
    return TracksResponse(tracks=track_list)


@app.get("/metadata", response_model=VideoMetadata)
def metadata(
    url: str = Query(..., description="YouTube video URL or ID"),
    service: YouTubeTranscriptService = Depends(get_service),  # noqa: B008
) -> VideoMetadata:
    try:
        meta = service.get_metadata(url)
    except BaseYtMcpError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.to_dict()) from exc
    return meta
