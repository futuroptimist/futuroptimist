"""FastAPI application exposing transcript tools over HTTP."""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse

from .errors import BaseYtMcpError
from .models import HealthResponse, MetadataResponse, TracksResponse, TranscriptResponse
from .settings import from_env
from .youtube_client import YouTubeTranscriptService


def create_app(service: Optional[YouTubeTranscriptService] = None) -> FastAPI:
    settings = service.settings if service else from_env()
    app = FastAPI(title="YouTube Transcript MCP", version="1.0.0")
    app.state.service = service or YouTubeTranscriptService(settings=settings)

    @app.exception_handler(BaseYtMcpError)
    async def _handle_domain_error(_: Request, exc: BaseYtMcpError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status.value,
            content={"error": exc.as_dict()},
        )

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(ok=True, version="1.0.0")

    @app.get("/transcript", response_model=TranscriptResponse)
    async def transcript(
        request: Request,
        url: str = Query(..., description="YouTube watch URL or raw ID."),
        lang: Optional[str] = Query(None, description="Preferred caption language."),
        prefer_auto: Optional[bool] = Query(
            None,
            description="Prefer auto-generated captions over manual ones if set to true.",
        ),
    ) -> TranscriptResponse:
        service: YouTubeTranscriptService = request.app.state.service
        return service.get_transcript(url, lang=lang, prefer_auto=prefer_auto)

    @app.get("/tracks", response_model=TracksResponse)
    async def tracks(
        request: Request,
        url: str = Query(..., description="YouTube watch URL or raw ID."),
    ) -> TracksResponse:
        service = request.app.state.service
        tracks = service.list_tracks(url)
        return TracksResponse(tracks=tracks)

    @app.get("/metadata", response_model=MetadataResponse)
    async def metadata(
        request: Request,
        url: str = Query(..., description="YouTube watch URL or raw ID."),
    ) -> MetadataResponse:
        service = request.app.state.service
        return MetadataResponse(**service.get_metadata(url).model_dump())

    return app


app = create_app()
