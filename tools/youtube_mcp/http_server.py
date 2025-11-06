"""FastAPI application exposing the transcript tooling over HTTP."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, Query
from fastapi.responses import JSONResponse

from .errors import BaseYtMcpError
from .models import HealthResponse, MetadataResponse, TracksResponse, TranscriptResponse
from .settings import Settings, get_settings
from .youtube_client import YouTubeTranscriptService


@lru_cache(maxsize=1)
def get_service(settings: Settings | None = None) -> YouTubeTranscriptService:
    return YouTubeTranscriptService(settings=settings or get_settings())


app = FastAPI(title="Futuroptimist YouTube Transcript Service", version="0.1.0")


@app.exception_handler(BaseYtMcpError)
async def handle_service_error(_: object, exc: BaseYtMcpError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status().value,
        content={"error": exc.to_dict()},
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(ok=True, version="0.1.0")


UrlParam = Annotated[str, Query(description="YouTube video URL or ID")]
LangParam = Annotated[str | None, Query(description="Preferred language code")]
PreferAutoParam = Annotated[bool | None, Query(description="Allow auto-generated captions")]
ServiceDep = Annotated[YouTubeTranscriptService, Depends(get_service)]


@app.get("/transcript", response_model=TranscriptResponse)
async def get_transcript(
    url: UrlParam,
    service: ServiceDep,
    lang: LangParam = None,
    prefer_auto: PreferAutoParam = None,
) -> TranscriptResponse:
    return service.get_transcript(url=url, lang=lang, prefer_auto=prefer_auto)


@app.get("/tracks", response_model=TracksResponse)
async def get_tracks(
    url: UrlParam,
    service: ServiceDep,
) -> TracksResponse:
    tracks = service.list_tracks(url=url)
    return TracksResponse(tracks=tracks)


@app.get("/metadata", response_model=MetadataResponse)
async def get_metadata(
    url: UrlParam,
    service: ServiceDep,
) -> MetadataResponse:
    metadata = service.get_metadata(url=url)
    return MetadataResponse.model_validate(metadata.model_dump())


__all__ = ["app", "get_service"]
