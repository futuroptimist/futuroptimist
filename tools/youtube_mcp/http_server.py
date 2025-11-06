"""FastAPI server exposing the YouTube transcript service."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

from fastapi import FastAPI, HTTPException, Query

from .errors import BaseYtMcpError
from .models import HealthResponse, MetadataResponse, TracksResponse, TranscriptResponse
from .settings import Settings
from .youtube_client import YouTubeTranscriptService

T = TypeVar("T")

anyio_module: Any | None
try:  # pragma: no cover - optional dependency for ASGI lifespan
    import anyio as _anyio_module
except ImportError:  # pragma: no cover
    anyio_module = None
else:
    anyio_module = _anyio_module

anyio: Any | None = anyio_module


def create_service(settings: Settings) -> YouTubeTranscriptService:
    return YouTubeTranscriptService(settings=settings)


def create_app(
    settings: Settings | None = None,
    service: YouTubeTranscriptService | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    service = service or create_service(settings)

    app = FastAPI(title="YouTube Transcript MCP", version="0.1.0")

    def _handle_error(exc: BaseYtMcpError) -> HTTPException:
        return HTTPException(status_code=exc.http_status.value, detail=exc.to_dict())

    async def _run_sync(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        if anyio is None:
            return func(*args, **kwargs)

        def call() -> T:
            return func(*args, **kwargs)

        return cast(T, await anyio.to_thread.run_sync(call))

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(ok=True, version="0.1.0")

    @app.get("/transcript", response_model=TranscriptResponse)
    async def transcript(
        url: str = Query(..., description="YouTube video URL or identifier"),
        lang: str | None = Query(None, description="Preferred caption language"),
        prefer_auto: bool | None = Query(
            None, description="If true, prefer auto-generated captions"
        ),
    ) -> TranscriptResponse:
        try:
            result = await _run_sync(
                service.get_transcript,
                url,
                lang=lang,
                prefer_auto=prefer_auto,
            )
        except BaseYtMcpError as exc:
            raise _handle_error(exc) from exc
        return result

    @app.get("/tracks", response_model=TracksResponse)
    async def tracks(
        url: str = Query(..., description="YouTube video URL or identifier"),
    ) -> TracksResponse:
        try:
            result = await _run_sync(service.search_captions, url)
        except BaseYtMcpError as exc:
            raise _handle_error(exc) from exc
        return result

    @app.get("/metadata", response_model=MetadataResponse)
    async def metadata(
        url: str = Query(..., description="YouTube video URL or identifier"),
    ) -> MetadataResponse:
        try:
            result = await _run_sync(service.get_metadata, url)
        except BaseYtMcpError as exc:
            raise _handle_error(exc) from exc
        return result

    return app


app = create_app()
